from datetime import datetime
from hashlib import md5 # for the avitar
from app import db, login
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


# see section on followers below
# Note that I am not declaring this table as a model, like I did for the users and 
# posts tables. Since this is an auxiliary table that has no data other than the foreign 
# keys, I created it without an associated model class.
followers = db.Table('followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id')))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)


    # Many to Many self-referential relationship table
    followed = db.relationship(
        # 'User' is the right side entity of the relationship
        'User', secondary=followers,
        # The followers.c.follower_id expression references the follower_id column of the association table.
        # primaryjoin indicates the condition that links the left side entity (the follower user) with the association table.
        primaryjoin=(followers.c.follower_id == id),
        # secondaryjoin indicates the condition that links the right side entity (the followed user) with the association table.
        secondaryjoin=(followers.c.followed_id == id),
        # backref defines how this relationship will be accessed from the right side entity. From the left side, the relationship 
        # is named followed, so from the right side I am going to use the name followers 
        backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')
        # The additional lazy argument indicates the execution mode for this query. A mode of dynamic sets up the query to not 
        # run until specifically requested,

    def follow(self, user):
        # method to add follower to user; user1.followed.append(user2)
        if not self.is_following(user): # prevents duplicate unfollow data records between the two users
            self.followed.append(user)

    def unfollow(self, user):
        # user1.followed.remove(user2)
        if self.is_following(user): # prevents duplicate unfollow data records between the two users
            self.followed.remove(user)

    def is_following(self, user):
        # The is_following() method issues a query on the followed relationship to check if a link between two users already exists. 
        return self.followed.filter(
            followers.c.followed_id == user.id).count() > 0

    # there are three main sections designed by the join(), filter() and order_by() methods of the SQLAlchemy query object
    def followed_posts(self):
        # What I'm saying with this call is that I want the database to create a temporary table that combines data from posts 
        # and followers tables. The data is going to be merged according to the condition that I passed as argument.
        followed = Post.query.join(
            # The first argument is the followers association table,
            # the second argument is the join condition.
            followers, (followers.c.followed_id == Post.user_id)).filter(
            #  the followed_id field of the followers table must be equal to the user_id of the posts table.
                followers.c.follower_id == self.id).order_by(
                # Since this query is in a method of class User, the self.id expression refers to the user ID of the user I'm interested in.
                    Post.timestamp.desc())
                    # Most recent time stamp first
        own = Post.query.filter_by(user_id=self.id)
        # query that returns your own posts
        return followed.union(own).order_by(Post.timestamp.desc())
        # own and followed are combined the resorted



    def __repr__(self): # tells python what to do when the print() method is invoked
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        '''
        The new avatar() method of the User class returns the URL of the user's avatar image, scaled to the 
        requested size in pixels. For users that don't have an avatar registered, an "identicon" image will 
        be generated. To generate the MD5 hash, I first convert the email to lower case, as this is required 
        by the Gravatar service. Then, because the MD5 support in Python works on bytes and not on strings, 
        I encode the string as bytes before passing it on to the hash function.
        - this is called from the user template & _post sub template 
        '''
        digest = md5(self.email.lower().encode('utf-8')).hexdigest() # gets a hash code for user's email address
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
            digest, size) # from gravatar, sends in hash code, (?-new arg) d argument for returning images
            # from unregistered users (identicon = geometric shapes), (&-new arg) s for size in pixels 
            # default (80 x 80)


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
Troubleshooting

interact with app database by starting shell
(venv) $ flask shell

print list of tables in the database
>>> print(db.metadata.tables.keys())

>>> for table in db.metadata.tables.keys():
...     tb = db.table(table)
...     pprint(tb.__dict__.keys())


to see the def__repr__ results type the following into the interpreter:

>>> flask shell

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

If you were to add new fields to the database, you would need to perform this same step
(venv) $ flask db migrate -m "new fields in user model"

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
...

******************************** FOLLOWERS *******************************
The representation of a many-to-many relationship requires the use of an 
auxiliary table called an association table.
While it may not seem obvious at first, the association table with its 
two foreign keys is able to efficiently answer all the queries about the relationship.

Looking at the summary of all the relationship types, it is easy to determine that 
the proper data model to track followers is the many-to-many relationship, because 
a user follows many users, and a user has many followers. 
But there is a twist. In the students and teachers example I had two entities that 
were related through the many-to-many relationship. But in the case of followers, I 
have users following other users, so there is just users.

The second entity of the relationship is also the users. A relationship in which 
instances of a class are linked to other instances of the same class is called a 
self-referential relationship.

AFter creating the new relationshio table,
The changes to the database need to be recorded in a new database migration:

(venv) $ flask db migrate -m "followers"
(venv) $ flask db upgrade

the is_following() supporting method to make sure the requested action makes sense. 
For example, if I ask user1 to follow user2, but it turns out that this following 
relationship already exists in the database, I do not want to add a duplicate. The 
same logic can be applied to unfollowing.

Obtaining the Posts from Followed Users

The most obvious solution is to run a query that returns the list of followed users, 
which as you already know, it would be user.followed.all(). Then for each of these 
returned users I can run a query to get the posts. Once I have all the posts I can 
merge them into a single list and sort them by date. Sounds good? Well, not really.
This is actually an awful solution that does not scale well.

There is really no way to avoid this merging and sorting of blog posts, but doing 
it in the application results in a very inefficient process. This kind of work is 
what relational databases excel at. The database has indexes that allow it to 
perform the queries and the sorting in a much more efficient way that I can 
possibly do from my side. So what I really want is to come up with a single 
database query that defines the information that I want to get, and then let the 
database figure out how to extract that information in the most efficient way.

Joins
Post.query.join(followers, (followers.c.followed_id == Post.user_id))

imaging the table structure required to retrieve the posts of of a uers's followed
users. 
JOIN
First query identifies the user ID from the UserName. 
Second query matches the user IDs of the users followed accounts in relation table.
Third quiery returns the post IDs of the followed users
FILTER
Forth filter query results for the posts followed by a single user
ORDER BY
Fifth sort qurey results by (Post.timestamp.desc()) for example






Even though adding and removing followers is fairly easy, I want to promote reusability 
in my code, so I'm not going to sprinkle "appends" and "removes" through the code. Instead,
I'm going to implement the "follow" and "unfollow" functionality as methods in the User model. 
It is always best to move the application logic away from view functions and into models or 
other auxiliary classes or modules, because as you will see later in this chapter, that makes 
unit testing much easier.

'''