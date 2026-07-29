import os
import pypdf

from src.models.orm import *
import pytest

def write_minimal_pdf(path, num_pages=1):
    writer = pypdf.PdfWriter()
    for _ in range(num_pages):
        writer.add_blank_page(width=200, height=200)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        writer.write(f)

# ========================================
# /api/problem/<id>/pdf
# ========================================

def test_problem_pdf_not_found(client, user_logged_in):
    response = client.get("/api/problem/999/pdf")
    assert response.status_code == 404
    assert response.get_json()["error"] == "problem_not_found"

def test_problem_pdf_restricted_no_ongoing_contest(client, user_logged_in, problems):
    response = client.get(f"/api/problem/{problems.id}/pdf")
    assert response.status_code == 403
    assert response.get_json()["error"] == "pdf_restricted"

def test_problem_pdf_restricted_show_pdf_disabled(client, user_logged_in, ongoing_contest_with_problem, problems):
    ongoing_contest_with_problem.show_pdf = False
    db.session.commit()

    response = client.get(f"/api/problem/{problems.id}/pdf")
    assert response.status_code == 403
    assert response.get_json()["error"] == "pdf_restricted"

def test_problem_pdf_success(client, user_logged_in, ongoing_contest_with_problem, problems, monkeypatch, tmp_path):
    monkeypatch.setattr("src.routes.problem.runtime_dir", str(tmp_path))
    ongoing_contest_with_problem.show_pdf = True
    db.session.commit()

    problems.pages = "1"
    pdf_path = os.path.join(tmp_path, "pdfs", problems.pset.get_pdf_name())
    write_minimal_pdf(pdf_path, num_pages=3)
    db.session.commit()

    response = client.get(f"/api/problem/{problems.id}/pdf")

    assert response.status_code == 200
    assert response.mimetype == "application/pdf"

    temp_path = os.path.join(tmp_path, "pdfs", f"problem{problems.id}.pdf")
    assert not os.path.exists(temp_path)

def test_problem_pdf_not_found_when_source_missing(client, user_logged_in, ongoing_contest_with_problem, problems, monkeypatch, tmp_path):
    monkeypatch.setattr("src.routes.problem.runtime_dir", str(tmp_path))
    ongoing_contest_with_problem.show_pdf = True
    problems.pages = "1"
    db.session.commit()

    response = client.get(f"/api/problem/{problems.id}/pdf")
    assert response.status_code == 404
    assert response.get_json()["error"] == "pdf_not_found"

def test_problem_pdf_off_by_one_page_bug(client, user_logged_in, ongoing_contest_with_problem, problems, monkeypatch, tmp_path):
    monkeypatch.setattr("src.routes.problem.runtime_dir", str(tmp_path))
    ongoing_contest_with_problem.show_pdf = True
    problems.pages = "2"  # -> index 1, out of range for a 1-page pdf
    pdf_path = os.path.join(tmp_path, "pdfs", problems.pset.get_pdf_name())
    write_minimal_pdf(pdf_path, num_pages=1)
    db.session.commit()

    response = client.get(f"/api/problem/{problems.id}/pdf")

    assert response.status_code != 500

# ========================================
# /api/admin/problem/<id>
# ========================================

def test_problem_success(client, admin_logged_in, problems):
    response = client.get("/api/admin/problem/1")

    problem = db.session.get(Problem, 1)
    pset = db.session.get(ProblemSet, 1)

    assert response.status_code == 200
    assert response.get_json()["problem"] == problem.serialize()
    assert response.get_json()["pset"] == pset.shallow_serialize()

def test_problem_not_found(client, admin_logged_in):
    response = client.get("/api/admin/problem/1")

    assert response.status_code == 404
    assert response.get_json()["error"] == "problem_not_found"

# ========================================
# /api/admin/problem/update
# ========================================

def test_problem_update_success(client, admin_logged_in, problems):
    problem_id = 1

    new_problem_details = {
        "id": problem_id,
        "name": "Problem A (edited)",
        "pages": "1 2",
        "useStdin": True,
        "inputFileName": "A.dat",
        "studentInput": "1\nHello",
        "judgeInput": "3\nHello\nBello\nJello",
        "judgeOutput": "1\n2\n3"
    }

    response = client.post("/api/admin/problem/update", json=new_problem_details)

    problem = db.session.get(Problem, problem_id)

    assert response.status_code == 204
    assert response.get_json() is None
    assert new_problem_details.items() <= problem.serialize().items()

def test_problem_update_not_found(client, admin_logged_in):
    problem_id = 1

    new_problem_details = {
        "id": problem_id,
        "name": "Problem A (edited)",
        "pages": "1 2",
        "useStdin": True,
        "inputFileName": "A.dat",
        "studentInput": "1\nHello",
        "judgeInput": "3\nHello\nBello\nJello",
        "judgeOutput": "1\n2\n3"
    }

    response = client.post("/api/admin/problem/update", json=new_problem_details)

    assert response.status_code == 404
    assert response.get_json()["error"] == "problem_not_found"

@pytest.mark.parametrize("name", [
    ("AB"),
    ("ABCDEFGHIJKLMNOPQRSTUVWXYZABCDEFGHIJKLMNOPQRSTUVWXY")
])
def test_problem_update_invalid_name(client, admin_logged_in, problems, name):
    problem_id = 1

    problem = db.session.get(Problem, problem_id)
    old_problem_details = problem.serialize()
    db.session.expire(problem)

    new_problem_details = {
        "id": problem_id,
        "name": name,
        "pages": "1 2",
        "useStdin": True,
        "inputFileName": "A.dat",
        "studentInput": "1\nHello",
        "judgeInput": "3\nHello\nBello\nJello",
        "judgeOutput": "1\n2\n3"
    }

    response = client.post("/api/admin/problem/update", json=new_problem_details)

    assert response.status_code == 400
    assert response.get_json()["error"] == "invalid_name"
    assert problem.serialize() == old_problem_details

# ========================================
# /api/admin/problem/<id>/delete
# ========================================

def test_problem_delete_success(client, admin_logged_in, problems):
    problem_id = 1

    response = client.delete(f"/api/admin/problem/{problem_id}/delete")

    problem = db.session.get(Problem, problem_id)

    assert response.status_code == 204
    assert response.get_json() is None 
    assert problem is None

def test_problem_delete_not_found(client, admin_logged_in):
    problem_id = 1

    response = client.delete(f"/api/admin/problem/{problem_id}/delete")

    assert response.status_code == 404
    assert response.get_json()["error"] == "problem_not_found"