from datetime import datetime
from hashlib import md5
from app import db, login
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self): # tells python what to do when the print() method is invoked
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
            digest, size)


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<Post {}>'.format(self.body)

'''
to see the def__repr__ results type the following into the interpreter:

>>> from app.models import User
>>> u = User(username='susan', email='susan@example.com')
>>> u
<User susan>

The first time you create a new app, you will need to enter the following into the interpreter:

(venv) $ flask db init

With the migration repository in place, it is time to create the first database migration, 
which will include the users table that maps to the User database model. There are two ways 
to create a database migration: manually or automatically. To generate a migration automatically, 
Alembic compares the database schema as defined by the database models, against the actual 
database schema currently used in the database. It then populates the migration script with the 
changes necessary to make the database schema match the application models.

In this case, since there is no previous database, the automatic migration will add the entire 
User model to the migration script. The flask db migrate sub-command generates these automatic 
migrations:

(venv) $ flask db migrate -m "users table"

The generated migration script has two functions called upgrade() and downgrade(). The upgrade() 
function applies the migration, and the downgrade() function removes it.

The flask db migrate command does not make any changes to the database, it just generates the 
migration script. To apply the changes to the database, the flask db upgrade command must be used.

(venv) $ flask db upgrade

Because this application uses SQLite, the upgrade command will detect that a database does not exist 
and will create it (you will notice a file named app.db is added after this command finishes, that 
is the SQLite database). When working with database servers such as MySQL and PostgreSQL, you have 
to create the database in the database server before running upgrade.

Note that Flask-SQLAlchemy uses a "snake case" naming convention for database tables by default. For 
the User model above, the corresponding table in the database will be named user. For a 
AddressAndPhone model class, the table would be named address_and_phone. If you prefer to choose your 
own table names, you can add an attribute named __tablename__ to the model class, set to the desired 
name as a string.

From the interpreter:

>>> from app import db
>>> from app.models import User, Post

>>> u = User(username='susan', email='susan@example.com')
>>> db.session.add(u)
>>> db.session.commit()

>>> users = User.query.all()
>>> users
[<User john>, <User susan>]
>>> for u in users:
...     print(u.id, u.username)
...
1 john
2 susan

>>> u = User.query.get(1)
>>> p = Post(body='my first post!', author=u)
>>> db.session.add(p)
>>> db.session.commit()

Additional database queries

>>> # get all posts written by a user
>>> u = User.query.get(1)
>>> u
<User john>
>>> posts = u.posts.all()
>>> posts
[<Post my first post!>]

>>> # same, but with a user that has no posts
>>> u = User.query.get(2)
>>> u
<User susan>
>>> u.posts.all()
[]

>>> # print post author and body for all posts 
>>> posts = Post.query.all()
>>> for p in posts:
...     print(p.id, p.author.username, p.body)
...
1 john my first post!

# get all users in reverse alphabetical order
>>> User.query.order_by(User.username.desc()).all()
[<User susan>, <User john>]

Final Clean up

>>> users = User.query.all()
>>> for u in users:
...     db.session.delete(u)
...
>>> posts = Post.query.all()
>>> for p in posts:
...     db.session.delete(p)
...
>>> db.session.commit()
'''
