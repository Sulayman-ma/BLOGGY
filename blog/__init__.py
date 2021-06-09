from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_moment import Moment
from config import configs


# TODO: Both markdown and Flask-PageDown to allow users to enter rich-text
db = SQLAlchemy()
mail = Mail()
moment = Moment()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'


def create_app(config_name):
    app = Flask(__name__)

    # Adding configurations
    app.config.from_object(configs[config_name])
    configs[config_name].init_app(app)

    # Extension initializations
    db.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    login_manager.init_app(app)

    # Blueprint registration here
    from .auth import auth as auth_blueprint
    from .main import main as main_blueprint

    app.register_blueprint(main_blueprint)
    app.register_blueprint(auth_blueprint, url_prefix = '/auth')

    # Application instance
    return app
