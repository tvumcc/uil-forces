from src.models.orm import *
import pytest

# ========================================
# TODO: /api/problem/<id>/pdf
# ========================================



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