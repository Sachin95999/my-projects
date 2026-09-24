from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    roll_no = db.Column(db.String(50), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    password = db.Column(db.String(200), nullable=False)
    hostel_name = db.Column(db.String(100), nullable=True)
    room_no = db.Column(db.String(20), nullable=True)
    is_admin = db.Column(db.Boolean, default=False)
    
    complaints = db.relationship('Complaint', backref='student', lazy=True)
    items_reported = db.relationship('LostFoundItem', backref='reporter', lazy=True)
    notifications = db.relationship('Notification', backref='user', lazy=True)

class LostFoundItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False) # Electronic, Document, etc.
    item_type = db.Column(db.String(10), nullable=False) # 'lost' or 'found'
    status = db.Column(db.String(20), default='Active') # Active, Claimed
    date_reported = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Complaint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50), nullable=False) # Plumbing, Electrical, etc.
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='Pending') # Pending, In Progress, Resolved, Auto-Resolved, Reopened
    priority = db.Column(db.String(20), default='Normal') # High, Medium, Low
    assigned_worker = db.Column(db.String(100), nullable=True)
    visit_time = db.Column(db.String(100), nullable=True)
    expected_resolution_time = db.Column(db.DateTime, nullable=True)
    date_lodged = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Notice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False, default='General') # Academic, Hostel, Events, General
    is_pinned = db.Column(db.Boolean, default=False)
    posted_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)

class MessMenu(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    day = db.Column(db.String(20), nullable=False) # Monday, Tuesday ...
    meal = db.Column(db.String(20), nullable=False) # Breakfast, Lunch, Dinner
    items = db.Column(db.Text, nullable=False)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.String(300), nullable=False)
    icon = db.Column(db.String(10), default='🔔')
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
