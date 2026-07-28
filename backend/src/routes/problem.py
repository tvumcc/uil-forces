import flask
import flask_login
import pypdf

import os

from src.app import runtime_dir
from src.models.orm import *
from src.utils import log, admin_required, valid_name

bp = flask.Blueprint("problem", __name__)

@bp.route("/api/problem/<id>/pdf")
@flask_login.login_required
def problem_pdf(id):
    """Returns a section of the problem set PDF for the specified problem"""

    problem = db.session.get(Problem, id)
    if not problem:
        return {"error": "problem_not_found"}, 404

    # Only allow access to the problem's PDF during an ongoing contest with PDFs enabled
    problem_ongoing = False
    for contest in db.session.query(Contest).all():
        if contest.is_ongoing() and contest.show_pdf and problem in contest.problems():
            problem_ongoing = True
            break
    try:
        if problem_ongoing:
            pdf_path = os.path.join(runtime_dir, "pdfs", problem.pset.get_pdf_name())
            pages = [int(x)-1 for x in problem.pages.split()]

            if not os.path.exists(pdf_path) or len(pages) == 0:
                return {"error": "pdf_not_found"}, 404

            reader = pypdf.PdfReader(pdf_path)
            writer = pypdf.PdfWriter()

            for page in pages:
                if page >= 0 and page <= len(reader.pages):
                    writer.add_page(reader.pages[page])

            temp_pdf = os.path.join(runtime_dir, "pdfs", f"problem{id}.pdf")
            with open(temp_pdf, "wb") as output_pdf:
                writer.write(output_pdf)
            response = flask.send_from_directory(os.path.join(runtime_dir, "pdfs"), f"problem{id}.pdf")
            return response
        else:
            return {"error": "pdf_restricted"}, 403
    finally:
        try: os.remove(temp_pdf)
        except: pass



# Admin API



@bp.route("/api/admin/problem/<id>")
@admin_required
def admin_problem(id):
    """Return JSON data for the queried problem"""
        
    problem = db.session.get(Problem, id) 
    if not problem:
        return {"error": "problem_not_found"}, 404

    return {"problem": problem.serialize(), "pset": problem.pset.shallow_serialize()}

@bp.route("/api/admin/problem/update", methods=["POST"])
@admin_required
def admin_update_problem():
    """Updates the specified problem with the provided new values"""

    request = flask.request.get_json()
    problem = db.session.get(Problem, request["id"]) 
    if not problem:
        return {"error": "problem_not_found"}, 404
    if not valid_name(request["name"]):
        return {"error": "invalid_name"}, 400

    problem.name = request["name"]
    problem.pages = request["pages"]
    problem.use_stdin = request["useStdin"]
    problem.input_file_name = request["inputFileName"]
    problem.student_input = request["studentInput"]
    problem.judge_input = request["judgeInput"]
    problem.judge_output = request["judgeOutput"]

    db.session.add(problem)
    db.session.commit()

    log.info(f"Problem {problem.id} ({problem.name}) updated by {flask_login.current_user.username}")

    return "", 204

@bp.route("/api/admin/problem/<id>/delete", methods=["DELETE"])
@admin_required
def admin_delete_problem(id):
    """Deletes the specified problem and its submissions"""

    problem = db.session.get(Problem, id) 
    if not problem:
        return {"error": "problem_not_found"}, 404

    db.session.delete(problem)
    db.session.commit()

    log.info(f"Problem {problem.id} ({problem.name}) deleted by {flask_login.current_user.username}")

    return "", 204
