import flask
import flask_login
import pypdf

import os

from main import app, runtime_dir
from src.backend.orm import *
from src.backend.utils import log, user_required, admin_required

@app.route("/api/problem/<id>/pdf")
@user_required
def problem_pdf(id):
    """Returns a section of the problem set PDF for the specified problem"""

    problem = db.session.get(Problem, id)
    if not problem:
        flask.abort(404)

    # Only allow access to the problem's PDF if the practice site is enabled and the problem set is not hidden 
    # or if there is an ongoing contest with the problem
    contests = db.session.query(Contest).all()
    problem_ongoing = False
    for contest in contests:
        if contest.is_ongoing() and contest.show_pdf:
            if problem in contest.problems():
                problem_ongoing = True
                break
    try:
        if Settings.practice_site_enabled() and not problem.pset.hide or problem_ongoing:
            pdf_path = os.path.join(runtime_dir, "pdfs", problem.pset.get_pdf_name())
            pages = [int(x)-1 for x in problem.pages.split()]

            if not os.path.exists(pdf_path) or len(pages) == 0:
                flask.abort(404)

            reader = pypdf.PdfReader(pdf_path)
            writer = pypdf.PdfWriter()

            for page in pages:
                if page > 0 and page <= len(reader.pages):
                    writer.add_page(reader.pages[page])

            temp_pdf = os.path.join(runtime_dir, "pdfs", f"problem{id}.pdf")
            with open(temp_pdf, "wb") as output_pdf:
                writer.write(output_pdf)
            response = flask.send_from_directory(os.path.join(runtime_dir, "pdfs"), f"problem{id}.pdf")
            return response
        else:
            return f"PDF for problem {id} cannot be accessed at this time", 403
    finally:
        try: os.remove(temp_pdf)
        except: pass



# Admin API



@app.route("/api/admin/problem/<id>")
@admin_required
def admin_problem(id):
    """Return JSON data for the queried problem"""
        
    problem = db.session.get(Problem, id) 
    if not problem:
        flask.abort(404, description="Problem does not exist")

    return {"problem": problem.serialize()}

@app.route("/api/admin/update/problem", methods=["POST"])
@admin_required
def admin_update_problem():
    """Updates the specified problem with the provided new values"""

    request = flask.request.get_json()
    problem = db.session.get(Problem, request["id"]) 
    if not problem:
        flask.abort(404, description="Problem does not exist")

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

    return f"Successfully updated problem {problem.id}"

@app.route("/api/admin/problem/<id>/delete", methods=["DELETE"])
@admin_required
def admin_delete_problem(id):
    """Deletes the specified problem and its submissions"""

    problem = db.session.get(Problem, id) 
    if not problem:
        return flask.abort(404, description="Problem does not exist")

    db.session.delete(problem)
    db.session.commit()

    return f"Successfully deleted problem {id}"