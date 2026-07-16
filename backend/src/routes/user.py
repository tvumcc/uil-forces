import flask
import flask_login
from werkzeug.security import generate_password_hash, check_password_hash

from src.app import app
from src.models.orm import *
from src.utils import log, admin_required, valid_username

@app.route("/api/login", methods=["POST"])
def login():
    """Logs in the client as an existing user"""

    response = flask.request.get_json()
    username = str(response["username"])
    password = str(response["password"])

    user = db.session.query(User).filter_by(username=username).first()

    if user is None or not check_password_hash(user.password_hash, password):
        return {"error": "invalid_credentials"}, 400

    flask_login.login_user(user)
    log.info(f"User '{user.username}' logged in")

    return "", 204

@app.route("/api/logout")
def logout():
    """Logs the client out"""

    flask_login.logout_user()

    return "", 204

@app.route("/api/register", methods=["POST"])
def register():
    """Creates a new user account and logs the client in as that user"""

    request = flask.request.get_json()
    username = str(request["username"])
    password = str(request["password"])

    if not valid_username(username):
        return {"error": "invalid_username"}, 400
    if db.session.query(User).filter_by(username=username).first() is not None:
        return {"error": "user_exists"}, 409

    user = User(
        username=username,
        password_hash=generate_password_hash(password),
        is_admin=False
    )
    db.session.add(user)
    db.session.commit()

    flask_login.login_user(db.session.get(User, user.id))

    return "", 201

@app.route("/api/user")
@flask_login.login_required
def user():
    """Returns JSON data for the currently logged in user"""

    return {"user": flask_login.current_user.shallow_serialize()}

@app.route("/api/users/leaderboard")
@flask_login.login_required
def users_leaderboard():
    """Returns the top 10 users ranked by number of unique problems solved"""

    ranked = sorted(
        ((user, user.num_problems_solved()) for user in db.session.query(User).all()),
        key=lambda entry: entry[1],
        reverse=True
    )[:10]

    return [{"user": user.shallow_serialize(), "problemsSolved": count} for user, count in ranked]



# Admin API



@app.route("/api/admin/users")
@admin_required
def admin_users():
    """Returns a list of all users"""

    return {"users": [user.shallow_serialize() for user in db.session.query(User).all()]}

@app.route("/api/admin/add/user", methods=["POST"])
@admin_required
def admin_add_user():
    """Adds a new user to the database given its username, password, and admin status"""

    data = flask.request.get_json()

    username = data["username"]
    password = data["password"] 
    is_admin = data["isAdmin"]

    if not valid_username(username):
        return {"error": "invalid_username"}, 400
    if db.session.query(User).filter_by(username=username).first() is not None:
        return {"error": "user_exists"}, 409

    user = User(
        username=username,
        password_hash=generate_password_hash(password),
        is_admin=is_admin
    )
    db.session.add(user)
    db.session.commit()

    return "", 201