# app/__init__.py
from flask import Flask
from flask_login import LoginManager

app = Flask(__name__, template_folder='../templates')
app.config['SECRET_KEY'] = '9d125d217fca3a2938b669e0553189a4'

login_manager = LoginManager(app)
login_manager.login_view = 'login'

from flask_login import UserMixin
class User(UserMixin):
    def __init__(self, user_id):
        self.id = user_id

from app import routes
