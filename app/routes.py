# app/routes.py
from flask import jsonify, redirect, render_template, request, url_for, flash
from flask_login import login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
from app import app, login_manager, User, db, Message
from datetime import datetime
from openai import OpenAI
import os
from dotenv import load_dotenv


bcrypt = Bcrypt(app)


load_dotenv()

API_KEY = os.getenv('API_KEY')


def run_conversation(prompt):
    # Initialize OpenAI client
    client = OpenAI(api_key=API_KEY)

    messages = [{"role": "user", "content": prompt}]

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages
    )

    response_text = response.choices[0].message.content

    return response_text


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/')
@login_required
def index():
    username = current_user.username
    return render_template('index.html', username=username)


@app.route('/home')
@login_required
def home():
    username = current_user.username
    return render_template('home.html', username=username)


@app.route('/chat')
@login_required
def chat():
    user = current_user
    chat_history = Message.query.filter_by(sender=user).all()
    return render_template('chat.html', chat_history=chat_history)


@app.route('/submit-message', methods=['POST'])
@login_required
def submit_message():
    message_content = request.form['message']

    user = current_user
    message = Message(content=message_content, sender=user, message_type='user')
    db.session.add(message)
    db.session.commit()

    response = run_conversation(prompt=message_content)
    print(f"Message sent to user {current_user.username}: {response}")

    message = Message(content=response, sender=user, message_type='server')
    db.session.add(message)
    db.session.commit()

    return redirect(url_for('chat'))


@app.route('/mcq')
@login_required
def mcq():
    return render_template('mcq.html')


@app.route('/qst')
@login_required
def qst():
    return render_template('qst.html')


@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')


@app.route('/future')
@login_required
def future():
    return render_template('future.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        print("\nUsername:", username, "\nPassword", password)
        user = User.query.filter_by(username=username).first()

        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Login unsuccessful. Please check your username and password.', 'danger')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/sign-up', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        print("\nUsername:", username, "\nEmail:", email, "\nPassword", password)

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        existing_user_username = User.query.filter_by(username=username).first()
        existing_user_email = User.query.filter_by(email=email).first()

        if existing_user_username:
            flash('Username is already taken. Please choose a different one.', 'danger')
        elif existing_user_email:
            flash('Email is already taken. Please choose a different one.', 'danger')
        else:
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
            user = User(username=username, email=email, password=hashed_password)
            db.session.add(user)
            db.session.commit()

            flash('Your account has been created! You can now log in.', 'success')
            return redirect(url_for('login'))

    return render_template('sign-up.html')
