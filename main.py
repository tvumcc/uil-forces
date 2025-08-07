import flask
import flask_login
import sqlalchemy
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, select
from src.backend.orm import *

import datetime

app = flask.Flask(__name__, static_folder="./dist", static_url_path="")
app.secret_key = "dklsjsfkbjsfgfsgjlk"
engine = create_engine("sqlite:///main.db")
Base.metadata.create_all(engine)
session: Session = sqlalchemy.orm.Session(engine)

login_manager = flask_login.LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login_page"

@login_manager.user_loader
def load_user(id):
    return session.get(User, id)

@app.route("/")
@flask_login.login_required
def index_page():
    return flask.send_from_directory(app.static_folder, "src/frontend/html/home.html")

@app.route("/login")
def login_page():
    return flask.send_from_directory(app.static_folder, "src/frontend/html/login.html")

@app.route("/contest")
@flask_login.login_required
def contest_page():
    return flask.send_from_directory(app.static_folder, "src/frontend/html/contest.html")

@app.route("/contests")
@flask_login.login_required
def contest_list_page():
    return flask.send_from_directory(app.static_folder, "src/frontend/html/contest_list.html")

@app.route("/practice")
@flask_login.login_required
def practice_page():
    return flask.send_from_directory(app.static_folder, "src/frontend/html/practice.html")

@app.route("/api/login", methods=["GET", "POST"])
def login():
    response = flask.request.get_json()
    username = str(response["username"])
    passphrase = str(response["password"])

    user = session.execute(select(User).filter_by(username=username)).scalar_one()

    login_success = False

    if not user.is_admin and user.passphrase == passphrase:
        flask_login.login_user(session.get(User, user.id))
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

@app.route("/api/contests")
@flask_login.login_required
def contests():
    contests = session.query(Contest).all()
    print(contests)
    out = {
        "upcoming": [],
        "ongoing": [],
        "past": []
    }

    for contest in contests:
        contest_json = {
            "name": contest.name,
            "id": contest.id,
            "problem_set": contest.problem_set.name,
            "start_time": contest.start_time,
            "end_time": contest.end_time
        }

        if contest.past():
            out["past"].append(contest_json)
        elif contest.ongoing():
            out["ongoing"].append(contest_json)
        elif contest.upcoming():
            out["upcoming"].append(contest_json)

    print(out)

    return out

@app.route("/api/contest/<id>")
@flask_login.login_required
def contest(id):
    contest = session.get(Contest, id)
    submissions = []
    if contest.past(): 
        submissions = contest.submissions
    else: 
        submissions = session.query(Submission).filter_by(user=flask_login.current_user, contest=contest).all()

    return {
        "name": contest.name,
        "id": contest.id,
        "problem_set": contest.problem_set.name,
        "start_time": contest.start_time,
        "end_time": contest.end_time,
        "submissions": [submission.shallow_serialize() for submission in submissions]
    }

@app.route("/api/contest/submissions/<id>")
@flask_login.login_required
def contest_submissions(id):
    contest: Contest = session.get(Contest, id)



if __name__ == "__main__":
    app.run(debug=True, port=5173)