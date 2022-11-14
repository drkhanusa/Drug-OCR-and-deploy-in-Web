from app import db
from flask_login import UserMixin
from datetime import datetime

class User(UserMixin, db.Model):
    __tablename__ = "user"
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    pwd = db.Column(db.String(300), nullable=False, unique=True)

    def __repr__(self):
        return '<User %r>' % self.username

class Note(db.Model):
    __tablename__ = "note"
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username_id = db.Column(db.Integer)
    text = db.Column(db.Text)
    done = db.Column(db.Boolean)
    dateAdded = db.Column(db.DateTime, default=datetime.now())