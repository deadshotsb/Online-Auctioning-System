from . import db
from flask_login import UserMixin

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(20), nullable=False)
    selling_items = db.relationship('Item', backref='user', lazy=True)

    def __repr__(self):
        return "<User %r>" % self.username

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    seller_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    item_name = db.Column(db.String(30), nullable=False)
    item_pic = db.Column(db.Text, nullable=False)
    pic_name = db.Column(db.Text, unique=True)
    mimetype = db.Column(db.Text)
    category = db.Column(db.String(30), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    duration = db.Column(db.Time, nullable=False)
    port = db.Column(db.Integer, unique=True)
    start_bid = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return "<Item %r>" % self.category