import flask
import flask_login
import flask_wtf
from sqlalchemy import event
from sqlalchemy.engine import Engine
from werkzeug.exceptions import HTTPException

import os, sys

from src.models.orm import db
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

DIST_DIR = resource_path("dist")
secret_path = os.path.join(runtime_dir, "secret.txt")
db_path = os.path.join(runtime_dir, "main.db")

login_manager = flask_login.LoginManager()
csrf = flask_wtf.CSRFProtect()
setup_logging(runtime_dir)

def create_app(test_config=None):
    app = flask.Flask(__name__, static_folder=None)

    try:
        app.secret_key = open(secret_path, "r").read().strip()
    except:
        print("No secret key found. In the root directory, create a file named 'secret.txt' containing a secret key and try again.")
        input("Press Enter to close")
        sys.exit()

    app.config.update({
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}"
    })

    if test_config is not None:
        app.config.update(test_config)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    from src.routes.user import bp as user_bp
    from src.routes.problem import bp as problem_bp
    from src.routes.contest import bp as contest_bp
    from src.routes.pset import bp as pset_bp
    from src.routes.submission import bp as submission_bp
    from src.routes.settings import bp as settings_bp

    app.register_blueprint(user_bp)
    app.register_blueprint(problem_bp)
    app.register_blueprint(contest_bp)
    app.register_blueprint(pset_bp)
    app.register_blueprint(submission_bp)
    app.register_blueprint(settings_bp)

    @app.errorhandler(HTTPException)
    def error_handler(e):
        return {
            "error": e.name, 
            "description": e.description
        }, e.code

    @app.route("/api/csrf-token", methods=["GET"])
    def csrf_token():
        return {"csrfToken": flask_wtf.csrf.generate_csrf()}

    @app.errorhandler(flask_wtf.csrf.CSRFError)
    def handle_csrf_error(e):
        return {"error": "csrf_invalid", "description": e.description}, 400

    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def spa_shell(path):
        full_path = os.path.join(DIST_DIR, path)
        if path and os.path.isfile(full_path):
            return flask.send_from_directory(DIST_DIR, path)
        return flask.send_from_directory(DIST_DIR, "index.html")

    return app

app = create_app()

@login_manager.unauthorized_handler
def unauthorized():
    return flask.jsonify({"error": "unauthorized"}), 401

@login_manager.user_loader
def load_user(id):
    return db.session.get(User, id)