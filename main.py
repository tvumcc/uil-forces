import flask
import flask_login
from sqlalchemy import event
from sqlalchemy.engine import Engine
from werkzeug.exceptions import HTTPException

import os, sys

from src.backend.orm import *
from src.backend.setup import *
import setup

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

if hasattr(sys, '_MEIPASS'):
    runtime_dir = os.path.dirname(sys.executable)
else:
    runtime_dir = os.path.abspath(".")

app = flask.Flask(__name__, static_folder=resource_path("./dist"), static_url_path="")

secret_path = os.path.join(runtime_dir, "secret.txt")
try:
    app.secret_key = open(secret_path, "r").read().strip()
except:
    print("No secret key found. In the root directory, create a file named 'secret.txt' containing the secret key.")
    exit()

db_path = os.path.join(runtime_dir, "main.db")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"

db.init_app(app)

from src.backend.pages import *
from src.backend.api.user import *
from src.backend.api.problem import *
from src.backend.api.contest import *
from src.backend.api.pset import *
from src.backend.api.submission import *
from src.backend.api.settings import *

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
    print("UIL Forces")
    print("Possible actions:")
    print("1. Run server")
    print("2. Start server setup")
    print("3. Quit")

    terminating_action = False
    while not terminating_action:
        action = input("Please specify an action: ")
        if action == "1":
            if not os.path.exists("main.db"):
                print("A database does not yet exist for this instance. Select '2. Start server setup' to create it.")
            else:
                app.run(debug=False, host="0.0.0.0", port=5173)
                terminating_action = True
        elif action == "2":
            setup.setup()
            print("Successfully completed setup.")
        elif action == "3":
            terminating_action = True
        else:
            print("Invalid action.")