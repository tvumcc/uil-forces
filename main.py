import flask
import flask_login
from sqlalchemy import create_engine
from src.orm import *

app = flask.Flask(__name__)
app.secret_key = "dklsjsfkbjsfgfsgjlk"
engine = create_engine("sqlite:///main.db", echo=True)
Base.metadata.create_all(engine)
session = sqlalchemy.orm.Session(engine)

login_manager = flask_login.LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(id):
    return session.get(User, id)

@app.route("/")
def index():
    return "This is the index. Hi!"

@app.route("/user")
@flask_login.login_required
def get_user():
    return {
        "username": "huh",
        "user": f"{flask_login.current_user.username}"
    }

@app.route("/login/<id>")
def login(id):
    flask_login.login_user(session.get(User, id))
    return flask.redirect(flask.url_for("index"))

@app.route("/logout")
def logout():
    flask_login.logout_user()
    return flask.redirect(flask.url_for("index"))