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

def test_pset_list_requires_admin(client, user_logged_in):
    response = client.get("/api/admin/psets")

    assert response.status_code == 403
    assert response.get_json()["error"] == "not_admin"

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

def test_pset_requires_admin(client, user_logged_in, psets):
    id = 1
    response = client.get(f"/api/admin/pset/{id}")

    assert response.status_code == 403
    assert response.get_json()["error"] == "not_admin"

# ========================================
# /api/admin/pset/update
# ========================================

# ========================================
# /api/admin/pset/add
# ========================================

# ========================================
# /api/admin/pset/add/problem
# ========================================

# ========================================
# TODO: /api/admin/pset/<id>/pdf
# ========================================

# ========================================
# TODO: /api/admin/pset/<id>/uploadpdf
# ========================================