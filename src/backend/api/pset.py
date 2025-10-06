import flask
import flask_login

import threading
import datetime

from main import app
from src.backend.orm import *
from src.backend.judge import Status, assign_status
from sqlalchemy import create_engine, select, desc

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

    thread = threading.Thread(target=assign_status, args=[submission.id, None])
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
