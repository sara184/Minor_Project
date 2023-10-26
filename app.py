from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from models.users import User, UserImage, Transaction, Payment
 # Import your User model
from config import SQLALCHEMY_DATABASE_URI, SQLALCHEMY_TRACK_MODIFICATIONS, SECRET_KEY
import os
import numpy as np
import cv2
from twilio.rest import Client
import random
import string
from twilio.base.exceptions import TwilioRestException
import razorpay
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from database import db




app = Flask(__name__)



# Configure your Flask app
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SECRET_KEY'] = SECRET_KEY

app.config['UPLOAD_FOLDER'] = 'static/images'

# Initialize the database
db.init_app(app)
migrate = Migrate(app, db)

# Razorpay configuration
RAZORPAY_API_KEY = 'rzp_test_kDG7c9ejyVQvWY'
RAZORPAY_API_SECRET = 'r3zTnpkkmzK3ooQZDdNdVxFs'

razorpay_client = razorpay.Client(auth=(RAZORPAY_API_KEY, RAZORPAY_API_SECRET))

# Twilio configuration
TWILIO_ACCOUNT_SID = 'AC66ec040e892db3cc66d3ba9cc45244d7'
TWILIO_AUTH_TOKEN = 'fce0456bb3e9c5c7a02c1830b11e6ed6'
TWILIO_PHONE_NUMBER = '+12294146107'

@app.route('/initialize_database')
def initialize_database():
    with app.app_context():
        db.create_all()
    return 'Database initialized'

@app.route('/')
def home():
    return render_template('index.html')  # Assuming you have an 'index.html' template


# Define a route for user registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        mobile_number = request.form['mobile_number']
        
        # Capture the user's facial image and save it
        if 'image' in request.files:
            image = request.files['image']
            image.save(os.path.join('static/images', f'{username}.jpg'))
        
        # Store the user's information in the database
        new_user = User(username=username, password=password, mobile_number=mobile_number)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! Please log in.')
        return redirect(url_for('login'))
    
    return render_template('registration.html')


# Define a route for user login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and user.password == password:
            session['user_id'] = user.id  # Store user ID in the session
            flash('Login successful!')
            return redirect(url_for('face_recognition'))
        else:
            flash('Invalid username or password.')

    return render_template('login.html')


# Define a route for face recognition
@app.route('/face_recognition', methods=['GET', 'POST'])
def face_recognition():
    if request.method == 'POST':
        username = request.form['username']
        login_image = request.files['image']
        stored_image = f'static/images/{username}.jpg'

        # Load the stored user's image
        stored_image = cv2.imread(stored_image)
        # Load the user's provided login image
        login_image = cv2.imdecode(np.fromstring(login_image.read(), np.uint8), cv2.IMREAD_COLOR)

        # Perform face recognition (you can use a more advanced method here)
        if np.array_equal(stored_image, login_image):
            session['user_id'] = User.query.filter_by(username=username).first().id
            flash('Face recognition successful!')
            return redirect(url_for('payment'))
        else:
            flash('Face recognition failed.')
            
    return render_template('face_recognition.html')


# Define a route for OTP generation
@app.route('/generate_otp')
def generate_otp():
    # Implement OTP generation and sending logic here
    
    
    if 'user_id' in session:
        user = User.query.get(session['user_id'])

        if user:
            otp = generate_otp()  # Generate a random OTP
            user.otp = otp  # Store the OTP in the user's database record
            db.session.commit()

            # Send the OTP via SMS using Twilio
            client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
            try:
                message = client.messages.create(
                    to=user.mobile_number,
                    from_=TWILIO_PHONE_NUMBER,
                    body=f'Your OTP: {otp}')
                return jsonify({'message': 'OTP sent successfully!'})
            except TwilioRestException as e:
                return jsonify({'error': 'Failed to send OTP via SMS.'})

        return jsonify({'error': 'User not found.'})

    return jsonify({'error': 'User not authenticated.'})
    

# Define a route for Payment
@app.route('/payment', methods=['GET', 'POST'])
def payment():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])

        if user:
            if request.method == 'POST':
                # Get transaction details from the form
                amount = request.form.get('amount')
                card_number = request.form.get('card_number')
                expiry_date = request.form.get('expiry_date')
                cvv = request.form.get('cvv')
                otp = request.form.get('otp')

                # Verify the OTP
                if otp == user.otp:
                    # Payment processing logic
                    try:
                        response = razorpay_client.order.create({
                            'amount': int(amount) * 100,  # Amount in paise (e.g., 100 INR is 10000 paise)
                            'currency': 'INR',
                            'payment_capture': 1
                        })

                        order_id = response['id']
                        return render_template('payment.html', order_id=order_id)
                    except Exception as e:
                        flash('Payment failed.')
                else:
                    flash('Invalid OTP. Please try again.')

            return render_template('payment.html')
        else:
            flash('User not found.')
    else:
        flash('User not authenticated.')
    return redirect(url_for('login'))







if __name__ == '__main__':
    app.run(debug=True)


