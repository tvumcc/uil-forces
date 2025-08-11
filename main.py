import flask
import flask_login
from flask_apscheduler import APScheduler
import sqlalchemy
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, select
from src.backend.orm import *

import datetime
from src.backend.judge import *

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
    return session.query(User).filter_by(id=id).one()

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

@app.route("/submission")
@flask_login.login_required
def submission_page():
    return flask.send_from_directory(app.static_folder, "src/frontend/html/submission.html")

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


    return out

@app.route("/api/contest/<id>")
@flask_login.login_required
def contest(id):
    contest = session.get(Contest, id)
    contest_profile = session.query(ContestProfile).filter_by(user=flask_login.current_user, contest=contest).first()
    if not contest_profile:
        contest_profile = ContestProfile(user=flask_login.current_user, contest=contest)
        session.add(contest_profile)
        session.commit()

    submissions = []
    if contest.past(): 
        for profile in contest.contest_profiles:
            submissions += profile.submissions
    else: 
        submissions = session.query(Submission).filter_by(contest_profile=contest_profile).all()

    return contest.serialize() | {
        "submissions": [submission.shallow_serialize() for submission in submissions]
    }

@app.route("/api/contest/submit", methods=["POST"])
@flask_login.login_required
def submit_contest_problem():
    response = flask.request.get_json()
    problem = session.get(Problem, response["problem_id"])
    contest = session.get(Contest, response["contest_id"])
    if not problem:
        return {"message": "invalid problem id"}
    if not contest:
        return {"message": "invalid contest id"}
    contest_profile = session.query(ContestProfile).filter_by(user=flask_login.current_user, contest=contest).first()
    if not contest_profile:
        contest_profile = ContestProfile(user=flask_login.current_user, contest=contest)
        session.add(contest_profile)
        session.commit()

    submission = Submission(
        problem=problem,
        contest_profile=contest_profile,
        user=flask_login.current_user,

        status=Status.Pending.value,
        filename=response["filename"],
        code=response["code"],
        submit_time=datetime.datetime.now()
    )
    session.add(submission)
    session.commit()

    status, output = grade_java_submission_jdk(submission)
    submission.status = status.value
    submission.output = output

    session.commit()
    return {}

@app.route("/api/submission/<id>")
@flask_login.login_required
def submission(id):
    submission = session.get(Submission, id)
    user = submission.user
    
    contest_profile = submission.contest_profile
    if contest_profile and not contest_profile.contest.past() and not user.is_admin and not user.id == flask_login.current_user.id:
        return {"message": "Submission cannot be viewed at this time"}

    return submission.serialize()

@app.route("/api/user")
@flask_login.login_required
def user():
    return flask_login.current_user.shallow_serialize()


if __name__ == "__main__":
    # scheduler = APScheduler()
    # scheduler.add_job(func=grade_pending_submissions, args=[session], id="grader", trigger="interval", seconds=3)
    # scheduler.start()
    app.run(debug=False, port=5173)