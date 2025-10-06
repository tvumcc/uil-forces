import flask
import flask_login
from sqlalchemy import select 

from main import app
from src.backend.orm import *

@app.route("/api/login", methods=["GET", "POST"])
def login():
    response = flask.request.get_json()
    username = str(response["username"])
    passphrase = str(response["password"])

    user = db.session.execute(select(User).filter_by(username=username)).scalar_one()

    login_success = False

    if user.passphrase == passphrase:
        flask_login.login_user(db.session.get(User, user.id))
        login_success = True

    return {
        "redirect": flask.url_for("index_page"),
        "login_success": login_success
    }

@app.route("/api/logout")
def logout():
    flask_login.logout_user()
    return {
        "redirect": "/login"
    }

@app.route("/api/register", methods=["POST"])
def register():
    response = flask.request.get_json()
    username = str(response["username"])
    passphrase = str(response["password"])

    if db.session.execute(select(User).filter_by(username=username)).first() is not None:
        return flask.Response(status=400, response="Username already exists")

    user = User(
        username=username,
        passphrase=passphrase,
        is_admin=False
    )
    db.session.add(user)
    db.session.commit()

    flask_login.login_user(db.session.get(User, user.id))

    return {
        "redirect": flask.url_for("index_page"),
        "login_success": True
    }

@app.route("/api/user")
@flask_login.login_required
def user():
    return flask_login.current_user.shallow_serialize()

@app.route("/api/admin/users")
@flask_login.login_required
def admin_users():
    if not flask_login.current_user.is_admin:
        return flask.abort(400)

    return {"users": [user.serialize() for user in db.session.query(User).all()]}

@app.route("/api/admin/add/user", methods=["POST"])
@flask_login.login_required
def admin_add_user():
    if not flask_login.current_user.is_admin:
        return flask.abort(400)

    request = flask.request.get_json()

    username = request["username"]
    password = request["password"] 
    is_admin = request["is_admin"]

    db.session.add(User(
        username=username,
        passphrase=password,
        is_admin=is_admin
    ))
    db.session.commit()

    return flask.Response(status=200)