import flask
import flask_login

import threading
import datetime
from datetime import timezone
import os
import shutil

from main import app
from src.backend.orm import *
from src.backend.judge import Status, assign_status
from sqlalchemy import desc

def get_user_pset_submissions(pset: ProblemSet):
    """Returns a list of all of the submissions that the currently logged in user has submitted to the specified problem set"""

    submissions = []
    for problem in pset.problems:
        submissions += db.session.query(Submission).filter_by(user=flask_login.current_user, problem=problem).order_by(desc(Submission.submit_time)).all()
    submissions.sort(key=lambda submission: submission.submit_time, reverse=True)
    return submissions

@app.route("/api/pset/<id>")
@flask_login.login_required
def pset(id):
    """Returns JSON data for the queried problem set, provided that it is not hidden or the practice site is disabled"""

    pset = db.session.get(ProblemSet, id)
    if not pset:
        flask.abort(404, description="Problem set does not exist")

    if Settings.practice_site_enabled() and not pset.hide:
        submissions = get_user_pset_submissions(pset)
        return {"pset": pset.serialize() | {"submissions": [submission.shallow_serialize() for submission in submissions]}}
    else:
        return {"pset": {"hide": True}}

@app.route("/api/psets")
@flask_login.login_required
def psets():
    """
    Returns a list of all problem sets that are not hidden. 
    If the practice site is disabled, none are returned and hide is set to true
    """

    if Settings.practice_site_enabled():
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
    """
    Processes a user's request to submit code to a problem in this problem set.
    This will create a new submission on the database and spawn another thread to run and assign a status to it.

    Whether the submission is ran using a local interpreter/compiler or a Docker container is based on the
    site-wide setting 'docker_grading'

    The client will continue to poll every 1 second `estimated_wait` times to check if a new status has been assigned to the submission.
    """

    request = flask.request.get_json()

    problem = db.session.get(Problem, request["problemID"])
    language = request["language"]
    if not problem:
        flask.abort(404, description="Problem does not exist")
    if language not in ["Java", "Python", "C++"]:
        flask.abort(400, description="Invalid language submitted")

    if Settings.practice_site_enabled() and not problem.problem_set.hide:
        submission = Submission(
            problem=problem,
            user=flask_login.current_user,

            status=Status.Pending.value,
            code=request["code"],
            submit_time=datetime.datetime.now(timezone.utc),
            language=language
        )
        db.session.add(submission)
        db.session.commit()

        thread = threading.Thread(target=assign_status, args=[submission, None], kwargs={"docker": Settings.docker_grading_enabled()})
        thread.daemon = True
        thread.start()

        return {
            "estimatedWait" : 15,
            "submissions": [submission.shallow_serialize() for submission in get_user_pset_submissions(problem.problem_set)]
        }
    else:
        return "The practice site or problem set is currently disabled", 403

@app.route("/api/pset/<id>/data")
@flask_login.login_required
def pset_data(id):
    """Returns a .zip file of all of the student data for the problems in this problem set"""

    pset = db.session.get(ProblemSet, id)
    if not pset:
        flask.abort(404, description="Problem set does not exist")

    if Settings.practice_site_enabled() and not pset.hide:
        try:
            dirname = f"pset{pset.id}-student-data"
            os.mkdir(dirname)

            for problem in pset.problems:
                if len(problem.student_input) > 0:
                    with open(os.path.join(dirname, problem.input_file_name), "w") as f:
                        f.write(problem.student_input)

            shutil.make_archive(dirname, "zip", dirname)
            return flask.send_file(f"{dirname}.zip")
        finally:
            try:
                shutil.rmtree(dirname)
                os.remove(f"{dirname}.zip")
            except: pass
    else:
        return "The practice site or problem set is currently disabled", 403



# Admin API



@app.route("/api/admin/psets")
@flask_login.login_required
def admin_psets():
    """Returns a list of all the problem sets currently contained within the database"""

    if not flask_login.current_user.is_admin:
        flask.abort(403)
    return {"psets": [pset.shallow_serialize() for pset in db.session.query(ProblemSet).all()]}

@app.route("/api/admin/pset/<id>")
@flask_login.login_required
def admin_pset(id):
    """Returns the JSON data for the queried problem set"""

    if not flask_login.current_user.is_admin:
        flask.abort(403)
    pset = db.session.get(ProblemSet, id)
    if not pset:
        flask.abort(404, description="Problem set does not exist")
    return {"pset": pset.serialize()}

@app.route("/api/admin/update/pset", methods=["POST"])
@flask_login.login_required
def admin_update_pset():
    """Updates the specified problem set with the provided new values"""

    if not flask_login.current_user.is_admin:
        flask.abort(403)
    
    request = flask.request.get_json()
    id = request["id"]
    name = request["name"]
    hide = request["hide"]

    pset = db.session.get(ProblemSet, id)
    pset.name = name
    pset.hide = hide

    db.session.add(pset)
    db.session.commit()

    return f"Successfully updated pset {id} ({pset.name})"

@app.route("/api/admin/add/pset", methods=["POST"])
@flask_login.login_required
def admin_add_pset():
    """Creates an empty problem set with just a name and adds it to the database"""

    if not flask_login.current_user.is_admin:
        flask.abort(403)
    
    request = flask.request.get_json()

    name = request["name"]

    pset = ProblemSet(name=name)
    db.session.add(pset)
    db.session.commit()

    return f"Created new empty problem set {pset.id} ({pset.name})"

@app.route("/api/admin/pset/add/problem", methods=["POST"])
@flask_login.login_required
def admin_pset_add_problem():
    """Creates an empty problem with just a name and adds it to the specified problem set"""

    if not flask_login.current_user.is_admin:
        flask.abort(403)

    request = flask.request.get_json()

    pset_id = request["psetID"]
    problem_name = request["problemName"]

    pset = db.session.get(ProblemSet, pset_id)
    if not pset:
        flask.abort(404, description="Problem set does not exist")

    problem = Problem(name=problem_name, problem_set=pset)
    db.session.add(problem)
    pset.problems.append(problem)

    db.session.add(pset)
    db.session.commit()

    return f"Created new empty problem {problem.id} ({problem.name})"

@app.route("/api/admin/pset/<id>/pdf")
@flask_login.login_required
def admin_pset_pdf(id):
    """Returns the entire PDF attached to this problem set"""

    if not flask_login.current_user.is_admin:
        flask.abort(403)

    pset = db.session.get(ProblemSet, id)
    if not pset:
        flask.abort(404, description="Problem set does not exist")
    return flask.send_from_directory(app.root_path, pset.pdf_path)

@app.route("/api/admin/pset/<id>/uploadpdf", methods=["POST"])
@flask_login.login_required
def admin_pset_upload_pdf(id):
    """Uploads a new PDF to replace the one currently attached to the specified problem set"""

    if not flask_login.current_user.is_admin:
        flask.abort(403)

    file = flask.request.files["pdf"]
    pset =  db.session.get(ProblemSet, id)
    if not pset:
        flask.abort(404, description="Problem set does not exist")

    if file and file.filename.lower().endswith(".pdf"):
        filepath = os.path.join(app.root_path, pset.pdf_path)
        file.save(filepath)
        return f"Successfully uploaded new PDF for problem set {pset.id} ({pset.name})"
    else:
        return "Invalid file type, please upload a PDF", 400