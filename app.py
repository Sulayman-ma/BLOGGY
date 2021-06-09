from blog import db, create_app
from blog.models import User, Role, Permission, Post
from flask_migrate import Migrate



app = create_app('dev')
migrate = Migrate(app, db)


@app.shell_context_processor
def make_shell_context():
    return dict(db = db, User = User, Role = Role, Permission = Permission,
                Post = Post)
