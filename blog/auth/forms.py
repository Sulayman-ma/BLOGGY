from flask_wtf import FlaskForm
from wtforms.fields import StringField, SubmitField, PasswordField, BooleanField
from wtforms.validators import DataRequired, Length, Regexp, EqualTo
from wtforms import ValidationError
from ..models import User



class RegForm(FlaskForm):
    email = StringField('Email: ', validators = [DataRequired(), Length(1, 64)])
    username = StringField('Username: ',
                           validators = [DataRequired(), Length(1, 64),
                                         Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
                                                'Username can only contain '
                                                'letters, numbers dots and '
                                                'underscores.')])
    password = PasswordField('Password: ',
                             validators = [DataRequired(),
                                           EqualTo('password2', message =
                                           'Passwords must match.')])
    password2 = PasswordField('Confirm Password: ', validators = [DataRequired()])
    submit = SubmitField('Register')

    @staticmethod
    def validate_email(self, field):
        if User.query.filter_by(email = field.data).first():
            raise ValidationError('Email already registered.')


    @staticmethod
    def validate_username(self, field):
        if User.query.filter_by(username = field.data).first():
            raise ValidationError('Username already in use.')


class LoginForm(FlaskForm):
    email = StringField('Email: ', validators = [DataRequired(), Length(1, 64)])
    password = PasswordField('Password: ', validators = [DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Log In')
