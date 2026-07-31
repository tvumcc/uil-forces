import pytest
import io
import os

from tests.utils import *
from src.models.orm import *

# ========================================
# /api/admin/psets
# ========================================

def test_pset_list_success(client, admin_logged_in, psets):
    response = client.get("/api/admin/psets")

    assert response.status_code == 200
    pset_list = response.get_json()["psets"]

    psetA = db.session.query(ProblemSet).filter_by(name="Problem Set A").first()
    psetB = db.session.query(ProblemSet).filter_by(name="Problem Set B").first()
    psetC = db.session.query(ProblemSet).filter_by(name="Problem Set C").first()

    assert len(pset_list) == 3
    assert pset_list[0] == psetA.shallow_serialize()
    assert pset_list[1] == psetB.shallow_serialize()
    assert pset_list[2] == psetC.shallow_serialize()

def test_pset_list_empty(client, admin_logged_in):
    response = client.get("/api/admin/psets")

    assert response.status_code == 200
    pset_list = response.get_json()["psets"]
    assert len(pset_list) == 0

# ========================================
# /api/admin/pset/<id>
# ========================================

def test_pset_success(client, admin_logged_in, psets):
    id = 1
    response = client.get(f"/api/admin/pset/{id}")

    assert response.status_code == 200

    psetDB = db.session.get(ProblemSet, id)
    psetResp = response.get_json()["pset"]

    assert psetDB.serialize() == psetResp

def test_pset_not_found(client, admin_logged_in, psets):
    id = 100
    response = client.get(f"/api/admin/pset/{id}")

    assert response.status_code == 404
    assert response.get_json()["error"] == "pset_not_found"

# ========================================
# /api/admin/pset/update
# ========================================

def test_pset_update_success(client, admin_logged_in, psets):
    id = 1
    new_name = "Problem Set A (edited)"

    response = client.post(f"/api/admin/pset/update", json={
        "id": id,
        "name": new_name
    })

    pset = db.session.get(ProblemSet, id)

    assert response.status_code == 204
    assert response.get_json() is None
    assert pset.name == new_name

@pytest.mark.parametrize("new_name", [
    ("AB"),
    ("ABCDEFGHIJKLMNOPQRSTUVWXYZABCDEFGHIJKLMNOPQRSTUVWXY"),
])
def test_pset_update_invalid_name_too_short(client, admin_logged_in, psets, new_name):
    id = 1
    pset = db.session.get(ProblemSet, id)
    old_name = pset.name
    db.session.expire(pset)

    response = client.post(f"/api/admin/pset/update", json={
        "id": id,
        "name": new_name
    })

    assert response.status_code == 400
    assert pset.name == old_name
    assert response.get_json()["error"] == "invalid_name"

def test_pset_update_pset_exists(client, admin_logged_in, psets):
    id = 1
    new_name = "Problem Set B"
    pset = db.session.get(ProblemSet, id)
    old_name = pset.name
    db.session.expire(pset)

    response = client.post(f"/api/admin/pset/update", json={
        "id": id,
        "name": new_name
    })

    assert response.status_code == 409
    assert pset.name == old_name
    assert response.get_json()["error"] == "pset_exists"

# ========================================
# /api/admin/pset/add
# ========================================

def test_pset_add_success(client, admin_logged_in, psets):
    name = "Problem Set D"

    response = client.post(f"/api/admin/pset/add", json={
        "name": name
    })

    pset = db.session.query(ProblemSet).filter_by(name=name).first()

    assert response.status_code == 201
    assert pset is not None

@pytest.mark.parametrize("pset_name", [
    ("AB"),
    ("ABCDEFGHIJKLMNOPQRSTUVWXYZABCDEFGHIJKLMNOPQRSTUVWXY")
])
def test_pset_add_invalid_name_too_short(client, admin_logged_in, psets, pset_name):
    response = client.post(f"/api/admin/pset/add", json={
        "name": pset_name 
    })

    pset = db.session.query(ProblemSet).filter_by(name=pset_name).first()

    assert response.status_code == 400
    assert pset is None
    assert response.get_json()["error"] == "invalid_name"

def test_pset_add_pset_exists(client, admin_logged_in, psets):
    name = "Problem Set A"

    response = client.post(f"/api/admin/pset/add", json={
        "name": name
    })

    pset_count = db.session.query(ProblemSet).filter_by(name=name).count()

    assert response.status_code == 409
    assert pset_count == 1
    assert response.get_json()["error"] == "pset_exists"

# ========================================
# /api/admin/pset/add/problem
# ========================================

def test_pset_add_problem_success(client, admin_logged_in, psets):
    pset_id = 1
    problem_name = "Problem A"

    response = client.post(f"/api/admin/pset/add/problem", json={
        "problemName": problem_name,
        "psetID": pset_id
    })

    problem = db.session.query(Problem).filter_by(name=problem_name).first()
    pset = db.session.get(ProblemSet, pset_id) 

    assert response.status_code == 201
    assert problem.name == problem_name
    assert len(pset.problems) == 1
    assert pset.problems[0] is problem

