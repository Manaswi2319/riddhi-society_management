from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='member')
    user_type = db.Column(db.String(20), default='resident')  # resident, staff, tenant
    flat_no = db.Column(db.String(10))
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100))
    phone = db.Column(db.String(15))
    address = db.Column(db.String(200))
    joining_date = db.Column(db.DateTime, default=datetime.utcnow)

class Member(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    flat_no = db.Column(db.String(10), unique=True, nullable=False)
    owner_name = db.Column(db.String(100), nullable=False)
    family_members = db.Column(db.Integer, default=1)
    phone = db.Column(db.String(15))
    email = db.Column(db.String(100))
    parking_slot = db.Column(db.String(10))

class Complaint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    flat_no = db.Column(db.String(10), nullable=False)
    complaint_type = db.Column(db.String(50))
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='Pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Bill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    flat_no = db.Column(db.String(10), nullable=False)
    month = db.Column(db.String(20), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    paid = db.Column(db.Boolean, default=False)
    due_date = db.Column(db.DateTime)

# Admin Section Models
class Section(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    section_name = db.Column(db.String(100), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Content(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    section_id = db.Column(db.Integer, db.ForeignKey('section.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.String(80))
    
    section = db.relationship('Section', backref=db.backref('contents', lazy=True))

class Receipt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    receipt_no = db.Column(db.String(50), unique=True, nullable=False)
    flat_no = db.Column(db.String(10), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_mode = db.Column(db.String(50))
    receipt_date = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.String(80))

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    expense_type = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    amount = db.Column(db.Float, nullable=False)
    expense_date = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.String(80))