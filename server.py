from flask import Flask, render_template, request, redirect,flash,url_for,jsonify, session
import sqlite3
import os
from werkzeug.utils import secure_filename

from models import db

app = Flask(__name__)
app.secret_key = "Success"

UPLOAD_FOLDER = os.path.join("static", "uploads")
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
@app.route('/')
def home():
    return render_template("index.html")

@app.route("/login", methods =["GET","POST"] )
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        try:
            conn = sqlite3.connect("User_data.db")
            cursor = conn.cursor()

            cursor.execute('SELECT id, first_name FROM users WHERE username = ? AND password = ? ', (username,password))
            user = cursor.fetchone()
            conn.close()

            if user:
                user_id, first_name = user
                flash(f"Wellcome, {first_name}", "Success")
                session['user_id'] = user_id
                print("Session User ID:", session.get('user_id'))

                return redirect(url_for('Home'))
            else:
                flash("Invalide Username and Password.\n Plz try again ", "danger")
                return redirect('/login')

        except Exception as e:
            flash("Error Occoure during loging . Please Try again later.", "danger")
            print(e)
            return redirect("/login")
    return render_template("login.html")

@app.route('/signup',methods=['GET',"POST"])
def signup():
    if request.method == "POST":
        first_name= request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']

        try:
            # Connect to SQLite database
            conn = sqlite3.connect('User_data.db')
            cursor = conn.cursor()

            # Insert data into the database
            cursor.execute('''
                        INSERT INTO users (first_name, last_name, email, username, password)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (first_name, last_name, email, username, password))

            conn.commit()
            conn.close()

            # Redirect to success or login page
            flash('Sign-in successful!', 'success')
            return redirect('/Home')

        except sqlite3.IntegrityError:
            flash('Username already exists. Try another.', 'danger')
            return redirect('/signup')

    return render_template('signup.html')
@app.route('/Home')
def Home():
    print('starting home')
    user_id = session.get('user_id')
    if not user_id:
        return redirect("/login")
    conn = sqlite3.connect("User_data.db")
    cursor = conn.cursor()

    cursor.execute("""
            SELECT i.id AS image_id, i.filename, i.description, i.likes,
                   CASE WHEN l.user_id IS NOT NULL THEN 1 ELSE 0 END AS is_liked
            FROM images i
            LEFT JOIN likes l ON i.id = l.image_id AND l.user_id = ?
        """, (user_id,))

    print(user_id)

    rows = cursor.fetchall()  # Fetch all results
    # Convert to dictionaries
    # images = [
    #     {"image_id": row[0], "filename": row[1], "description": row[2], "likes": row[3], "is_liked": row[4]}
    #     for row in rows
    # ]

    images = [
        {"image_id": row[0], "filename": row[1], "description": row[2], "likes": row[3]}
        for row in rows
    ]

    print(images)
    conn.close()
    return render_template("home.html", images=images)

@app.route('/get_comments/<int:image_id>')
def get_comments(image_id):
    conn = sqlite3.connect("User_data.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT u.first_name, c.comment, c.created_at
        FROM comments c
        JOIN users u ON c.user_id = u.id
        WHERE c.image_id = ?
        ORDER BY c.created_at ASC
    """, (image_id,))
    comments = cursor.fetchall()

    conn.close()
    return jsonify([{
        "username": comment[0],
        "comment": comment[1],
        "created_at": comment[2]
    } for comment in comments])

@app.route("/upload", methods = ["GET", "POST"])
def upload():
    if request.method == "POST":
        if 'image' not in request.files or request.files['image'].filename == '':
            flash("no file select", "danger")
            return redirect(request.url)

        image = request.files["image"]
        description = request.form["description"]
        if image:
            filename = secure_filename(image.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(filepath)

            conn = sqlite3.connect("User_data.db")
            cursor = conn.cursor()

            cursor.execute(
                ''' INSERT INTO images (filename ,type,  description) VALUES (?,?,?) ''',
                (filename,"image", description))

            db.session.add(images (filename ,type,  description))

            conn.commit()
            conn.close()

            flash(("Image Upload Successfully", "success"))
            return  redirect("/Home")

    return  render_template("upload.html")


@app.route('/like', methods=['POST'])
def like():
    data = request.json
    image_id = data['image_id']
    user_id = session.get('user_id')  # Fetch user ID from session

    if not user_id:
        return jsonify({"error": "User not logged in"}), 401

    # Ensure the image exists
   image = Image.query.filter_by(id = image.id).first()
   if not image:
       return jsonify({"error" :"User not found"}),404


    # Check if the user already liked the image
existing_like = Like.query.fiter_by(user_id= user_id, image_is = image_id ).first()

    if existing_like:
        # User already liked the image, so we remove the like
        db.session
        liked = False
    else:
        # Insert new like and increment the likes in the images table
        cursor.execute("INSERT INTO likes (user_id, image_id) VALUES (?, ?)", (user_id, image_id))
        cursor.execute("UPDATE images SET likes = likes + 1 WHERE filename = ?", (image_id,))
        liked = True

    conn.commit()

    # Fetch the updated like count
    cursor.execute("SELECT likes FROM images WHERE filename = ?", (image_id,))
    updated_likes = cursor.fetchone()[0]
    conn.close()

    return jsonify({"liked": liked, "likes": updated_likes})


@app.route('/comment', methods=['POST'])
def comment():
    data = request.json
    comment_text = data.get('comment')
    image_id = data.get('image_id')
    user_id = session.get("user_id")

    if not user_id:
        return jsonify({"error": "User not logged in"}), 401

    if not comment_text:
        return jsonify({"error": "Comment cannot be empty"}), 400

    try:
        # Insert comment into database
        new_comment = comment(user_id=user_id, image_id=image_id, comment=comment_text)
        db.session.add(new_comment)
        db.session.commit()


        # Fetch the inserted comment details
        comment_detail = db.session.query(comment.id,User.first_name,comment.comment).join(User,comment.user_id == User.id).filter(Comment.id==new_comment.id).first()

        if comment_detail:
            return jsonify({
                "id": comment_details[0],
                "name": comment_details[1],
                "comment": comment_details[2],
            })
        else:
            return jsonify({"error": "Failed to retrieve the new comment."}), 500

    except Exception as e:
        conn.rollback()
        return jsonify({"error": "An internal error occurred. Please try again later."}), 500
    finally:
        conn.close()



if __name__ == '__main__':
    app.run(debug=True)