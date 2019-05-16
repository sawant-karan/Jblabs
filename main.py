from flask import Flask,jsonify,request,render_template,Response,session,abort
import os
from flask_cors import CORS
from datetime import datetime, timedelta
import json
from string import ascii_uppercase as ALC
from itertools import chain, product
import redis
from pymongo import MongoClient
import jwt
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user

redis_conn = redis.StrictRedis(host='127.0.0.1', port=6381, password='', db=0)

# Mongo Database Connector
url = "mongodb+srv://karan:karan1012@cluster0-chsff.mongodb.net/karan"
client = MongoClient(url)
db = client['karan']

userschemas = db.userschemas

# silly user model
class User(UserMixin):

    def __init__(self, id):
        self.id = id
        self.name = "user" + str(id)
        self.password = self.name + "_secret"
        
    def __repr__(self):
        return "%d/%s/%s" % (self.id, self.name, self.password)


# Declaring the app
app = Flask(__name__)
cors = CORS(app, resources={r"/*": {"origins": "*"}})

# flask-login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    return render_template('login.html')

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/report', methods=['GET', 'POST'])
@login_required
def report():
    return render_template('report.html')

@app.route('/user/', methods=['GET', 'POST', 'DELETE', 'PATCH'])
@login_required
def user():
    if request.method == 'GET':
        return "Get"
    data = request.get_json()
    if request.method == 'POST':
        return "Post"
    if request.method == 'DELETE':
        return "Delete"
    if request.method == 'PATCH':
        return "Patch"

# somewhere to logout
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return Response('<p>Logged out</p>')

# handle login failed
@app.errorhandler(401)
def page_not_found(e):
    return Response('<p>Login failed</p>')

# callback to reload the user object        
@login_manager.user_loader
def load_user(userid):
    return User(userid)


if __name__ == "__main__":
	port = int(os.environ.get("PORT", 13000))
	app.run(host='0.0.0.0', port=port,threaded = True, debug=True)