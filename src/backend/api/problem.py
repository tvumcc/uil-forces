import flask
import flask_login
import pypdf

import os

from main import app
from src.backend.orm import *

@app.route("/api/problem/<id>/pdf")
@flask_login.login_required
def problem_pdf(id):
    problem = db.session.get(Problem, id)
    if not problem: flask.abort(404)

    # Only allow access to the problem's PDF if the practice site is enabled and the problem set is not hidden 
    # or if there is an ongoing contest with the problem
    practice_site = db.session.query(Settings).filter_by(key="practice_site").first().value.lower() == "true"
    contests = db.session.query(Contest).all()
    problemOngoing = False
    for contest in contests:
        if contest.ongoing() and contest.show_pdf:
            if problem in contest.problems():
                problemOngoing = True
                break

    if practice_site and not problem.problem_set.hide or problemOngoing:
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
        try:
            os.remove(temp_pdf)
        except: pass
        return response
    else:
        return flask.Response(status=403)

@app.route("/api/admin/problem/<id>")
@flask_login.login_required
def admin_problem(id):
    if not flask_login.current_user.is_admin:
        return flask.abort(400)
    problem = db.session.get(Problem, id) 
    return {"problem": problem.serialize()}

@app.route("/api/admin/update/problem", methods=["POST"])
@flask_login.login_required
def admin_update_problem():
    if not flask_login.current_user.is_admin:
        return flask.abort(400)

    request = flask.request.get_json()
    problem = db.session.get(Problem, request["id"]) 

    problem.name = request["name"]
    problem.pages = request["pages"]
    problem.use_stdin = request["use_stdin"]
    problem.input_file_name = request["input_file_name"]
    problem.student_input = request["student_input"]
    problem.judge_input = request["judge_input"]
    problem.judge_output = request["judge_output"]

    db.session.add(problem)
    db.session.commit()

    return flask.Response(status=200)