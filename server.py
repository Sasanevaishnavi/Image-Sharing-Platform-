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
    user_id = session.get('user_id')
    image_id = 'image_id'

    if not user_id:
        return redirect("/login")
    conn = sqlite3.connect("User_data.db")
    cursor = conn.cursor()



    # for image in cursor.execute("SELECT filename, description, likes FROM images"):
    #     image == user_id
    #     cursor.execute("SELECT * FROM likes WHERE user_id = ? AND image_id = ?", (user_id, image_id))
    #     is_like = cursor.fetchone()
    #     return is_like == True

    cursor.execute("""
            SELECT i.filename, i.description, i.likes,
                   CASE WHEN l.user_id IS NOT NULL THEN 1 ELSE 0 END AS is_liked
            FROM images i
            LEFT JOIN likes l ON i.filename = l.image_id AND l.user_id = ?
        """, (user_id,))

    images = cursor.fetchall()  # Fetch all results



    images_with_comment = []
    for image in images:
        cursor.execute("""
                   SELECT c.id, u.first_name, c.comment 
                   FROM comments c 
                   JOIN users u ON c.user_id = u.id 
                   WHERE c.image_id = ? 
                   ORDER BY c.created_at ASC
               """, (image[0],))
        comments = cursor.fetchall()

        images_with_comment.append({

            'filename': image[0],
            'description': images[1],
            'likes': image[2],
            'comments': comments
        })

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


@app.route('/like', methods=['POST'])
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


    image_id = request.form.get('image_id')
    cursor.execute("""
        INSERT INTO likes (user_id, image_id) VALUES (?, ?)
    """, (user_id, image_id))
    conn.commit()
    return jsonify({"message": "Image liked successfully"})

    # Check if the user already liked the image
    cursor.execute("SELECT * FROM likes WHERE user_id = ? AND image_id = ?", (user_id, image_id))
    like_exists = cursor.fetchone()

    if like_exists:
        # User already liked the image, so we remove the like
        cursor.execute("DELETE FROM likes WHERE user_id = ? AND image_id = ?", (user_id, image_id))
        cursor.execute("UPDATE images SET likes = CASE WHEN likes > 0 THEN likes - 1 ELSE 0 END WHERE filename = ?", (image_id,))
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


@app.route('/comment', methods = ["GET", "POST"])
def comment():
    data = request.json
    comment_text = data.get('comment')
    image_id = data.get('image_id')
    user_id = session.get("user_id")

    if not user_id:
        return jsonify({"error": "User not logged in"}), 401

    conn = sqlite3.connect("User_data.db")
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO comments (user_id, image_id, comment) VALUES (?, ?, ?)",
            (user_id, image_id, comment_text)
        )
        conn.commit()

        # Fetch the comment details to send back to frontend
        cursor.execute("""
               SELECT c.id, u.first_name, c.comment 
               FROM comments c 
               JOIN users u ON c.user_id = u.id 
               WHERE c.id = ?
           """, (cursor.lastrowid,))
        comment_details = cursor.fetchone()

        conn.close()

        return jsonify({
            "id": comment_details[0],
            "name": comment_details[1],
            "comment": comment_details[2],

        })

    except Exception as e:
        conn.rollback()

        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()



if __name__ == '__main__':
    app.run(debug=True)