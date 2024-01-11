# app/routes.py
from flask import redirect, render_template, request, url_for, flash
from flask_login import login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
from app import app, login_manager, User, db

bcrypt = Bcrypt(app)


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
    return render_template('chat.html')


@app.route('/mcq')
@login_required
def mcq():
    return render_template('mcq.html')


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
