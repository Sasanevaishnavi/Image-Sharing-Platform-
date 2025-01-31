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
        if 'user_id' in session:
                user_id = session['user_id']
        else:
                user_id = None
                # push him to login page
                return redirect(url_for('login'))

        images = Image.query.all()
        user_id = session.get("user_id", None)
        
        image_data = []
        for image in images:
            is_liked = False
            if user_id:
                is_liked = Like.query.filter_by(user_id=user_id, image_id=image.id).first() is not None
            comments = Comment.query.filter_by(image_id=image.id).order_by(Comment.created_at.desc()).all()

            comments_data = [{
                "username " : comment.user.first_name,
                "comment" : comment.comment,
                "timestamp": comment.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            } for comment in comments]

            image_data.append({
                "image_id": image.id,
                "user_poster": image.user.first_name,
                "filename": image.filename,
                "description": image.description,
                "likes": image.likes,
                "is_liked": is_liked,
                "comments": comments_data 
                
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
    
# ---------------------------------------------------------------------------------------------------------
    @app.route("/like", methods=["PUT"])
    def like_image():
        if 'user_id' not in session:
            return jsonify({'error': 'User not logged in'}), 401
        try:
            data = request.json
            image_id = data.get('image_id')
            user_id = session['user_id']
            if not image_id:
                return jsonify({"error": "Image ID is missing"}), 400
            # Get the image
            image = Image.query.get_or_404(image_id)
            # Check if user already liked this image
            existing_like = Like.query.filter_by(
                user_id=user_id,
                image_id=image_id
            ).first()
            if existing_like:
                # Unlike
                db.session.delete(existing_like)
                image.likes = max(0, image.likes - 1)  # Prevent negative likes
                liked = False
            else:
                # Like
                new_like = Like(
                    user_id=user_id,
                    image_id=image_id,
                    post_id=0  # Default value if needed
                )
                db.session.add(new_like)
                image.likes += 1
                liked = True
            db.session.commit()
            return jsonify({
                "liked": liked,
                "total_likes": image.likes
            })
        except Exception as e:
            db.session.rollback()
            print(f"Error processing like: {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route('/upload', methods=['GET', 'POST'])
    def upload():
        if 'user_id' not in session:
            flash("You need to log in to upload images", "danger")
            return redirect(url_for('login'))

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

                # Save the image details in the database with user_id
                user_id = session['user_id']  # Get the logged-in user ID
                file_type = image.mimetype
                new_image = Image(user_id=user_id, filename=filename, type=file_type, description=description)  # Use 'user_id'
                db.session.add(new_image)
                db.session.commit()

                flash("Image uploaded successfully", "success")
                return redirect("/Home")

        return render_template("upload.html")

        
    return app