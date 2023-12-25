# app/routes.py
from flask import redirect, render_template, request, url_for
from flask_login import login_user, login_required, logout_user
from app import app, login_manager, User


@login_manager.user_loader
def load_user(user_id):
    return User(user_id)


@app.route('/')
@login_required
def index():
    return render_template('index.html')


@app.route('/home')
@login_required
def home():
    return render_template('home.html')


@app.route('/chat')
@login_required
def chat():
    return render_template('chat.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        print("\nUsername:", username, "\nPassword", password)
        # Replace below if statement with actual authentication logic
        if username == 'sariitani' and password == 'sariitani101':
            user = User(1)  # Who is the user?

            print(user)
            
            login_user(user)
            return redirect(url_for('index'))
        else:
            # signify that the user was not authenticated successfully
            pass
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

        # Validate and save to the database (replace with your logic)
        # Use a secure method to hash and store the password (e.g., Flask-Bcrypt)
        return redirect(url_for('login'))
    return render_template('sign-up.html')
