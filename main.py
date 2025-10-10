import flask
import flask_login
import sqlalchemy

import os

from src.backend.orm import *
from src.backend.judge import *

app = flask.Flask(__name__, static_folder="./dist", static_url_path="")
app.secret_key = open("secret.txt", "r").read().strip()
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.abspath("main.db")}"
db.init_app(app)

from src.backend.pages import *
from src.backend.api.user import *
from src.backend.api.problem import *
from src.backend.api.contest import *
from src.backend.api.pset import *
from src.backend.api.submission import *
from src.backend.api.settings import *

with app.app_context():
    db.create_all()

login_manager = flask_login.LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login_page"

@login_manager.user_loader
def load_user(id):
    return db.session.get(User, id)

if __name__ == "__main__":
    app.run(debug=False, port=5173)