import flask
import flask_login

import os

from src.app import app, runtime_dir
from src.models.orm import *
from src.setup import *
from src.utils import admin_required, valid_name

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
        return {"error": "pset_not_found"}, 404

    return {"pset": pset.serialize()}

@app.route("/api/admin/pset/update", methods=["POST"])
@admin_required
def admin_update_pset():
    """Updates the specified problem set with the provided new values"""

    request = flask.request.get_json()
    id = request["id"]
    name = request["name"]

    pset = db.session.get(ProblemSet, id)

    if not valid_name(name):
        return {"error": "invalid_name"}, 400
    if pset.name != name and db.session.query(ProblemSet).filter_by(name=name).first() is not None:
        return {"error": "pset_exists"}, 409

    pset.name = name

    db.session.add(pset)
    db.session.commit()

    log.info(f"Problem set {pset.id} ({pset.name}) details updated by {flask_login.current_user.username}")

    return "", 204

@app.route("/api/admin/pset/add", methods=["POST"])
@admin_required
def admin_add_pset():
    """Creates an empty problem set with just a name and adds it to the database"""

    request = flask.request.get_json()

    name = request["name"]

    if not valid_name(name):
        return {"error": "invalid_name"}, 400
    if db.session.query(ProblemSet).filter_by(name=name).first() is not None:
        return {"error": "pset_exists"}, 409

    pset = ProblemSet(name=name)
    db.session.add(pset)
    db.session.commit()

    log.info(f"Problem set {pset.id} ({pset.name}) created by {flask_login.current_user.username}")

    return "", 201

@app.route("/api/admin/pset/add/problem", methods=["POST"])
@admin_required
def admin_pset_add_problem():
    """Creates an empty problem with just a name and adds it to the specified problem set"""

    request = flask.request.get_json()

    pset_id = request["psetID"]
    problem_name = request["problemName"]

    pset = db.session.get(ProblemSet, pset_id)
    if not pset:
        return {"error": "pset_not_found"}, 404
    if not valid_name(problem_name):
        return {"error": "invalid_name"}, 400
    if db.session.query(Problem).filter_by(name=problem_name, pset=pset).first() is not None:
        return {"error": "problem_exists_in_pset"}, 409

    problem = Problem(name=problem_name, pset=pset)
    db.session.add(problem)
    pset.problems.append(problem)

    db.session.add(pset)
    db.session.commit()

    log.info(f"Problem {problem.id} ({problem.name}) created by {flask_login.current_user.username}")

    return "", 201

@app.route("/api/admin/pset/<id>/pdf")
@admin_required
def admin_pset_pdf(id):
    """Returns the entire PDF attached to this problem set"""

    pset = db.session.get(ProblemSet, id)
    if not pset:
        return {"error": "pset_not_found"}, 404
    return flask.send_from_directory(runtime_dir, os.path.join("pdfs", pset.get_pdf_name()))

@app.route("/api/admin/pset/<id>/uploadpdf", methods=["POST"])
@admin_required
def admin_pset_upload_pdf(id):
    """Uploads a new PDF to replace the one currently attached to the specified problem set"""

    file = flask.request.files["pdf"]
    pset =  db.session.get(ProblemSet, id)
    if not pset:
        return {"error": "pset_not_found"}, 404

    if file:
        filepath = os.path.join(runtime_dir, "pdfs", pset.get_pdf_name())
        file.save(filepath)

        log.info(f"PDF for problem set {pset.id} ({pset.name}) uploaded by {flask_login.current_user.username}")

        return "", 204
    else:
        return {"error": "invalid_file_type"}, 400