from flask import render_template, request, redirect, flash, url_for, jsonify, session
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Image, Like, Comment
import os
from datetime import datetime




def init_routes(app):
    @app.route('/')
    def home():
        return render_template("index.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            username = request.form["username"]
            password = request.form["password"]
            
            # Query the database for the user
            user = User.query.filter_by(username=username).first()
            print(f"Login attempt - Username: {username}")

            if user:
                print(f"User found: {user.username}")
                print("wellocome in if loop ")
            
                # Check if user exists and password is correct
                if user and check_password_hash(user.password, password):
                    print("Password verified") 
                    
                    flash(f"Welcome, {user.first_name}", "success")
                    session['user_id'] = user.id # Save user ID in the session
                    print("Session User ID:", session.get('user_id'))
                    return redirect(url_for('Home'))  # Ensure correct route name
                else:
                    flash("Invalid Username and Password. Please try again.", "danger")
                    return redirect(url_for('login'))
            else:
                print("entrr in else loop")
        return render_template("login.html")


    @app.route('/signup', methods=['GET', "POST"])
    def signup():
        if request.method == "POST":
            first_name = request.form['first_name']
            last_name = request.form['last_name']
            email = request.form['email']
            username = request.form['username']
            password = generate_password_hash(request.form['password'])

            try:
                new_user = User(
                    first_name=first_name, 
                    last_name=last_name, 
                    email=email, 
                    username=username, 
                    password=password
                )
                db.session.add(new_user)
                db.session.commit()

                flash('Sign-in successful!', 'success')
                return redirect('/Home')

            except Exception as e:
                db.session.rollback()
                flash('Username or email already exists. Try another.', 'danger')
                return redirect('/signup')

        return render_template('signup.html')

    @app.route('/Home')
    def Home():
        if 'user_id' not in session:
            return redirect(url_for('login'))

        images = Image.query.all()
        user_id = session['user_id']

        image_data = []
        for image in images:
            is_liked = Like.query.filter_by(user_id=user_id, image_id=image.id).first() is not None
            image_data.append({
                "image_id": image.id,
                "filename": image.filename,
                "description": image.description,
                "likes": image.likes,
                "is_liked": is_liked
            })

        print(image_data)

        return render_template("home.html", images=image_data)
    


    @app.route('/comments', methods=['POST'])
    def add_comment():
        print("Adding comment...")
        if 'user_id' not in session:
            return jsonify({'error': 'Please login first'}), 401

        data = request.json
        image_id = data.get('image_id')
        comment_text = data.get('comment')
        user_id = session.get('user_id')
        
        # Validate inputs
        if not comment_text or not image_id:
            return jsonify({'error': 'Comment cannot be empty'}), 400

        new_comment = Comment(
            user_id=user_id,
            image_id=image_id, 
            comment=comment_text,
            created_at=datetime.utcnow()  # Ensure this is correctly recorded
        )
        db.session.add(new_comment)
        db.session.commit()

        return jsonify({
            'comment': new_comment.comment,
            'username': session.get('username'),  # Assuming username is in session
            'timestamp': new_comment.created_at.isoformat()
        })


    

    @app.route('/get_comments/<int:image_id>', methods=["GET"])
    def get_comments(image_id):
        comments = Comment.query.filter_by(image_id=image_id).order_by(Comment.created_at.desc()).all()
        
        comments_data = [{
            'username': comment.user.first_name,
            'comment': comment.comment,
            'timestamp': comment.created_at.isoformat()
        } for comment in comments]
        
        return jsonify(comments_data)
    
    @app.route("/newHome", methods = ["GET","POST"])
    def newhome():
       
        
        return render_template("newHome.html")

    @app.route("/like", methods=["POST"])
    def like_image():
        if 'user_id' not in session:
            print("User not logged in.")
            return jsonify({'error': 'User not logged in'}), 401

        try:
            data = request.json
            print(f"Received data: {data}")
            image_id = data.get('image_id')  # Safely get the image_id from the request
            user_id = session.get('user_id')  # Fetch user ID from session
            post_id=0

            if not image_id:
                print("Missing image ID.")
                return jsonify({"error": "Image ID is missing"}), 400

            # Ensure the image exists
            image = Image.query.filter_by(id=image_id).first()
            if not image:
                return jsonify({"error": "Image not found"}), 404


              # Fetch post_id from the request
            
                  # Define logic to determine post_id
                # Check if the user already liked the image
            existing_like = Like.query.filter_by(user_id=user_id, image_id=image_id).first()

            if existing_like:
                    # Unlike the image
                    db.session.delete(existing_like)
                    image.likes = max(image.likes - 1, 0)  # Prevent negative likes
                    liked = False
            else:
                    # Like the image
                    new_like = Like(user_id=user_id, image_id=image_id, post_id=post_id)
                    db.session.add(new_like)
                    image.likes += 1  # Increment like count
                    liked = True

            db.session.commit()

            return jsonify({"liked": liked, "total_likes": image.likes})
        except Exception as e:
            print(f"Error processing like: {e}")
            return jsonify({"error": "Internal Server Error"}), 500
    
    @app.route('/upload', methods=['GET', 'POST'])
    def upload():
        if request.method == "POST":
            # Check if the form has an image file
            if 'image' not in request.files or request.files['image'].filename == '':
                flash("No file selected", "danger")
                return redirect(request.url)

            # Retrieve the image and description
            image = request.files["image"]
            description = request.form.get("description")

            if image:
                # Secure the filename and save the file
                filename = secure_filename(image.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                image.save(filepath)

                # Save the image details in the database
                file_type = image.mimetype
                new_image = Image(filename=filename, type=file_type, description=description)
                db.session.add(new_image)
                db.session.commit()

                flash("Image uploaded successfully", "success")
                return redirect("/Home")

        return render_template("upload.html")

    



    return app





