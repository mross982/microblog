from datetime import datetime
from flask import render_template, flash, redirect, url_for, request
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.urls import url_parse
from app import app, db
from app.forms import LoginForm, RegistrationForm, EditProfileForm, PostForm
from app.models import User, Post

#These routes are know as the view function
# Note the 'Post/Redirect/Get' pattern (even redirect to the same page). This avoids inserting 
# duplicate posts when a user refreshes the page after submitting a web form.


@app.before_request
def before_request():
    '''
    The @before_request decorator from Flask register the decorated function to be executed right 
    before the view function. This is extremely useful because now I can insert code that I want 
    to execute before any view function in the application, and I can have it in a single place. 
    The implementation simply checks if the current_user is logged in, and in that case sets the 
    last_seen field to the current time. 
    '''
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        # the reason db.session.add() is not located here is b/c current_user indicates the database
        # has already been queried that will add the user to the database session.
        db.session.commit()


@app.route('/')
@app.route('/index') # default method only includes 'GET'
@login_required
def index():
    # form = PostForm()
    # if form.validate_on_submit():
    #     post = Post(body=form.post.data, author=current_user)
    #     db.session.add(post)
    #     db.session.commit()
    #     flash('Your post is now live!')
    #     return redirect(url_for('index'))
    posts = [
        {'author': {'username': 'Miguel'},'body': 'Some beautiful text'},
        {'author': {'username': 'Susan B'}, 'body': 'Susan B Anthony is the GREATEST!'}
    ]

    return render_template('index.html', title='Home', posts=posts)

'''
The render_template() function invokes the Jinja2 template engine that comes bundled 
with the Flask framework. Jinja2 substitutes {{ ... }} blocks in the template with the 
corresponding values, given by the arguments provided in the render_template() call.
'''


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        # user = {'username', 'Michael'} # mock user object for initial dev
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

'''
When a route has a dynamic component (e.g. <>), Flask will accept any text in that portion 
of the URL, and will invoke the view function with the actual text as an argument. For 
example, if the client browser requests URL /user/susan, the view function is going to be 
called with the argument username set to 'susan'. 
'''
@app.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404() # sends a 404 if no match
    # other query options include .first() and .all()
    # returns user object with attributes of field names in the database
    posts = [
        {'author': user, 'body': 'Test post #1'},
        {'author': user, 'body': 'Test post #2'}
    ]
    return render_template('user.html', user=user, posts=posts)


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    # form = EditProfileForm() # original
    form = EditProfileForm(current_user.username) # allows error caused by selecting same username
    # as someone else to be resolved without interference if you enter your current username
    if form.validate_on_submit(): # only returns true if a POST method AND information is validated
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.') # sends text to the flash section of the base template
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET': # if the client is GET info (i.e. first directed to the URL)
        form.username.data = current_user.username # fill in the fields with previously entered data
        form.about_me.data = current_user.about_me # from the database
    return render_template('edit_profile.html', title='Edit Profile',
                           form=form)
