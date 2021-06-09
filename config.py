from os.path import dirname, join, abspath
from os import environ



base_dir = abspath(dirname(__file__))

class Config:
    # Always better to import from the environmental variables
    SECRET_KEY = 'generate key here'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAIL_SERVER = 'smtp.googlemail.com'
    MAIL_PORT = '587'
    MAIL_USE_TLS = 'true'
    MAIL_USERNAME = 'mas03.abba@gmail.com'
    MAIL_PASSWORD = environ.get('EMAIL_PASS')
    BLOGGY_ADMIN = 'suleyman.abba@gmail.com'

    @staticmethod
    def init_app(app):
        pass


class Development(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + join(base_dir, 'dev.sqlite')


configs = {
    'dev': Development,

    'default': Development
}
