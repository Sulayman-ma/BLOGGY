from flask_wtf import FlaskForm
from wtforms.fields import StringField, SubmitField, TextAreaField, BooleanField, \
    SelectField
from wtforms.validators import Length, DataRequired, Regexp
from wtforms.validators import ValidationError
from ..models import Role, User



class EditProfileForm(FlaskForm):
    name = StringField('Real Name: ', validators = [Length(0, 64)])
    location = StringField('Location: ', validators = [Length(0, 64)])
    about_me = TextAreaField('About Me')
    submit = SubmitField('Submit')


class EditProfileAdminForm(FlaskForm):
    email = StringField('Email: ', validators = [DataRequired(), Length(1, 64)])
    username = StringField('Username', validators = [DataRequired(), Length(1, 64),
                            Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
               'Usernames must have only letters, numbers, dots or '
               'underscores')])
    confirmed = BooleanField('Confirmed')
    role = SelectField('Role', coerce = int)
    name = StringField('Real name', validators = [Length(0, 64)])
    location = StringField('Location', validators = [Length(0, 64)])
    about_me = TextAreaField('About me')
    submit = SubmitField('Submit')

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.role.choices = [(role.id, role.name)
                             for role in Role.query.order_by(Role.name).all()]
        self.user = user

    def validate_email(self, field):
        """The method raises an error if and only if, the user's email is changed
        and another user happens to be using the same email."""
        if field.data != self.user.email and \
                User.query.filter_by(email = field.data).first():
            raise ValidationError('Email already registered.')

    def validate_username(self, field):
        """Same as the method above, but raises the error upon username
        duplication."""
        if field.data != self.user.username and \
                User.query.filter_by(username = field.data):
            raise ValidationError('Username already in use.')


class PostForm(FlaskForm):
    body = TextAreaField(validators = [DataRequired()])
    submit = SubmitField('Submit')

