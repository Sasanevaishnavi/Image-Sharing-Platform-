from flask import render_template, request, redirect, flash, url_for, jsonify, session
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Image, Like, Comment
import os
from datetime import datetime


def init_routes(app):
    @app.route('/')
    def index2():
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
                return redirect('/home')

            except Exception as e:
                db.session.rollback()
                flash('Username or email already exists. Try another.', 'danger')
                return redirect('/signup')

        return render_template('signup.html')

    @app.route('/home')
    def home():
        if 'user_id' in session:
                user_id = session['user_id']
        else:
                user_id = None
                # push him to login page
                return redirect(url_for('login'))

        images = Image.query.all()
        user_id = session.get("user_id", None)
        user_account = User.query.filter_by(id=user_id).first() 
    
        image_data = []
        for image in images:
            is_liked = False
            if user_id:
                is_liked = Like.query.filter_by(user_id=user_id, image_id=image.id).first() is not None
# ---------------------------------------------------------------------------------------------------------
             # Debugging: Print the user_id for each image
            print(f"Fetching Uploader for Image ID {image.id}, User ID: {image.user_id}")

            uploader = User.query.filter_by(id=image.user_id).first()  # Correctly fetch uploader
            user_poster_name = uploader.first_name if uploader else "Unknown"

            # Debugging: Check if we found the uploader
            if uploader:
                print(f"Uploader Found: {uploader.first_name}")
            else:
                print(f"Uploader Not Found for Image ID {image.id}")


            comments = Comment.query.filter_by(image_id=image.id).order_by(Comment.created_at.desc()).all()

            comments_data = []
            for comment in comments:
                commenter = User.query.filter_by(id=comment.user_id).first()  # Fetch commenter
                commenter_name = commenter.first_name if commenter else "Unknown"

                comments_data.append({
                    "username": commenter_name,  # Correct name of the commenter
                    "comment": comment.comment,
                    "timestamp": comment.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    "comment_id": comment.id,  # Add this
                    "user_id": comment.user_id
                })
          
            image_data.append({
                "image_id": image.id,
                "user_poster": user_poster_name,
                "user_poster_id": image.user_id,
                "filename": image.filename,
                "description": image.description,
                "likes": image.likes,
                "is_liked": is_liked,
                "comments": comments_data 
                
            })

        # print(image_data)

        return render_template("home.html", images=image_data,user_account=user_account,user_id=user_id)
    


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
            'timestamp': new_comment.created_at.isoformat(),
            'comment_id': new_comment.id 
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
    


    @app.route('/comments/<int:comment_id>', methods =['DELETE'])
    def delete_comment(comment_id):
        print(f"Received request to delete comment with ID: {comment_id}") 

        if 'user_id' not in session:
            print("User is not logged in")
            return jsonify ({'error': 'Please login first'}), 401
        
        comment = Comment.query.get(comment_id)

        if not comment:
            print("Comment not found in database")  # Debugging line
            return jsonify({'error': 'Comment not found'}), 404

        if comment.user_id != session['user_id']:
            print(f"Unauthorized access attempt by user {session['user_id']} for comment {comment_id}")  # Debugging line
            return jsonify({'error': 'Unauthorized'}), 403
            
        try:
            db.session.delete(comment)
            db.session.commit()
            return jsonify({'message': 'Comment deleted successfully'}), 200
        except Exception as e:
            db.session.rollback()  # Fixed: Rollback in case of error
            return jsonify({'error': 'Database error', 'details': str(e)}), 500

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
            if 'image' not in request.files or request.files['image'].filename == '':
                flash("No file selected", "danger")
                return redirect(request.url)

            image = request.files["image"]
            description = request.form.get("description")

            if image:
                filename = secure_filename(image.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                image.save(filepath)

                user_id = session.get('user_id')  # ✅ Correctly fetch user_id from session

                # Debugging print
                print(f"Uploading Image by User ID: {user_id}")

                if not user_id:
                    flash("Error: User not found. Please log in again.", "danger")
                    return redirect(url_for('login'))

                new_image = Image(
                    user_id=user_id,  # Correct user_id assignment
                    filename=filename,
                    type=image.mimetype,
                    description=description
                )
                db.session.add(new_image)
                db.session.commit()

                flash("Image uploaded successfully", "success")
                return redirect("/home")

        return render_template("upload.html")
    
    

    @app.route("/logout", methods=["POST"])
    def logout():
        if "user_id" in session:
            session.pop("user_id", None)  # Remove user_id from session
            return jsonify({"success": True})
    
        return jsonify({"success": False})
    

    @app.route('/images/<int:image_id>', methods =['DELETE'])
    def delete_image(image_id):
        print(f"Received request to delete image with ID: {image_id}") 

        if 'user_id' not in session:
            print("User is not logged in")
            return jsonify ({'error': 'Please login first'}), 401
        
        image = Image.query.get(image_id)

        if not image:
            print("image not found in database")  # Debugging line
            return jsonify({'error': 'image not found'}), 404

        if image.user_id != session['user_id']:
            print(f"Unauthorized access attempt by user {session['user_id']} for image {image_id}")  # Debugging line
            return jsonify({'error': 'Unauthorized'}), 403
            
        try:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], image.filename)
            if os.path.exists(file_path):
                os.remove(file_path)

            # Delete associated likes and comments
            Like.query.filter_by(image_id=image_id).delete()
            Comment.query.filter_by(image_id=image_id).delete()
            db.session.delete(image)
            db.session.commit()
            return jsonify({'message': 'image deleted successfully'}), 200
        
        except Exception as e:
            db.session.rollback()  # Fixed: Rollback in case of error
            return jsonify({'error': 'Database error', 'details': str(e)}), 500
   
    return app