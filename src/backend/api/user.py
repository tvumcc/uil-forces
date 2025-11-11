import flask
import flask_login

from main import app
from src.backend.orm import *
from src.backend.log import log

@app.route("/api/login", methods=["GET", "POST"])
def login():
    """Logs in the client as an existing user"""

    response = flask.request.get_json()
    username = str(response["username"])
    password = str(response["password"])

    login_success = False
    user = db.session.query(User).filter_by(username=username).first()

    if user is not None and user.password == password:
        flask_login.login_user(db.session.get(User, user.id))
        login_success = True
        log.info(f"User '{user.username}' logged in")
    else:
        return "Login failed; invalid credentials", 400

    return {
        "redirect": flask.url_for("index_page"),
        "loginSuccess": login_success
    }

@app.route("/api/logout")
def logout():
    """Logs the client out"""

    flask_login.logout_user()
    return {"redirect": "/login"}

@app.route("/api/register", methods=["POST"])
def register():
    """Creates a new user account and logs the client in as that user"""

    request = flask.request.get_json()
    username = str(request["username"])
    password = str(request["password"])

    if db.session.query(User).filter_by(username=username).first() is not None:
        flask.abort(400, description="Username already exists")

    user = User(
        username=username,
        password=password,
        is_admin=False
    )
    db.session.add(user)
    db.session.commit()

    flask_login.login_user(db.session.get(User, user.id))

    return {
        "redirect": flask.url_for("index_page"),
        "loginSuccess": True
    }

@app.route("/api/user")
@flask_login.login_required
def user():
    """Returns JSON data for the currently logged in user"""

    return {"user": flask_login.current_user.shallow_serialize()}



# Admin API



@app.route("/api/admin/users")
@flask_login.login_required
def admin_users():
    """Returns a list of all users"""

    if not flask_login.current_user.is_admin:
        flask.abort(403)

    return {"users": [user.serialize() for user in db.session.query(User).all()]}

@app.route("/api/admin/add/user", methods=["POST"])
@flask_login.login_required
def admin_add_user():
    """Adds a new user to the database given its username, password, and admin status"""

    if not flask_login.current_user.is_admin:
        flask.abort(400)

    request = flask.request.get_json()

    username = request["username"]
    password = request["password"] 
    is_admin = request["isAdmin"]

    db.session.add(User(
        username=username,
        password=password,
        is_admin=is_admin
    ))
    db.session.commit()

    return f"Successfully added user '{username}'"