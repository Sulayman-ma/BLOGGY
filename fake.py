from random import randint
from sqlalchemy.exc import IntegrityError
from faker import Faker
from blog import db
from blog.models import User, Post



"""
The Faker module generates fake users basically for the application.
Manually creating users is tedious, so the Faker class comes in and does all the
work for you. 
"""

def users(count):
    fake = Faker()
    i = 0
    while i < count:
        u = User(email = fake.email(), username = fake.user_name(),
                 password = 'password', confirmed = True,
                 name = fake.name(), location= fake.city(),
                 about_me = fake.text(), member_since = fake.past_date())
        db.session.add(u)
        try:
            # Try to commit and counter IntegrityError to avoid duplicate users
            db.session.commit()
            i += 1
        except IntegrityError:
            db.session.rollback()



def posts(count):
    fake = Faker()
    user_count = User.query.count()
    for i in range(count):
        u = User.query.offset(randint(0, user_count - 1)).first()
        p = Post(body = fake.text(), timestamp = fake.past_date(),
                 author = u)
        db.session.add(p)
    db.session.commit()


# File is run once and users and posts and created.
from app import app
app_ctx = app.app_context()
app_ctx.push()
users(50)
posts(50)