def test_pset_add_problem_pset_not_found(client, admin_logged_in, psets):
    pset_id = 100
    problem_name = "Problem A"

    response = client.post(f"/api/admin/pset/add/problem", json={
        "problemName": problem_name,
        "psetID": pset_id
    })

    problem = db.session.query(Problem).filter_by(name=problem_name).first()
    pset = db.session.get(ProblemSet, pset_id) 

    assert response.status_code == 404
    assert pset is None
    assert problem is None
    assert response.get_json()["error"] == "pset_not_found"


@pytest.mark.parametrize("problem_name", [
    ("AB"),
    ("ABCDEFGHIJKLMNOPQRSTUVWXYZABCDEFGHIJKLMNOPQRSTUVWXY"),
])
def test_pset_add_problem_invalid_name(client, admin_logged_in, psets, problem_name):
    pset_id = 1

    response = client.post(f"/api/admin/pset/add/problem", json={
        "problemName": problem_name,
        "psetID": pset_id
    })

    problem = db.session.query(Problem).filter_by(name=problem_name).first()
    pset = db.session.get(ProblemSet, pset_id) 

    assert response.status_code == 400
    assert problem is None
    assert len(pset.problems) == 0
    assert response.get_json()["error"] == "invalid_name"

def test_pset_add_problem_problem_exists_in_pset(client, admin_logged_in, psets):
    pset_id = 1
    problem_name = "Problem A"

    pset = db.session.get(ProblemSet, pset_id)
    problem1 = Problem(name=problem_name, pset=pset)
    db.session.add(problem1)
    pset.problems.append(problem1)
    db.session.commit()

    assert len(pset.problems) == 1

    db.session.expire(pset)

    response = client.post(f"/api/admin/pset/add/problem", json={
        "problemName": problem_name,
        "psetID": pset_id
    })

    problem = db.session.query(Problem).filter_by(name=problem_name).first()

    assert response.status_code == 409
    assert problem is problem1
    assert len(pset.problems) == 1
    assert response.get_json()["error"] == "problem_exists_in_pset"

# ========================================
# /api/admin/pset/<id>/pdf
# ========================================

def test_admin_pset_pdf_not_found(client, admin_logged_in):
    response = client.get("/api/admin/pset/999/pdf")
    assert response.status_code == 404
    assert response.get_json()["error"] == "pset_not_found"

def test_admin_pset_pdf_success(client, admin_logged_in, psets, monkeypatch, tmp_path):
    monkeypatch.setattr("src.routes.pset.runtime_dir", str(tmp_path))

    pset = db.session.get(ProblemSet, 1)
    pdf_path = os.path.join(tmp_path, "pdfs", pset.get_pdf_name())
    write_minimal_pdf(pdf_path)

    response = client.get(f"/api/admin/pset/{pset.id}/pdf")

    assert response.status_code == 200
    assert response.mimetype == "application/pdf"

def test_admin_pset_pdf_file_missing_on_disk(client, admin_logged_in, psets, monkeypatch, tmp_path):
    monkeypatch.setattr("src.routes.pset.runtime_dir", str(tmp_path))
    pset = db.session.get(ProblemSet, 1)

    response = client.get(f"/api/admin/pset/{pset.id}/pdf")
    assert response.status_code == 404
    assert response.get_json()["error"] == "pdf_not_found"

# ========================================
# /api/admin/pset/<id>/uploadpdf
# ========================================

def test_admin_pset_upload_pdf_success(client, admin_logged_in, psets, monkeypatch, tmp_path):
    monkeypatch.setattr("src.routes.pset.runtime_dir", str(tmp_path))
    os.mkdir(os.path.join(tmp_path, "pdfs"))
    pset = db.session.get(ProblemSet, 1)

    fake_pdf_bytes = b"%PDF-1.4 fake content for test"
    response = client.post(
        f"/api/admin/pset/{pset.id}/uploadpdf",
        data={"pdf": (io.BytesIO(fake_pdf_bytes), "upload.pdf")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 204
    saved_path = os.path.join(tmp_path, "pdfs", pset.get_pdf_name())
    assert os.path.exists(saved_path)
    with open(saved_path, "rb") as f:
        assert f.read() == fake_pdf_bytes

def test_admin_pset_upload_pdf_not_found(client, admin_logged_in, monkeypatch, tmp_path):
    monkeypatch.setattr("src.routes.pset.runtime_dir", str(tmp_path))

    response = client.post(
        "/api/admin/pset/999/uploadpdf",
        data={"pdf": (io.BytesIO(b"x"), "upload.pdf")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 404
    assert response.get_json()["error"] == "pset_not_found"

def test_admin_pset_upload_pdf_empty_filename_rejected(client, admin_logged_in, psets, monkeypatch, tmp_path):
    monkeypatch.setattr("src.routes.pset.runtime_dir", str(tmp_path))
    pset = db.session.get(ProblemSet, 1)

    response = client.post(
        f"/api/admin/pset/{pset.id}/uploadpdf",
        data={"pdf": (io.BytesIO(b""), "")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "invalid_file_type"