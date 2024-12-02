from flask import Flask, render_template, request, redirect,flash,url_for,jsonify, session
import sqlite3
import os
from werkzeug.utils import secure_filename

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
                user_id, first_name= user
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

# @app.route("/Home")
# def Home():
#     conn = sqlite3.connect("User_data.db")
#     cursor = conn.cursor()
#     cursor.execute("SELECT filename, description , likes FROM images")
#     images = cursor.fetchall()
#     conn.close()
#     return render_template("Home.html",images=images)
@app.route('/Home')
def Home():
    user_id = session.get('user_id')
    conn = sqlite3.connect("User_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT filename, description, likes FROM images")
    images = cursor.fetchall()

    images_with_comment = []
    for image in images:
        cursor.execute(('''
            SELECT comments.id, users.first_name, comments.comment FROM comments c
            JOIN users u ON comments.user_id = users.id
            WHERE comments.image_id = ?
            ORDER BY comments.created_at ASC
        '''), (image[0],))
        comments = cursor.fetchall()
        images_with_comment.append((image[0], image[1], image[2], image[3], comments))

    conn.close()
    return render_template("home.html", images=images)
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

            conn.commit()
            conn.close()

            flash(("Image Upload Successfully", "success"))
            return  redirect("/Home")

    return  render_template("upload.html")


@app.route('/like', methods=["POST"])
def like():
    data = request.json
    image_id = data['image_id']
    user_id = session.get('user_id')  # Fetch user ID from session

    if not user_id:
        return jsonify({"error": "User not logged in"}), 401

    conn = sqlite3.connect("User_data.db")
    cursor = conn.cursor()

    # Ensure the image exists
    cursor.execute("SELECT * FROM images WHERE filename = ?", (image_id,))
    image = cursor.fetchone()
    if not image:
        conn.close()
        return jsonify({"error": "Image not found"}), 404

    # Check if the user already liked the image
    cursor.execute("SELECT * FROM likes WHERE user_id = ? AND image_id = ?", (user_id, image_id))
    like_exists = cursor.fetchone()

    if like_exists:
        conn.close()
        return jsonify({"error": "Already liked this post"}), 400  # Bad Request

    # Add the like
    cursor.execute("INSERT INTO likes (user_id, image_id) VALUES (?, ?)", (user_id, image_id))
    cursor.execute("UPDATE images SET likes = likes + 1 WHERE filename = ?", (image_id,))
    conn.commit()

    # Fetch the updated like count
    cursor.execute("SELECT likes FROM images WHERE filename = ?", (image_id,))
    updated_likes = cursor.fetchone()[0]
    conn.close()

    return jsonify({"likes": updated_likes})

@app.route('/comment', methods = ["GET", "POST"])
def comment():
    data = request.json
    comment_text = data('comment')
    image_id = data('image_id')
    user_id = session.get("user_id")

    conn = sqlite3.connect("user_data_db")
    cursor = conn.cursor()

    cursor.execute( "INSERT INTO comments (user_id, image_id, comment) VALUES (?,?)",(user_id, image_id,comment_text ))
    conn.commit()
    conn.close()





if __name__ == '__main__':
    app.run(debug=True)