import flask
import flask_login
import flask_wtf
from sqlalchemy import event
from sqlalchemy.engine import Engine
from werkzeug.exceptions import HTTPException

import os, sys, logging
from logging.handlers import TimedRotatingFileHandler

from src.models.orm import *
from src.setup import *

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

logs_dir = os.path.join(runtime_dir, "logs")
os.makedirs(logs_dir, exist_ok=True)
log_path = os.path.join(logs_dir, "app.log")

formatter = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y/%m/%d %H:%M:%S",
)

file_handler = TimedRotatingFileHandler(
    log_path,
    when="midnight",
    interval=1,
    backupCount=50, # keep 50 days of contest history
    encoding="utf-8",
)
file_handler.setFormatter(formatter)

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

logging.basicConfig(
    level=logging.INFO,
    handlers=[console_handler, file_handler],
)

DIST_DIR = resource_path("dist")

app = flask.Flask(__name__, static_folder=None)

secret_path = os.path.join(runtime_dir, "secret.txt")
try:
    app.secret_key = open(secret_path, "r").read().strip()
except:
    print("No secret key found. In the root directory, create a file named 'secret.txt' containing the secret key.")
    exit()

db_path = os.path.join(runtime_dir, "main.db")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"

db.init_app(app)

from src.routes.user import *
from src.routes.problem import *
from src.routes.contest import *
from src.routes.pset import *
from src.routes.submission import *
from src.routes.settings import *

login_manager = flask_login.LoginManager()
login_manager.init_app(app)

@login_manager.unauthorized_handler
def unauthorized():
    return flask.jsonify({"error": "unauthorized"}), 401

@login_manager.user_loader
def load_user(id):
    return db.session.get(User, id)

@app.errorhandler(HTTPException)
def error_handler(e):
    return {
        "error": e.name, 
        "description": e.description
    }, e.code

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def spa_shell(path):
    full_path = os.path.join(DIST_DIR, path)
    if path and os.path.isfile(full_path):
        return flask.send_from_directory(DIST_DIR, path)
    return flask.send_from_directory(DIST_DIR, "index.html")

csrf = flask_wtf.CSRFProtect()
csrf.init_app(app)

@app.route("/api/csrf-token", methods=["GET"])
def csrf_token():
    return {"csrfToken": flask_wtf.csrf.generate_csrf()}

@app.errorhandler(flask_wtf.csrf.CSRFError)
def handle_csrf_error(e):
    return {"error": "csrf_invalid", "description": e.description}, 400