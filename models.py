from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
db = SQLAlchemy()
friends_association = db.Table(
    'friends',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
    db.Column('friend_id', db.Integer, db.ForeignKey('users.id'))
)
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    
    
    bio = db.Column(db.Text, nullable=True)
    avatar_filename = db.Column(db.String(255), default='default.png')
    
    reviews = db.relationship('Review', backref='author', lazy=True)
    lists = db.relationship('ListEntry', backref='user', lazy=True)
    likes = db.relationship('ReviewLike', backref='user', lazy=True)
    comments = db.relationship('Comment', backref='author', lazy=True)
    
    friends = db.relationship(
        'User', secondary=friends_association,
        primaryjoin=(friends_association.c.user_id == id),
        secondaryjoin=(friends_association.c.friend_id == id),
        backref=db.backref('friend_of', lazy='dynamic'), lazy='dynamic'
    )

class MediaItem(db.Model):
    __tablename__ = 'media_items'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    media_type = db.Column(db.String(50), default='movie')
    image_filename = db.Column(db.String(255), nullable=True)
    
    reviews = db.relationship('Review', backref='media', lazy=True)
    lists = db.relationship('ListEntry', backref='media', lazy=True)
class Review(db.Model):
    __tablename__ = 'reviews'
    id = db.Column(db.Integer, primary_key=True)
    rating = db.Column(db.Integer, nullable=False)
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    media_id = db.Column(db.Integer, db.ForeignKey('media_items.id'), nullable=False)
    
    likes = db.relationship('ReviewLike', backref='review', lazy=True, cascade="all, delete-orphan")
    comments = db.relationship('Comment', backref='review', lazy=True, cascade="all, delete-orphan")
class ListEntry(db.Model):
    __tablename__ = 'personal_lists'
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(50), nullable=False)
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    media_id = db.Column(db.Integer, db.ForeignKey('media_items.id'), nullable=False)
class ReviewLike(db.Model):
    __tablename__ = 'review_likes'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    review_id = db.Column(db.Integer, db.ForeignKey('reviews.id'), nullable=False)
class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    review_id = db.Column(db.Integer, db.ForeignKey('reviews.id'), nullable=False)
class Report(db.Model):
    __tablename__ = 'reports'
    id = db.Column(db.Integer, primary_key=True)
    reason = db.Column(db.String(255), nullable=False) # Причина скарги
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    review_id = db.Column(db.Integer, db.ForeignKey('reviews.id'), nullable=False)