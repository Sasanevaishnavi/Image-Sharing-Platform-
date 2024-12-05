from flask import render_template, request, redirect, flash, url_for, jsonify, session
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Image, Like, Comment
import os




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
                    session['user_id'] = user.id  # Save user ID in the session
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
    

    # @app.route("/comments", methods =["GET", "POST"] )
    # def comments():
    #     data = request.json
    #     comment_text = data.get('comment')
    #     image_id = data.get('image_id')
    #     user_id = session.get("user_id")

    #     if not user_id:
    #         return jsonify({"error": "User not logged in"}), 401

    #     if not comment_text:
    #         return jsonify({"error": "Comment cannot be empty"}), 400

    #     try:
    #         # Insert comment into the database
    #         new_comment = Comment(
    #             user_id=user_id,
    #             image_id=image_id,
    #             comment=comment_text
    #             )
    #         db.session.add(new_comment)
    #         db.session.commit()

    #         # Fetch the inserted comment details
    #         comment_details = db.session.query(
    #             Comment.id, User.first_name, Comment.comment
    #         ).join(User, Comment.user_id == User.id).filter(Comment.id == new_comment.id).first()

    #         if comment_details:
    #             return jsonify({
    #                 "id": comment_details[0],
    #                 "name": comment_details[1],
    #                 "comment": comment_details[2],
    #             })
    #         else:
    #             return jsonify({"error": "Failed to retrieve the new comment."}), 500

    #     except Exception as e:
    #         db.session.rollback()
    #         return jsonify({"error": "An internal error occurred. Please try again later."}), 500

    @app.route('/like', methods=['POST'])
    def like_image():
        if 'user_id' not in session:
            return jsonify({'error': 'Please login first'}), 401

        data = request.json
        image_id = data.get('image_id')
        user_id = session['user_id']

        # Check if image exists
        image = Image.query.get(image_id)
        if not image:
            return jsonify({'error': 'Image not found'}), 404

        # Check if user already liked the image
        existing_like = Like.query.filter_by(user_id=user_id, image_id=image_id).first()

        try:
            if existing_like:
                # Unlike the image
                db.session.delete(existing_like)
                image.likes -= 1
                liked = False
            else:
                # Like the image
                new_like = Like(user_id=user_id, image_id=image_id)
                db.session.add(new_like)
                image.likes += 1
                liked = True

            db.session.commit()
            
            return jsonify({
                'liked': liked, 
                'total_likes': image.likes
            })
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': 'An error occurred'}), 500

    @app.route('/comments', methods=['POST'])
    def add_comment():
        if 'user_id' not in session:
            return jsonify({'error': 'Please login first'}), 401

        data = request.json
        image_id = data.get('image_id')
        comment_text = data.get('comment')

        if not comment_text:
            return jsonify({'error': 'Comment cannot be empty'}), 400

        try:
            new_comment = Comment(
                user_id=session['user_id'], 
                image_id=image_id, 
                comment=comment_text
            )
            db.session.add(new_comment)
            db.session.commit()

            return jsonify({
                'comment': comment_text,
                'username': current_user.first_name,  # Assuming you have current_user set up
                'timestamp': new_comment.created_at.isoformat()
            })
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': 'Failed to add comment'}), 500
    @app.route('/get_comments/<int:image_id>')
    def get_comments(image_id):
        comments = Comment.query.filter_by(image_id=image_id).order_by(Comment.created_at.desc()).all()
        
        comments_data = [{
            'username': comment.user.first_name,
            'comment': comment.comment,
            'timestamp': comment.created_at.isoformat()
        } for comment in comments]
        
        return jsonify(comments_data)
    

    # @app.route("/like", methods = ["GET","POST"])
    # def like_image():
    #     if 'user_id' not in session:
    #         return jsonify({'error': 'Please login first'}), 401
    
    #     data = request.json
    #     image_id = data['image_id']
    #     user_id = session.get('user_id')  # Fetch user ID from session

    #     if not user_id:
    #         return jsonify({"error": "User not logged in"}), 401

    #     # Ensure the image exists
    #     image = Image.query.filter_by(id=image_id).first()
    #     if not image:
    #         return jsonify({"error": "Image not found"}), 404

    #     # Check if the user already liked the image
    #     existing_like = Like.query.filter_by(user_id=user_id, image_id=image_id).first()

    #     if existing_like:
    #         # Unlike the image
    #         db.session.delete(existing_like)
    #         image.likes = db.func.ifnull(image.likes - 1, 0)  # Decrease like count but prevent negative values
    #         liked = False
    #     else:
    #         # Like the image
    #         new_like = Like(user_id=user_id, image_id=image_id)
    #         db.session.add(new_like)
    #         image.likes = db.func.ifnull(image.likes + 1, 1)  # Increment like count
    #         liked = True

    #     db.session.commit()

    #     return jsonify({"liked": liked,
    #                      "total_likes": image.likes})
        

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
                new_image = Image(filename=filename, description=description)
                db.session.add(new_image)
                db.session.commit()

                flash("Image uploaded successfully", "success")
                return redirect("/Home")

        return render_template("upload.html")

    # @app.route('/get_comments/<int:image_id>')
    # def get_comments(image_id):
    #     # Fetch comments for the given image ID, including user details
    #     comments = (
    #         db.session.query(User.first_name, Comment.comment, Comment.created_at)
    #         .join(User, Comment.user_id == User.id)
    #         .filter(Comment.image_id == image_id)
    #         .order_by(Comment.created_at.asc())
    #         .all()
    #     )

        # Return the comments as JSON
        # return jsonify([
        #     {
        #         "username": comment[0],
        #         "comment": comment[1],
        #         "created_at": comment[2]
        #     }
        #     for comment in comments
        # ])

    # Add other routes (get_comments, upload, like, comment) similarly
    # Truncated for brevity, follow the same pattern as above routes

    return app





