from flask import Flask
from models import db
from routes import init_routes
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
import os

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = "Success"
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///User_data.db'
    app.config['UPLOAD_FOLDER'] = os.path.join("static", "uploads")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Ensure upload folder exists
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    # Initialize extensions
    db.init_app(app)

    # Initialize Migrate
    migrate = Migrate(app, db)

    # Initialize routes
    app = init_routes(app)
    app.secret_key = 'your_secret_key_here'  # Replace with a secure random key
    app.config['SESSION_TYPE'] = 'filesystem'

    return app

# Create and initialize app
app = create_app()

# Create database tables (this is for the first time or after creating the migrations)
with app.app_context():
    db.create_all()




if __name__ == '__main__':
    app.run(debug=True)