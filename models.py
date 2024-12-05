from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    # Add relationships
    likes = db.relationship('Like', backref='user', lazy=True)
    comments = db.relationship("Comment", backref="user", lazy="dynamic")

class Image(db.Model):
    __tablename__ = 'images'
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    likes = db.Column(db.Integer, default=0)
    # Add relationships
    image_likes = db.relationship('Like', backref='image', lazy='dynamic', cascade="all, delete-orphan")
    comments = db.relationship('Comment', backref='image', lazy='dynamic', cascade="all, delete-orphan")

class Like(db.Model):
    __tablename__ = 'likes'
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', name='fk_likes_user_id'), nullable=False)
    image_id = db.Column(db.Integer, db.ForeignKey('images.id'), nullable=False)
    
    # Define the unique constraint in __table_args__
    __table_args__ = (
        db.UniqueConstraint('user_id', 'image_id', name='uq_user_image'),
    )

class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', name='fk_comments_user_id'), nullable=False)
    image_id = db.Column(db.Integer, db.ForeignKey('images.id', name='fk_comments_image_id'), nullable=False)
    comment = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)