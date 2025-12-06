import flask
import flask_login
from sqlalchemy import event
from sqlalchemy.engine import Engine
from werkzeug.exceptions import HTTPException

import os

from src.backend.orm import *
from src.backend.judge import *

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

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

if not os.path.exists("main.db"):
    print("Initialize the database first by running setup.py")

login_manager = flask_login.LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login_page"

@login_manager.user_loader
def load_user(id):
    return db.session.get(User, id)

@app.errorhandler(HTTPException)
def error_handler(e):
    return {
        "error": e.name, 
        "description": e.description
    }, e.code

if __name__ == "__main__":
    app.run(debug=False, port=5173)