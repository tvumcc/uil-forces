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
