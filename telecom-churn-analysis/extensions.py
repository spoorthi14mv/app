from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()
login = LoginManager()
login.login_view = 'auth.login'
login.login_message_category = 'info'
csrf = CSRFProtect()
