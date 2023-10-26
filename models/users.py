from datetime import datetime
from sqlalchemy import ForeignKey, Float, String, Integer, Column, DateTime
from sqlalchemy.orm import relationship
from database import db

class User(db.Model):
    __tablename__ = 'users'  # Define the table name

    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    full_name = Column(String(120), nullable=False)
    mobile_number = Column(String(15), unique=True, nullable=False)

    # Add more fields as needed for your user model
    # ...

    # Define a one-to-many relationship between User and UserImage
    images = relationship('UserImage', backref='user', lazy=True)

    def __init__(self, username, password, full_name, mobile_number):
        self.username = username
        self.password = password
        self.full_name = full_name
        self.mobile_number = mobile_number

class UserImage(db.Model):
    __tablename__ = 'user_images'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    filename = Column(String(255), nullable=False)

    def __init__(self, user_id, filename):
        self.user_id = user_id
        self.filename = filename

class Transaction(db.Model):
    __tablename__ = 'transactions'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    amount = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __init__(self, user_id, amount):
        self.user_id = user_id
        self.amount = amount

class Payment(db.Model):
    __tablename__ = 'payments'

    id = Column(Integer, primary_key=True)
    transaction_id = Column(Integer, ForeignKey('transactions.id'), nullable=False)
    card_number = Column(String(16), nullable=False)
    expiry_date = Column(String(7), nullable=False)
    cvv = Column(String(3), nullable=False)

    def __init__(self, transaction_id, card_number, expiry_date, cvv):
        self.transaction_id = transaction_id
        self.card_number = card_number
        self.expiry_date = expiry_date
        self.cvv = cvv
