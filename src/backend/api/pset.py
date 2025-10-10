import flask
import flask_login

import threading
import datetime
from datetime import timezone

from main import app
from src.backend.orm import *
from src.backend.judge import Status, assign_status
from sqlalchemy import desc

@app.route("/api/pset/<id>")
@flask_login.login_required
def pset(id):
    settings = db.session.query(Settings).filter_by(key="practice_site").first()
    pset = db.session.get(ProblemSet, id)

    if settings and settings.value == "true" and pset and not pset.hide:
        submissions = []
        for problem in pset.problems:
            submissions += db.session.query(Submission).filter_by(user=flask_login.current_user, problem=problem).order_by(desc(Submission.submit_time)).all()
        submissions.sort(key=lambda submission: submission.submit_time, reverse=True)

        return pset.serialize() | {
            "submissions": [submission.shallow_serialize() for submission in submissions]
        }
    else:
        return {"hide": True}

@app.route("/api/psets")
@flask_login.login_required
def psets():
    settings = db.session.query(Settings).filter_by(key="practice_site").first()
    if settings and settings.value == "true":
        psets = db.session.query(ProblemSet).all()
        return {
            "hide": False,
            "psets": [pset.shallow_serialize() for pset in psets if not pset.hide]
        }
    else:
        return {"hide": True}

@app.route("/api/pset/submit", methods=["POST"])
@flask_login.login_required
def submit_pset_problem():
    settings = db.session.query(Settings).filter_by(key="practice_site").first()
    problem = db.session.get(Problem, response["problem_id"])
    pset = problem.problem_set if problem else None

    if settings and settings.value == "true" and pset and not pset.hide:
        response = flask.request.get_json()
        language = response["language"]
        if not problem:
            return {"message": "invalid problem id"}

        submission = Submission(
            problem=problem,
            user=flask_login.current_user,

            status=Status.Pending.value,
            code=response["code"],
            submit_time=datetime.datetime.now(timezone.utc),
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
    else:
        return flask.Response(status=400)

@app.route("/api/admin/pset/<id>")
@flask_login.login_required
def admin_pset(id):
    if not flask_login.current_user.is_admin:
        return flask.abort(400)
    pset = db.session.get(ProblemSet, id)
    return {"pset": pset.serialize()}

@app.route("/api/admin/update/pset", methods=["POST"])
@flask_login.login_required
def admin_update_pset():
    if not flask_login.current_user.is_admin:
        return flask.abort(400)
    
    request = flask.request.get_json()
    id = request["id"]
    name = request["name"]
    hide = request["hide"]

    pset = db.session.get(ProblemSet, id)
    pset.name = name
    pset.hide = hide

    db.session.add(pset)
    db.session.commit()

    return flask.Response(status=200)