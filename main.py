import flask
import flask_login
from flask_apscheduler import APScheduler
import sqlalchemy
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, select, desc
from src.backend.orm import *
import pypdf

import datetime
import os
import threading
from src.backend.judge import *

app = flask.Flask(__name__, static_folder="./dist", static_url_path="")
app.secret_key = open("secret.txt", "r").read().strip()
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.abspath("main.db")}"
db.init_app(app)

with app.app_context():
    db.create_all()

login_manager = flask_login.LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login_page"

@login_manager.user_loader
def load_user(id):
    return db.session.get(User, id)

@app.route("/")
@flask_login.login_required
def index_page():
    return flask.send_from_directory(app.static_folder, "src/frontend/html/home.html")

@app.route("/login")
def login_page():
    return flask.send_from_directory(app.static_folder, "src/frontend/html/login.html")

@app.route("/register")
def register_page():
    return flask.send_from_directory(app.static_folder, "src/frontend/html/register.html")

@app.route("/contest")
@flask_login.login_required
def contest_page():
    return flask.send_from_directory(app.static_folder, "src/frontend/html/contest.html")

@app.route("/contests")
@flask_login.login_required
def contest_list_page():
    return flask.send_from_directory(app.static_folder, "src/frontend/html/contestList.html")

@app.route("/submission")
@flask_login.login_required
def submission_page():
    return flask.send_from_directory(app.static_folder, "src/frontend/html/submission.html")

@app.route("/pset")
@flask_login.login_required
def pset_page():
    return flask.send_from_directory(app.static_folder, "src/frontend/html/problemSet.html")

@app.route("/psets")
@flask_login.login_required
def pset_list_page():
    return flask.send_from_directory(app.static_folder, "src/frontend/html/problemSetList.html")

@app.route("/admin/users")
@flask_login.login_required
def admin_user_list_page():
    if not flask_login.current_user.is_admin:
        return flask.abort(400)
    return flask.send_from_directory(app.static_folder, "src/frontend/html/adminUserList.html")

@app.route("/admin/contests")
@flask_login.login_required
def admin_contest_list_page():
    if not flask_login.current_user.is_admin:
        return flask.abort(400)
    return flask.send_from_directory(app.static_folder, "src/frontend/html/adminContestList.html")

@app.route("/admin/contest")
@flask_login.login_required
def admin_contest_page():
    if not flask_login.current_user.is_admin:
        return flask.abort(400)
    return flask.send_from_directory(app.static_folder, "src/frontend/html/adminContest.html")


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

@app.route("/api/contests")
@flask_login.login_required
def contests():
    contests = db.session.query(Contest).all()
    out = {
        "upcoming": [],
        "ongoing": [],
        "past": []
    }

    for contest in contests:
        contest_json = contest.shallow_serialize() 
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
    contest = db.session.get(Contest, id)
    contest_profile = db.session.query(ContestProfile).filter_by(user=flask_login.current_user, contest=contest).first()
    if not contest_profile:
        contest_profile = ContestProfile(user=flask_login.current_user, contest=contest)
        db.session.add(contest_profile)
        db.session.commit()

    submissions = []
    if contest.past(): 
        for profile in contest.contest_profiles:
            submissions += profile.submissions
    else: 
        submissions = db.session.query(Submission).filter_by(contest_profile=contest_profile).order_by(desc(Submission.submit_time)).all()

    return contest.serialize() | {
        "submissions": [submission.shallow_serialize() for submission in submissions]
    }

