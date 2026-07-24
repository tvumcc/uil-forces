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

def test_pset_update_success(client, admin_logged_in, psets):
    id = 1
    new_name = "Problem Set A (edited)"

    response = client.post(f"/api/admin/pset/update", json={
        "id": id,
        "name": new_name
    })

    pset = db.session.get(ProblemSet, id)

    assert response.status_code == 204
    assert pset.name == new_name

def test_pset_update_invalid_name_too_short(client, admin_logged_in, psets):
    id = 1
    new_name = "AB"
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

def test_pset_update_invalid_name_too_long(client, admin_logged_in, psets):
    id = 1
    new_name = "ABCDEFGHIJKLMNOPQRSTUVWXYZABCDEFGHIJKLMNOPQRSTUVWXY"
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

def test_pset_update_requires_admin(client, user_logged_in, psets):
    id = 1
    new_name = "Problem Set A (edited)"
    pset = db.session.get(ProblemSet, id)
    old_name = pset.name
    db.session.expire(pset)

    response = client.post(f"/api/admin/pset/update", json={
        "id": id,
        "name": new_name
    })

    assert response.status_code == 403
    assert pset.name == old_name
    assert response.get_json()["error"] == "not_admin"

def test_pset_update_requires_csrf(app, client, admin_logged_in, psets):
    app.config["WTF_CSRF_ENABLED"] = True

    id = 1
    new_name = "Problem Set A (edited)"
    pset = db.session.get(ProblemSet, id)
    old_name = pset.name
    db.session.expire(pset)

    response = client.post(f"/api/admin/pset/update", json={
        "id": id,
        "name": new_name
    })

    assert response.status_code == 400
    assert pset.name == old_name
    assert response.get_json()["error"] == "csrf_invalid"

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

def test_pset_add_invalid_name_too_short(client, admin_logged_in, psets):
    name = "AB"

    response = client.post(f"/api/admin/pset/add", json={
        "name": name
    })

    pset = db.session.query(ProblemSet).filter_by(name=name).first()

    assert response.status_code == 400
    assert response.get_json()["error"] == "invalid_name"
    assert pset is None

def test_pset_add_invalid_name_too_short(client, admin_logged_in, psets):
    name = "ABCDEFGHIJKLMNOPQRSTUVWXYZABCDEFGHIJKLMNOPQRSTUVWXY"

    response = client.post(f"/api/admin/pset/add", json={
        "name": name
    })

    pset = db.session.query(ProblemSet).filter_by(name=name).first()

    assert response.status_code == 400
    assert response.get_json()["error"] == "invalid_name"
    assert pset is None

def test_pset_add_pset_exists(client, admin_logged_in, psets):
    name = "Problem Set A"

    response = client.post(f"/api/admin/pset/add", json={
        "name": name
    })

    pset_count = db.session.query(ProblemSet).filter_by(name=name).count()

    assert response.status_code == 409
    assert pset_count == 1
    assert response.get_json()["error"] == "pset_exists"

def test_pset_add_requires_admin(client, user_logged_in, psets):
    name = "Problem Set D"

    response = client.post(f"/api/admin/pset/add", json={
        "name": name
    })

    pset = db.session.query(ProblemSet).filter_by(name=name).first()

    assert response.status_code == 403
    assert pset is None
    assert response.get_json()["error"] == "not_admin"

def test_pset_add_requires_csrf(app, client, admin_logged_in, psets):
    app.config["WTF_CSRF_ENABLED"] = True

    name = "Problem Set D"

    response = client.post(f"/api/admin/pset/add", json={
        "name": name
    })

    pset = db.session.query(ProblemSet).filter_by(name=name).first()

    assert response.status_code == 400
    assert pset is None
    assert response.get_json()["error"] == "csrf_invalid"

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

def test_pset_add_problem_invalid_name_too_short(client, admin_logged_in, psets):
    pset_id = 1
    problem_name = "AB"

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

def test_pset_add_problem_invalid_name_too_long(client, admin_logged_in, psets):
    pset_id = 1
    problem_name = "ABCDEFGHIJKLMNOPQRSTUVWXYZABCDEFGHIJKLMNOPQRSTUVWXY"

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

def test_pset_add_problem_requires_admin(client, user_logged_in, psets):
    pset_id = 1
    problem_name = "Problem A"

    response = client.post(f"/api/admin/pset/add/problem", json={
        "problemName": problem_name,
        "psetID": pset_id
    })

    problem = db.session.query(Problem).filter_by(name=problem_name).first()
    pset = db.session.get(ProblemSet, pset_id) 

    assert response.status_code == 403
    assert problem is None
    assert len(pset.problems) == 0
    assert response.get_json()["error"] == "not_admin"

def test_pset_add_problem_requires_admin(app, client, admin_logged_in, psets):
    app.config["WTF_CSRF_ENABLED"] = True

    pset_id = 1
    problem_name = "Problem A"

    response = client.post(f"/api/admin/pset/add/problem", json={
        "problemName": problem_name,
        "psetID": pset_id
    })

    problem = db.session.query(Problem).filter_by(name=problem_name).first()
    pset = db.session.get(ProblemSet, pset_id) 

    assert response.status_code == 400
    assert problem is None
    assert len(pset.problems) == 0
    assert response.get_json()["error"] == "csrf_invalid"

# ========================================
# TODO: /api/admin/pset/<id>/pdf
# ========================================

# ========================================
# TODO: /api/admin/pset/<id>/uploadpdf
# ========================================