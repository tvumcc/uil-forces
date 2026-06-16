import flask
import flask_login
from werkzeug.security import generate_password_hash, check_password_hash
import sqlalchemy

from main import app
from src.backend.orm import *
from src.backend.utils import log, user_required, admin_required

@app.route("/api/login", methods=["GET", "POST"])
def login():
    """Logs in the client as an existing user"""

    response = flask.request.get_json()
    username = str(response["username"])
    password = str(response["password"])

    login_success = False
    user = db.session.query(User).filter_by(username=username).first()

    if user is not None and check_password_hash(user.password_hash, password):
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
        password_hash=generate_password_hash(password),
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
@user_required
def user():
    """Returns JSON data for the currently logged in user"""

    return {"user": flask_login.current_user.shallow_serialize()}

@app.route("/api/user/<id>/problems")
@user_required
def user_problems(id):
    """Returns how many unique problems the specified user has solved"""

    user = db.session.get(User, id)
    if not user:
        return flask.abort(404, description="User does not exist")

    return {
        "user": user.shallow_serialize(),
        "problemsSolved": user.num_problems_solved()
    }

@app.route("/api/users/leaderboard")
@user_required
def users_leaderboard():
    """Returns the top 10 users ranked by number of unique problems solved"""

    users = sorted(db.session.query(User).all(), key=lambda user: user.num_problems_solved(), reverse=True)[:10]

    return [{
        "user": user.shallow_serialize(),
        "problemsSolved": user.num_problems_solved()
    } for user in users]



# Admin API



@app.route("/api/admin/users")
@admin_required
def admin_users():
    """Returns a list of all users"""

    return {"users": [user.serialize() for user in db.session.query(User).all()]}

@app.route("/api/admin/add/user", methods=["POST"])
@admin_required
def admin_add_user():
    """Adds a new user to the database given its username, password, and admin status"""

    request = flask.request.get_json()

    username = request["username"]
    password = request["password"] 
    is_admin = request["isAdmin"]

    db.session.add(User(
        username=username,
        password_hash=generate_password_hash(password),
        is_admin=is_admin
    ))
    db.session.commit()

    return f"Successfully added user '{username}'"