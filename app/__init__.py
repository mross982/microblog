from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from config import Config

# line below (and from app inport routes) is all you need for a basic app
app = Flask(__name__)
# creates the application object as an instance of class Flask imported from the flask package.


app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login = LoginManager(app)
login.login_view = 'login'

# app is the package; routes, models, etc. are the modules
from app import routes, models, errors

'''
One aspect that may seem confusing at first is that there are two entities named app. 
The app package is defined by the app directory and the __init__.py script, and is 
referenced in the from app import routes statement. The app variable is defined as an 
instance of class Flask in the __init__.py script, which makes it a member of the app 
package.
'''