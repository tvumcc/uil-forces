import flask
import flask_login
from sqlalchemy import create_engine, select
from src.backend.orm import *
from urllib.parse import urlparse

app = flask.Flask(__name__, static_folder="./dist", static_url_path="")
app.secret_key = "dklsjsfkbjsfgfsgjlk"
engine = create_engine("sqlite:///main.db", echo=True)
Base.metadata.create_all(engine)
session = sqlalchemy.orm.Session(engine)

login_manager = flask_login.LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login_page"

@login_manager.user_loader
def load_user(id):
    return session.get(User, id)

@app.route("/")
def index():
    return flask.send_from_directory(app.static_folder, "src/frontend/html/home.html")

@app.route("/login")
def login_page():
    return flask.send_from_directory(app.static_folder, "src/frontend/html/login.html")

@app.route("/api/top")
def top():
    return {
        "data": "blahaj"
    }

@app.route("/api/user")
@flask_login.login_required
def get_user():
    return {
        "username": "huh",
        "user": f"{flask_login.current_user.username}"
    }

@app.route("/api/login", methods=["GET", "POST"])
def login():
    response = flask.request.get_json()
    username = str(response["username"])
    passphrase = str(response["password"])
    print(username)
    print(passphrase)

    user = session.execute(select(User).filter_by(username=username)).scalar_one()

    login_success = False

    if not user.is_admin and user.passphrase == passphrase:
        flask_login.login_user(session.get(User, user.id))
        login_success = True

    return {
        "redirect": flask.url_for("index"),
        "login_success": login_success
    }


@app.route("/api/logout")
def logout():
    flask_login.logout_user()
    return flask.redirect(flask.url_for("login_page"))

if __name__ == "__main__":
    app.run(debug=True, port=5173)