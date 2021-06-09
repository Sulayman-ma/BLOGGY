from . import db
from . import login_manager
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import UserMixin, AnonymousUserMixin
from flask import current_app
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from datetime import datetime



class Permission:
    FOLLOW = 1
    COMMENT = 2
    WRITE = 4
    MODERATE = 8
    ADMIN = 16


class Role(db.Model):
    """Role model. Pun unintended."""
    __tablename__ = 'roles'

    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(64), unique = True)
    # Default should only be True for the User role and False for others.
    default = db.Column(db.Boolean, default = False, index = True)
    permissions = db.Column(db.Integer)

    # Link to User table
    users = db.relationship('User', backref = 'role', lazy = 'dynamic')

    def __init__(self, **kwargs):
        super(Role, self).__init__(**kwargs)
        # Always set default role to 0 if there is None. For anonymous users.
        if self.permissions is None:
            self.permissions = 0

    def __repr__(self):
        return '<{} Role - {}>'.format(self.name, self.permissions)

    def add_permission(self, perm):
        if not self.has_permission(perm):
            self.permissions += perm

    def remove_permission(self, perm):
        if self.has_permission(perm):
            self.permissions -= perm

    def reset_permissions(self):
        self.permissions = 0

    def has_permission(self, perm):
        """Uses the bitwise and operator to check if a combined permission value
        includes the given basic permission."""
        return self.permissions & perm == perm

    @staticmethod
    def insert_roles():
        # Roles defined with permissions given to each
        roles = {
            'User': [Permission.FOLLOW, Permission.COMMENT, Permission.WRITE],
            'Moderator': [Permission.FOLLOW, Permission.COMMENT, Permission.WRITE,
                          Permission.MODERATE],
            'Administrator': [Permission.FOLLOW, Permission.COMMENT,
                              Permission.WRITE, Permission.MODERATE,
                              Permission.ADMIN]
        }
        default_role = 'User'

        for r in roles:
            role = Role.query.filter_by(name = r).first()
            # If role does not exist in DB, create one.
            if role is None:
                role = Role(name = r)
            role.reset_permissions()
            # Look for role's permissions and add to the new object
            for perm in roles[r]:
                role.add_permission(perm)
            # Set default to True if Role is User and False otherwise
            role.default = (role.name == default_role)
            db.session.add(role)

        db.session.commit()


class Follow(db.Model):
    __tablename__ = 'follows'
    follower_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                            primary_key = True)
    followed_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                            primary_key = True)
    timestamp = db.Column(db.DateTime(), default = datetime.now())


class User(UserMixin, db.Model):
    # UserMixin from flask_login associates the model with login sessions
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key = True)
    email = db.Column(db.String(64), unique = True, index = True)
    username = db.Column(db.String(64), unique = True, index = True)
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default = True)
    name = db.Column(db.String(64))
    location = db.Column(db.String(64))
    about_me = db.Column(db.Text())
    member_since = db.Column(db.DateTime(), default = datetime.today())
    last_seen = db.Column(db.DateTime(), default = datetime.today())

    # Link to user Posts
    posts = db.relationship('Post', backref = 'author', lazy = 'dynamic')

    # Relationship to Follow table
    followed = db.relationship('Follow',
                               foreign_keys = [Follow.follower_id],
                               backref = db.backref('follower', lazy = 'joined'),
                               lazy = 'dynamic',
                               cascade = 'all, delete-orphan')
    followers = db.relationship('Follow',
                               foreign_keys = [Follow.followed_id],
                               backref = db.backref('followed', lazy = 'joined'),
                               lazy = 'dynamic',
                               cascade = 'all, delete-orphan')

    # Follow relationship related methods
    def follow(self, user):
        if not self.is_following(user):
            # Create a Follow instance.
            f = Follow(follower = self, followed = user)
            # Add to DB session
            db.session.add(f)

    def unfollow(self, user):
        # The followed list is filtered to find the specific followed user
        f = self.followed.filter_by(followed_id = user.id).first()
        if f:
            # If the association exists, delete the Follow instance.
            db.session.delete(f)

    def is_following(self, user):
        if user.id is None:
            return False
        return self.followed.filter_by(followed_id = user.id).first() is not None

    def is_followed_by(self, user):
        if user.id is None:
            return False
        return self.followers.filter_by(follower_id = user.id).first() is not None


    # Foreign key in model
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))

    def __repr__(self):
        return "<User {}>".format(self.username)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.role is None:
            # If the admin's email appears during registration, grant them the
            # admin role.
            if self.email == current_app.config['BLOGGY_ADMIN']:
                self.role = Role.query.filter_by(name = 'Administrator').first()
            # If user still doesn't have a role, assign them default User role
            if self.role is None:
                self.role = Role.query.filter_by(default = True).first()

    """
    Password is a decorated property that raises an error when it is accessed. 
    Of course even with brute force, it cannot be recovered as it has been hashed.
    The setter does the hashing and a verify method is needed at last. 
    """

    @property
    def password(self):
        raise AttributeError('ACCESS DENIED! PASSWORD CANNOT BE READ!')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)


    # Account confirmation methods
    def generate_confirmation_token(self, expiration = 900):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id}).decode('utf-8')

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        # noinspection PyBroadException
        try:
            data = s.loads(token.encode('utf-8'))
        except:
            return False
        # If the provided token is not equal to the user ID, the return False and
        # nullify the confirmation link and token
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True


    # User action/permission control methods
    def can(self, perm):
        # return true is the user's role has the required permission
        return self.role is not None and self.role.has_permission(perm)

    def is_administrator(self):
        return self.can(Permission.ADMIN)

    # User profile related methods
    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)
        db.session.commit()


class AnonymousUser(AnonymousUserMixin):
    @staticmethod
    def can(permissions):
        return False

    @staticmethod
    def is_administrator():
        return False


# The login manager will use the application's custom anonymous user class so we
# set the attribute accordingly.
login_manager.anonymous_user = AnonymousUser

@login_manager.user_loader
def load_user(user_id):
    """
    This method is registered with the decorator above such that when Flask-Login
    needs to load the user, it calls it and of course the method will query the DB
    and retrieve the user.
    """
    return User.query.get(int(user_id))


class Post(db.Model):
    __tablename__ = 'posts'

    id = db.Column(db.Integer, primary_key = True)
    body = db.Column(db.Text())
    timestamp = db.Column(db.DateTime(), index = True, default = datetime.now())
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.timestamp = datetime.now()