@app.route("/api/contest/submit", methods=["POST"])
@flask_login.login_required
def submit_contest_problem():
    response = flask.request.get_json()
    problem = db.session.get(Problem, response["problem_id"])
    contest = db.session.get(Contest, response["contest_id"])
    language = response["language"]
    if not problem:
        return {"message": "invalid problem id"}
    if not contest:
        return {"message": "invalid contest id"}
    contest_profile = db.session.query(ContestProfile).filter_by(user=flask_login.current_user, contest=contest).first()
    if not contest_profile:
        contest_profile = ContestProfile(user=flask_login.current_user, contest=contest)
        db.session.add(contest_profile)
        db.session.commit()

    submission = Submission(
        problem=problem,
        contest_profile=contest_profile,
        user=flask_login.current_user,

        status=Status.Pending.value,
        code=response["code"],
        submit_time=datetime.datetime.now(),
        language=language
    )
    db.session.add(submission)
    db.session.commit()

    thread = threading.Thread(target=assign_status, args=[submission.id])
    thread.daemon = True
    thread.start()

    submissions = db.session.query(Submission).filter_by(contest_profile=contest_profile).order_by(desc(Submission.submit_time)).all()
    return {
        "estimated_wait" : 15,
        "submissions": [submission.shallow_serialize() for submission in submissions]
    }

@app.route("/api/pset/<id>")
@flask_login.login_required
def pset(id):
    pset = db.session.get(ProblemSet, id)
    submissions = []
    for problem in pset.problems:
        submissions += db.session.query(Submission).filter_by(user=flask_login.current_user, problem=problem).order_by(desc(Submission.submit_time)).all()
    submissions.sort(key=lambda submission: submission.submit_time, reverse=True)

    return pset.serialize() | {
        "submissions": [submission.shallow_serialize() for submission in submissions]
    }

@app.route("/api/psets")
@flask_login.login_required
def psets():
    psets = db.session.query(ProblemSet).all()
    return {
        "psets": [pset.shallow_serialize() for pset in psets]
    }

@app.route("/api/pset/submit", methods=["POST"])
def submit_pset_problem():
    response = flask.request.get_json()
    problem = db.session.get(Problem, response["problem_id"])
    language = response["language"]
    if not problem:
        return {"message": "invalid problem id"}

    submission = Submission(
        problem=problem,
        user=flask_login.current_user,

        status=Status.Pending.value,
        code=response["code"],
        submit_time=datetime.datetime.now(),
        language=language
    )
    db.session.add(submission)
    db.session.commit()

    thread = threading.Thread(target=assign_status, args=[submission.id])
    thread.daemon = True
    thread.start()


    submissions = []
    for prob in problem.problem_set.problems:
        submissions += db.session.query(Submission).filter_by(user=flask_login.current_user, problem=prob).order_by(desc(Submission.submit_time)).all()
    submissions.sort(key=lambda submission: submission.submit_time, reverse=True)

    return {
        "estimated_wait" : 15,
        "submissions": [submission.shallow_serialize() for submission in submissions]
    }

@app.route("/api/problem/<id>/pdf")
@flask_login.login_required
def problem_pdf(id):
    problem = db.session.get(Problem, id)
    if not problem: flask.abort(404)
    pdf_path = problem.problem_set.pdf_path
    pages = [int(x)-1 for x in problem.pages.split()]

    if not os.path.exists(pdf_path) or len(pages) == 0:
        flask.abort(404)

    reader = pypdf.PdfReader(pdf_path)
    writer = pypdf.PdfWriter()

    for page in pages:
        writer.add_page(reader.pages[page])

    temp_pdf = "pdfs/problem.pdf"
    with open(temp_pdf, "wb") as output_pdf:
        writer.write(output_pdf)
    response = flask.send_from_directory(app.root_path, temp_pdf)
    os.remove(temp_pdf)
    return response

@app.route("/api/submission/<id>")
@flask_login.login_required
def submission(id):
    submission = db.session.get(Submission, id)
    user = submission.user
    
    contest_profile = submission.contest_profile
    if contest_profile and not contest_profile.contest.past() and not user.is_admin and not user.id == flask_login.current_user.id:
        return {"message": "Submission cannot be viewed at this time"}

    return submission.serialize()

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

@app.route("/api/admin/contests")
@flask_login.login_required
def admin_contests():
    if not flask_login.current_user.is_admin:
        return flask.abort(400)
    return {"contests": [contest.shallow_serialize() for contest in db.session.query(Contest).all()]}

