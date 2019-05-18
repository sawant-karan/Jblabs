from flask import Flask,jsonify,request,render_template,Response,session,abort
import flask
import os
from flask_cors import CORS
from datetime import datetime, timedelta
import json
from string import ascii_uppercase as ALC
from itertools import chain, product
import redis
from pymongo import MongoClient
import flask_login
import jwt
import bson
import hashlib
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user

redis_conn = redis.StrictRedis(host='127.0.0.1', port=6381, password='', db=0)

# Mongo Database Connector
url = "mongodb://<username>:<password>@<host>:27017/test"
client = MongoClient(url)
db = client["test"]

userschemas = db.userschemas
reportschemas = db.reportchemas
# users = {"karan@gmail.com": {"password": "karan", "data": {"name": "Karan Sawant", "_id": "12332467654322", "email": "karan@gmail.com", "auth": True, "admin": False}}}
# silly user model
# class User(UserMixin):
#     pass
class User(UserMixin):

    def __init__(self, id):
        self.id = id
        
    def __repr__(self):
        return self.id

# Declaring the app
app = Flask(__name__)
cors = CORS(app, resources={r"/*": {"origins": "*"}})

# flask-login
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

@app.route('/', methods=['GET'])
def index():
    if flask_login.current_user.is_authenticated:
        return flask.redirect(flask.url_for('dashboard'))
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if flask_login.current_user.is_authenticated:
        return flask.redirect(flask.url_for('dashboard'))
    if request.method == 'GET':
        return render_template('register.html')
    email = request.form['email']
    password = request.form['password']
    name = request.form['name']
    cpassword = request.form['cpassword']
    if request.method == 'POST':
        if password == cpassword:
            exist = userschemas.find_one({"email": email})
            if not exist:             
                h1 = hashlib.sha512(str(password).encode()).hexdigest()
                h2 = hashlib.md5(h1.encode()).hexdigest()
                data = {'email': email,"password": h2, "data": {"name": name, "email": email, "auth": True, "admin": False}}
                pre = userschemas.insert_one(data).inserted_id
                if pre:
                    user = User(jwt.encode({"data": {"name": name, "email": email, "auth": True, "admin": False}}, 'asdjnsmfsjjsdf', algorithm='HS256').decode('utf-8'))
                    user.email = email
                    flask_login.login_user(user)
                    return flask.redirect(flask.url_for('dashboard'))
                else:
                    return render_template('register.html') # Database Error
            else:
                return render_template('register.html') # Users Exists
        return render_template('login.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if flask_login.current_user.is_authenticated:
        return flask.redirect(flask.url_for('dashboard'))
    if request.method == 'GET':
        return render_template('login.html')
    email = request.form['email']
    password = request.form['password']
    h1 = hashlib.sha512(str(password).encode()).hexdigest()
    h2 = hashlib.md5(h1.encode()).hexdigest()
    if request.method == 'POST':
        users = userschemas.find_one({"email": email})
        if h2 == users["password"]:
            if users["data"]["auth"]:
                user = User(jwt.encode({"data": users["data"]}, 'asdjnsmfsjjsdf', algorithm='HS256').decode('utf-8'))
                user.email = email
                flask_login.login_user(user)
                return flask.redirect(flask.url_for('dashboard'))
            else:
                return render_template('login.html')# Not authorised        
        return render_template('login.html')


@app.route('/dashboard', methods=['GET', 'POST'])
@flask_login.login_required
def dashboard():
    data = jwt.decode(flask_login.current_user.id, 'asdjnsmfsjjsdf', algorithms=['HS256'])
    if data["data"]["admin"] == True:
        return flask.redirect(flask.url_for('users'))
    email = data["data"]["email"]
    reports = list(reportschemas.find({"email": email}).sort("timestamp", -1))
    if not reports:
        reports.append({"type": "No Reports", "view": "#"})
    return render_template('dashboard.html', reports=reports)


@app.route('/report/<id>', methods=['GET'])
@flask_login.login_required
def report(id):
    id = bson.ObjectId(id)
    report = reportschemas.find_one({"_id": id})
    return render_template('report.html', report=report)


@app.route('/users', methods=['GET', 'POST', 'DELETE'])
@flask_login.login_required
def users():
    data = jwt.decode(flask_login.current_user.id, 'asdjnsmfsjjsdf', algorithms=['HS256'])
    if data["data"]["admin"] == True:
        if request.method == 'GET':
            users = userschemas.find({"data.admin": False})
            return render_template('users.html', users=users)
        
        email = request.form['email']
        if request.method == 'POST':
            myuser = userschemas.find_one({"email": email})
            auth = not myuser["data"]["auth"]
            post = userschemas.update({'_id':myuser["_id"]},{"$set": {"data.auth": auth}})
            return flask.redirect(flask.url_for('users'))
        if request.method == 'DELETE':
            post = userschemas.delete_one({"email": email})
            return flask.redirect(flask.url_for('users'))
    return flask.redirect(flask.url_for('dashboard'))


@app.route('/reports/<email>', methods=['GET', 'POST'])
@flask_login.login_required
def reports(email):
    data = jwt.decode(flask_login.current_user.id, 'asdjnsmfsjjsdf', algorithms=['HS256'])
    if data["data"]["admin"] == True:
        if request.method == 'GET':
            reports = list(reportschemas.find({"email": email}))
            print(reports)
            return render_template('user_reports.html', reports=reports, email=email)
        # data = request.get_json() 
        report_type = request.form['report_type']
        result = request.form['result']
        if request.method == 'POST':
            data = {"email": email, "report_type": report_type, "result": result}
            post = reportschemas.insert_one(data).inserted_id
            return flask.redirect(flask.url_for('users'))
    return flask.redirect(flask.url_for('dashboard'))

# somewhere to logout
@app.route("/logout")
@flask_login.login_required
def logout():
    flask_login.logout_user()
    return flask.redirect(flask.url_for('login'))


# handle login failed
@app.errorhandler(401)
def page_not_found(e):
    return flask.redirect(flask.url_for('login'))


# callback to reload the user object        
@login_manager.user_loader
def load_user(userid):
    return User(userid)


if __name__ == "__main__":
    app.secret_key = 'fghjnbbhkjghjkm hjkasdkjhasdllfakjaid23y937ryhsfjlabsf'
    app.config['SESSION_TYPE'] = 'filesystem'
    port = int(os.environ.get("PORT", 13000))
    app.run(host='0.0.0.0', port=port,threaded = True, debug=True)