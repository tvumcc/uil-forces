import flask

import os
import shutil

from main import app, runtime_dir
from src.backend.orm import *
from src.backend.setup import *
from src.backend.utils import log, admin_required

# Admin API

@app.route("/api/admin/psets")
@admin_required
def admin_psets():
    """Returns a list of all the problem sets currently contained within the database"""

    return {"psets": [pset.shallow_serialize() for pset in db.session.query(ProblemSet).all()]}

@app.route("/api/admin/pset/<id>")
@admin_required
def admin_pset(id):
    """Returns the JSON data for the queried problem set"""

    pset = db.session.get(ProblemSet, id)
    if not pset:
        flask.abort(404, description="Problem set does not exist")
    return {"pset": pset.serialize()}

@app.route("/api/admin/update/pset", methods=["POST"])
@admin_required
def admin_update_pset():
    """Updates the specified problem set with the provided new values"""

    request = flask.request.get_json()
    id = request["id"]
    name = request["name"]
    grading_timeout = request["gradingTimeout"]

    pset = db.session.get(ProblemSet, id)
    pset.name = name
    pset.grading_timeout = grading_timeout

    db.session.add(pset)
    db.session.commit()

    return f"Successfully updated pset {id} ({pset.name})"

@app.route("/api/admin/add/pset", methods=["POST"])
@admin_required
def admin_add_pset():
    """Creates an empty problem set with just a name and adds it to the database"""

    request = flask.request.get_json()

    name = request["name"]

    pset = ProblemSet(name=name)
    db.session.add(pset)
    db.session.commit()

    return f"Created new empty problem set {pset.id} ({pset.name})"

@app.route("/api/admin/pset/add/problem", methods=["POST"])
@admin_required
def admin_pset_add_problem():
    """Creates an empty problem with just a name and adds it to the specified problem set"""

    request = flask.request.get_json()

    pset_id = request["psetID"]
    problem_name = request["problemName"]

    pset = db.session.get(ProblemSet, pset_id)
    if not pset:
        flask.abort(404, description="Problem set does not exist")

    problem = Problem(name=problem_name, pset=pset)
    db.session.add(problem)
    pset.problems.append(problem)

    db.session.add(pset)
    db.session.commit()

    return f"Created new empty problem {problem.id} ({problem.name})"

@app.route("/api/admin/pset/<id>/pdf")
@admin_required
def admin_pset_pdf(id):
    """Returns the entire PDF attached to this problem set"""

    pset = db.session.get(ProblemSet, id)
    if not pset:
        flask.abort(404, description="Problem set does not exist")
    return flask.send_from_directory(runtime_dir, os.path.join("pdfs", pset.get_pdf_name()))

@app.route("/api/admin/pset/<id>/uploadpdf", methods=["POST"])
@admin_required
def admin_pset_upload_pdf(id):
    """Uploads a new PDF to replace the one currently attached to the specified problem set"""

    file = flask.request.files["pdf"]
    pset =  db.session.get(ProblemSet, id)
    if not pset:
        flask.abort(404, description="Problem set does not exist")

    if file:
        filepath = os.path.join(runtime_dir, "pdfs", pset.get_pdf_name())
        file.save(filepath)
        return f"Successfully uploaded new PDF for problem set {pset.id} ({pset.name})"
    else:
        return "Invalid file type, please upload a PDF", 400