@app.route("/api/admin/contest/<id>")
@flask_login.login_required
def admin_contest(id):
    if not flask_login.current_user.is_admin:
        return flask.abort(400)
    contest = db.session.get(Contest, id)
    return {"contest": contest.serialize()}

@app.route("/api/admin/contest/<id>/add/problem", methods=["POST"])
@flask_login.login_required
def admin_contest_add_problem(id):
    if not flask_login.current_user.is_admin:
        return flask.abort(400)

    request = flask.request.get_json()
    pset_name = request["pset_name"]
    problem_name = request["problem_name"]

    contest = db.session.get(Contest, id)
    problem_set = db.session.query(ProblemSet).filter_by(name=pset_name).first()
    if problem_set is None:
        return flask.abort(400)

    problem = db.session.query(Problem).filter_by(problem_set=problem_set, name=problem_name).first()

    if problem is None:
        return flask.abort(400)

    for p in contest.problems:
        if p.id == problem.id:
            return flask.abort(400)

    contest.problems.append(problem)
    db.session.add(contest)
    db.session.commit()

    return flask.Response(status=200)

@app.route("/api/admin/contest/<id>/add/pset", methods=["POST"])
@flask_login.login_required
def admin_contest_add_pset(id):
    if not flask_login.current_user.is_admin:
        return flask.abort(400)

    request = flask.request.get_json()
    pset_name = request["pset_name"]

    contest = db.session.get(Contest, id)
    problem_set = db.session.query(ProblemSet).filter_by(name=pset_name).first()
    if problem_set is None:
        return flask.abort(400)

    for problem in problem_set.problems:
        if not problem in contest.problems:
            contest.problems.append(problem) 

    db.session.add(contest)
    db.session.commit()

    return flask.Response(status=200)

@app.route("/api/admin/contest/unlinkproblem", methods=["POST"])
@flask_login.login_required
def admin_contest_unlink_problem():
    if not flask_login.current_user.is_admin:
        return flask.abort(400)

    request = flask.request.get_json()
    contest_id = request["contest_id"]
    problem_id = request["problem_id"]

    contest: Contest = db.session.get(Contest, contest_id)
    problem = db.session.get(Problem, problem_id)

    if contest is None:
        return flask.abort(404)
    if problem is None:
        return flask.abort(404)

    try:
        contest.problems.remove(problem)
        db.session.add(contest)
        db.session.commit()
    except ValueError:
        return flask.abort(400)

    return flask.Response(status=200)

@app.route("/api/admin/update/contest", methods=["POST"])
@flask_login.login_required
def admin_update_contest():
    if not flask_login.current_user.is_admin:
        return flask.abort(400)
    
    request = flask.request.get_json()
    id = request["id"]
    name = request["name"]
    start_time = request["start_time"]
    end_time = request["end_time"]

    contest = db.session.get(Contest, id)
    contest.name = name
    contest.start_time = datetime.datetime.fromisoformat(start_time)
    contest.end_time = datetime.datetime.fromisoformat(end_time)

    db.session.add(contest)
    db.session.commit()

    return flask.Response(status=200)

@app.route("/api/admin/add/contest", methods=["POST"])
@flask_login.login_required
def admin_add_contest():
    if not flask_login.current_user.is_admin:
        return flask.abort(400)
    
    request = flask.request.get_json()

    name = request["name"]
    start_time = datetime.datetime.fromisoformat(request["start_time"])
    end_time = datetime.datetime.fromisoformat(request["end_time"])

    db.session.add(Contest(
        name=name,
        start_time=start_time,
        end_time=end_time
    ))
    db.session.commit()

    return flask.Response(status=200)

if __name__ == "__main__":
    # scheduler = APScheduler()
    # scheduler.add_job(func=grade_pending_submissions, args=[db.session], id="grader", trigger="interval", seconds=3)
    # scheduler.start()
    app.run(debug=False, port=5173)