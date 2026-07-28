import pytest
import os

from src.models.orm import *
from src.judge import Status

# ========================================
# /api/contests
# ========================================

def test_contests_categorizes_correctly(client, user_logged_in, ongoing_contest, upcoming_contest, past_contest):
    response = client.get("/api/contests")
    data = response.get_json()

    assert response.status_code == 200
    assert [c["name"] for c in data["ongoing"]] == [ongoing_contest.name]
    assert [c["name"] for c in data["upcoming"]] == [upcoming_contest.name]
    assert [c["name"] for c in data["past"]] == [past_contest.name]

def test_contests_empty(client, user_logged_in):
    response = client.get("/api/contests")
    data = response.get_json()

    assert response.status_code == 200
    assert data == {"upcoming": [], "ongoing": [], "past": []}

# ========================================
# /api/contest/<id>
# ========================================

def test_contest_not_found(client, user_logged_in):
    response = client.get("/api/contest/999")
    assert response.status_code == 404
    assert response.get_json()["error"] == "contest_not_found"

def test_contest_upcoming_has_no_submissions_key(client, user_logged_in, upcoming_contest):
    response = client.get(f"/api/contest/{upcoming_contest.id}")
    data = response.get_json()

    assert response.status_code == 200
    assert "submissions" not in data["contest"]

def test_contest_creates_profile_if_missing(client, user_logged_in, ongoing_contest):
    assert db.session.query(ContestProfile).filter_by(user=user_logged_in, contest=ongoing_contest).first() is None

    response = client.get(f"/api/contest/{ongoing_contest.id}")

    assert response.status_code == 200
    profile = db.session.query(ContestProfile).filter_by(user=user_logged_in, contest=ongoing_contest).first()
    assert profile is not None

def test_contest_ongoing_only_shows_own_submissions(client, user_logged_in, ongoing_contest_with_problem, problems):
    other_user = User(username="other", password_hash="x", is_admin=False)
    db.session.add(other_user)
    db.session.commit()

    my_profile = ContestProfile(user=user_logged_in, contest=ongoing_contest_with_problem)
    other_profile = ContestProfile(user=other_user, contest=ongoing_contest_with_problem)
    db.session.add_all([my_profile, other_profile])
    db.session.commit()

    my_submission = Submission(
        problem=problems, contest_profile=my_profile, user=user_logged_in,
        status=Status.Accepted.value, code="a", language="Python",
        submit_time=datetime.datetime.now(timezone.utc),
    )
    other_submission = Submission(
        problem=problems, contest_profile=other_profile, user=other_user,
        status=Status.Accepted.value, code="b", language="Python",
        submit_time=datetime.datetime.now(timezone.utc),
    )
    db.session.add_all([my_submission, other_submission])
    db.session.commit()

    response = client.get(f"/api/contest/{ongoing_contest_with_problem.id}")
    data = response.get_json()

    submission_ids = [s["id"] for s in data["contest"]["submissions"]]
    assert response.status_code == 200
    assert my_submission.id in submission_ids
    assert other_submission.id not in submission_ids

def test_contest_past_shows_all_profiles_submissions(client, user_logged_in, problems, past_contest_with_problem):
    other_user = User(username="other", password_hash="x", is_admin=False)
    db.session.add(other_user)
    db.session.commit()

    my_profile = ContestProfile(user=user_logged_in, contest=past_contest_with_problem)
    other_profile = ContestProfile(user=other_user, contest=past_contest_with_problem)
    db.session.add_all([my_profile, other_profile])
    db.session.commit()

    other_submission = Submission(
        problem=problems, contest_profile=other_profile, user=other_user,
        status=Status.Accepted.value, code="b", language="Python",
        submit_time=datetime.datetime.now(timezone.utc),
    )
    db.session.add(other_submission)
    db.session.commit()

    response = client.get(f"/api/contest/{past_contest_with_problem.id}")
    data = response.get_json()

    submission_ids = [s["id"] for s in data["contest"]["submissions"]]
    assert response.status_code == 200
    assert other_submission.id in submission_ids

# ========================================
# /api/contest/submit
# ========================================

def test_contest_submit_problem_not_found(client, user_logged_in, ongoing_contest):
    response = client.post("/api/contest/submit", json={
        "problemID": 999, "contestID": ongoing_contest.id, "code": "x", "language": "Python"
    })
    assert response.status_code == 404
    assert response.get_json()["error"] == "problem_not_found"

def test_contest_submit_contest_not_found(client, user_logged_in, problems):
    response = client.post("/api/contest/submit", json={
        "problemID": problems.id, "contestID": 999, "code": "x", "language": "Python"
    })
    assert response.status_code == 404
    assert response.get_json()["error"] == "contest_not_found"

def test_contest_submit_contest_not_ongoing_upcoming(client, user_logged_in, upcoming_contest, problems):
    response = client.post("/api/contest/submit", json={
        "problemID": problems.id, "contestID": upcoming_contest.id, "code": "x", "language": "Python"
    })
    assert response.status_code == 403
    assert response.get_json()["error"] == "contest_not_ongoing"

def test_contest_submit_contest_not_ongoing_past(client, user_logged_in, past_contest, problems):
    response = client.post("/api/contest/submit", json={
        "problemID": problems.id, "contestID": past_contest.id, "code": "x", "language": "Python"
    })
    assert response.status_code == 403
    assert response.get_json()["error"] == "contest_not_ongoing"

def test_contest_submit_invalid_language(client, user_logged_in, ongoing_contest_with_problem, problems):
    response = client.post("/api/contest/submit", json={
        "problemID": problems.id, "contestID": ongoing_contest_with_problem.id,
        "code": "x", "language": "COBOL"
    })
    assert response.status_code == 400
    assert response.get_json()["error"] == "invalid_language"

def test_contest_submit_success(client, user_logged_in, ongoing_contest_with_problem, problems, monkeypatch):
    calls = []
    monkeypatch.setattr(
        "src.routes.contest.enqueue_submission",
        lambda submission_id, contest_profile_id=None: calls.append((submission_id, contest_profile_id))
    )

    response = client.post("/api/contest/submit", json={
        "problemID": problems.id, "contestID": ongoing_contest_with_problem.id,
        "code": "print(1)", "language": "Java"
    })

    assert response.status_code == 200
    submission_id = response.get_json()["submission"]["id"]

    submission = db.session.get(Submission, submission_id)
    assert submission.status == Status.Pending.value
    assert submission.language == "Java"
    assert len(calls) == 1
    assert calls[0][0] == submission_id

def test_contest_submit_cooldown_blocks_rapid_resubmission(client, user_logged_in, ongoing_contest_with_problem, problems, monkeypatch):
    monkeypatch.setattr("src.routes.contest.enqueue_submission", lambda *a, **k: None)

    client.post("/api/contest/submit", json={
        "problemID": problems.id, "contestID": ongoing_contest_with_problem.id,
        "code": "a", "language": "Java"
    })
    response = client.post("/api/contest/submit", json={
        "problemID": problems.id, "contestID": ongoing_contest_with_problem.id,
        "code": "b", "language": "Java"
    })

    assert response.status_code == 429
    assert response.get_json()["error"] == "submission_cooldown_ongoing"

# ========================================
# /api/contest/<id>/leaderboard
# ========================================

def test_leaderboard_shows_own_submissions_during_ongoing_contest(client, user_logged_in, ongoing_contest_with_problem, problems):
    profile = ContestProfile(user=user_logged_in, contest=ongoing_contest_with_problem)
    db.session.add(profile)
    db.session.commit()

    submission = Submission(
        problem=problems, contest_profile=profile, user=user_logged_in,
        status=Status.Accepted.value, code="print(1)", language="Java",
        submit_time=datetime.datetime.now(timezone.utc),
    )
    db.session.add(submission)
    db.session.commit()

    response = client.get(f"/api/contest/{ongoing_contest_with_problem.id}/leaderboard")
    data = response.get_json()

    assert response.status_code == 200
    entries = data["leaderboard"]
    assert len(entries) == 1
    assert entries[0]["user"] == user_logged_in.shallow_serialize()
    assert entries[0]["score"] > 0
    assert entries[0]["problemsSolved"][0][1] == 1

def test_contest_leaderboard_hidden_when_disabled(client, user_logged_in, ongoing_contest):
    ongoing_contest.show_leaderboard = False
    db.session.commit()

    response = client.get(f"/api/contest/{ongoing_contest.id}/leaderboard")
    assert response.status_code == 200
    assert response.get_json() == {}

def test_contest_leaderboard_hidden_when_upcoming(client, user_logged_in, upcoming_contest):
    response = client.get(f"/api/contest/{upcoming_contest.id}/leaderboard")
    assert response.status_code == 200
    assert response.get_json() == {}

def test_contest_leaderboard_excludes_profiles_with_no_valid_submissions(client, user_logged_in, ongoing_contest_with_problem):
    contest_profile = ContestProfile(user=user_logged_in, contest=ongoing_contest_with_problem)
    db.session.add(contest_profile)
    db.session.commit()

    response = client.get(f"/api/contest/{ongoing_contest_with_problem.id}/leaderboard")
    assert response.status_code == 200
    assert response.get_json()["leaderboard"] == []

def test_contest_leaderboard_contest_not_found(client, user_logged_in):
    response = client.get("/api/contest/999/leaderboard")
    assert response.status_code == 404
    assert response.get_json()["error"] == "contest_not_found"

# ========================================
# /api/contest/<id>/data
# ========================================

def test_contest_data_available_to_regular_user(client, user_logged_in, ongoing_contest, monkeypatch, tmp_path):
    monkeypatch.setattr("src.routes.contest.runtime_dir", str(tmp_path))
    monkeypatch.chdir(tmp_path)  # keeps dirname/zip creation from touching your real repo dir

    response = client.get(f"/api/contest/{ongoing_contest.id}/data")

    assert response.status_code == 200
    assert response.mimetype in ("application/zip", "application/octet-stream")

def test_contest_data_works_for_upcoming_and_past_too(client, user_logged_in, upcoming_contest, past_contest, monkeypatch, tmp_path):
    monkeypatch.setattr("src.routes.contest.runtime_dir", str(tmp_path))
    monkeypatch.chdir(tmp_path)

    for contest in (upcoming_contest, past_contest):
        response = client.get(f"/api/contest/{contest.id}/data")
        assert response.status_code == 200

def test_contest_data_not_found(client, user_logged_in):
    response = client.get("/api/contest/999/data")
    assert response.status_code == 404
    assert response.get_json()["error"] == "contest_not_found"

def test_contest_data_cleans_up_temp_files(client, user_logged_in, ongoing_contest, monkeypatch, tmp_path):
    monkeypatch.setattr("src.routes.contest.runtime_dir", str(tmp_path))
    monkeypatch.chdir(tmp_path)

    client.get(f"/api/contest/{ongoing_contest.id}/data")

    dirname = f"contest{ongoing_contest.id}-student-data"
    assert not os.path.exists(os.path.join(tmp_path, dirname))
    assert not os.path.exists(os.path.join(tmp_path, f"{dirname}.zip"))

def test_contest_data_includes_student_input_for_problems_that_have_it(client, user_logged_in, ongoing_contest_with_problem, problems, monkeypatch, tmp_path):
    monkeypatch.setattr("src.routes.contest.runtime_dir", str(tmp_path))
    monkeypatch.chdir(tmp_path)

    response = client.get(f"/api/contest/{ongoing_contest_with_problem.id}/data")
    assert response.status_code == 200

    import zipfile, io
    with zipfile.ZipFile(io.BytesIO(response.data)) as z:
        assert "A.dat" in z.namelist()
        assert z.read("A.dat").decode() == "1\n2\n3"

def test_contest_data_empty_input_file_name_returns_empty_zip(client, user_logged_in, ongoing_contest_with_problem, problems, monkeypatch, tmp_path):
    problems.student_input = "some input"
    problems.input_file_name = None
    db.session.commit()

    monkeypatch.setattr("src.routes.contest.runtime_dir", str(tmp_path))
    monkeypatch.chdir(tmp_path)

    response = client.get(f"/api/contest/{ongoing_contest_with_problem.id}/data")
    assert response.status_code == 200

    import zipfile, io
    with zipfile.ZipFile(io.BytesIO(response.data)) as z:
        assert len(z.namelist()) == 0

def test_contest_data_empty_input_returns_empty_zip(client, user_logged_in, ongoing_contest_with_problem, problems, monkeypatch, tmp_path):
    problems.student_input = ""
    problems.input_file_name = "input.dat"
    db.session.commit()

    monkeypatch.setattr("src.routes.contest.runtime_dir", str(tmp_path))
    monkeypatch.chdir(tmp_path)

    response = client.get(f"/api/contest/{ongoing_contest_with_problem.id}/data")
    assert response.status_code == 200

    import zipfile, io
    with zipfile.ZipFile(io.BytesIO(response.data)) as z:
        assert len(z.namelist()) == 0

# ========================================
# /api/admin/contests
# ========================================

def test_admin_contests_list_success(client, admin_logged_in, ongoing_contest, past_contest, upcoming_contest):
    response = client.get("/api/admin/contests")
    names = [c["name"] for c in response.get_json()["contests"]]
    assert response.status_code == 200
    assert ongoing_contest.name in names
    assert past_contest.name in names
    assert upcoming_contest.name in names

def test_admin_contests_list_empty(client, admin_logged_in):
    response = client.get("/api/admin/contests")
    names = [c["name"] for c in response.get_json()["contests"]]
    assert response.status_code == 200
    assert len(names) == 0

# ========================================
# /api/admin/contest/<id>
# ========================================

def test_admin_contest_success(client, admin_logged_in, upcoming_contest):
    response = client.get("/api/admin/contest/1")
    assert response.status_code == 200
    assert response.get_json()["contest"] == upcoming_contest.serialize()

def test_admin_contest_not_found(client, admin_logged_in):
    response = client.get("/api/admin/contest/999")
    assert response.status_code == 404
    assert response.get_json()["error"] == "contest_not_found"

# ========================================
# /api/admin/contest/<id>/add/problem
# ========================================

def test_admin_contest_add_problem_success(client, admin_logged_in, ongoing_contest, problems):
    response = client.post(f"/api/admin/contest/{ongoing_contest.id}/add/problem", json={
        "psetName": problems.pset.name, "problemName": problems.name
    })
    assert response.status_code == 204
    assert problems in ongoing_contest.problems()

def test_admin_contest_add_problem_pset_not_found(client, admin_logged_in):
    response = client.post(f"/api/admin/contest/999/add/problem")
    assert response.status_code == 404
    assert response.get_json()["error"] == "contest_not_found"

def test_admin_contest_add_problem_pset_not_found(client, admin_logged_in, ongoing_contest):
    response = client.post(f"/api/admin/contest/{ongoing_contest.id}/add/problem", json={
        "psetName": "Nonexistent", "problemName": "x"
    })
    assert response.status_code == 404
    assert response.get_json()["error"] == "pset_not_found"

def test_admin_contest_add_problem_pset_not_found(client, admin_logged_in, ongoing_contest, problems):
    response = client.post(f"/api/admin/contest/{ongoing_contest.id}/add/problem", json={
        "psetName": problems.pset.name, "problemName": "x"
    })
    assert response.status_code == 404
    assert response.get_json()["error"] == "problem_not_found"

def test_admin_contest_add_problem_already_linked(client, admin_logged_in, ongoing_contest_with_problem, problems):
    response = client.post(f"/api/admin/contest/{ongoing_contest_with_problem.id}/add/problem", json={
        "psetName": problems.pset.name, "problemName": problems.name
    })
    assert response.status_code == 400
    assert response.get_json()["error"] == "problem_already_linked"

# ========================================
# /api/admin/contest/<id>/add/pset
# ========================================

def test_admin_contest_add_pset_success(client, admin_logged_in, ongoing_contest, problems):
    response = client.post(f"/api/admin/contest/{ongoing_contest.id}/add/pset", json={
        "psetName": problems.pset.name
    })
    assert response.status_code == 204
    assert problems in ongoing_contest.problems()

def test_admin_contest_add_pset_pset_not_found(client, admin_logged_in, ongoing_contest, problems):
    response = client.post(f"/api/admin/contest/{ongoing_contest.id}/add/pset", json={
        "psetName": "Nonexistent"
    })
    assert response.status_code == 404
    assert response.get_json()["error"] == "pset_not_found"

def test_admin_contest_add_pset_contest_not_found(client, admin_logged_in, problems):
    response = client.post("/api/admin/contest/999/add/pset", json={
        "psetName": problems.pset.name
    })
    assert response.status_code == 404
    assert response.get_json()["error"] == "contest_not_found"

# ========================================
# /api/admin/contest/unlinkproblem
# ========================================

def test_admin_contest_unlink_problem_success(client, admin_logged_in, ongoing_contest_with_problem, problems):
    response = client.post("/api/admin/contest/unlinkproblem", json={
        "contestID": ongoing_contest_with_problem.id, "problemID": problems.id
    })
    assert response.status_code == 204
    assert problems not in ongoing_contest_with_problem.problems()

def test_admin_contest_unlink_problem_contest_not_found(client, admin_logged_in):
    response = client.post("/api/admin/contest/unlinkproblem", json={
        "contestID": 1, "problemID": 1
    })
    assert response.status_code == 404
    assert response.get_json()["error"] == "contest_not_found"

def test_admin_contest_unlink_problem_contest_not_found(client, admin_logged_in, ongoing_contest):
    response = client.post("/api/admin/contest/unlinkproblem", json={
        "contestID": ongoing_contest.id, "problemID": 1
    })
    assert response.status_code == 404
    assert response.get_json()["error"] == "problem_not_found"

def test_admin_contest_unlink_problem_not_linked(client, admin_logged_in, ongoing_contest, problems):
    response = client.post("/api/admin/contest/unlinkproblem", json={
        "contestID": ongoing_contest.id, "problemID": problems.id
    })
    assert response.status_code == 400
    assert response.get_json()["error"] == "problem_not_linked"

# ========================================
# /api/admin/contest/update
# ========================================

def test_admin_update_contest_success(client, admin_logged_in, ongoing_contest):
    response = client.post("/api/admin/contest/update", json={
        "id": ongoing_contest.id,
        "name": "Renamed Contest",
        "startTime": "2026-01-01T00:00:00",
        "endTime": "2026-01-02T00:00:00",
        "showPdf": True,
        "showLeaderboard": False,
        "allowedLanguages": "Python Java",
    })
    assert response.status_code == 204
    assert response.get_json() is None

    db.session.refresh(ongoing_contest)
    assert ongoing_contest.name == "Renamed Contest"
    assert ongoing_contest.show_pdf is True
    assert ongoing_contest.show_leaderboard is False

@pytest.mark.parametrize("name", [
    ("AB"),
    ("ABCDEFGHIJKLMNOPQRSTUVQXYZABCDEFGHIJKLMNOPQRSTUVQXY")
])
def test_admin_update_contest_invalid_name(client, admin_logged_in, ongoing_contest, name):
    response = client.post("/api/admin/contest/update", json={
        "id": ongoing_contest.id, "name": name,
        "startTime": "2026-01-01T00:00:00", "endTime": "2026-01-02T00:00:00",
        "showPdf": False, "showLeaderboard": True, "allowedLanguages": "Java",
    })
    assert response.status_code == 400
    assert response.get_json()["error"] == "invalid_name"

def test_admin_update_contest_name_exists(client, admin_logged_in, ongoing_contest, past_contest):
    response = client.post("/api/admin/contest/update", json={
        "id": ongoing_contest.id, "name": past_contest.name,
        "startTime": "2026-01-01T00:00:00", "endTime": "2026-01-02T00:00:00",
        "showPdf": False, "showLeaderboard": True, "allowedLanguages": "Java",
    })
    assert response.status_code == 409
    assert response.get_json()["error"] == "contest_exists"

# ========================================
# /api/admin/contest/add
# ========================================

def test_admin_add_contest_success(client, admin_logged_in):
    response = client.post("/api/admin/contest/add", json={
        "name": "New Contest",
        "startTime": "2026-01-01T00:00:00",
        "endTime": "2026-01-02T00:00:00",
    })
    assert response.status_code == 201
    assert response.get_json() is None
    assert db.session.query(Contest).filter_by(name="New Contest").first() is not None

@pytest.mark.parametrize("name", [
    ("AB"),
    ("ABCDEFGHIJKLMNOPQRSTUVQXYZABCDEFGHIJKLMNOPQRSTUVQXY")
])
def test_admin_add_contest_invalid_name(client, admin_logged_in, name):
    response = client.post("/api/admin/contest/add", json={
        "name": name, "startTime": "2026-01-01T00:00:00", "endTime": "2026-01-02T00:00:00",
    })
    assert response.status_code == 400
    assert response.get_json()["error"] == "invalid_name"

def test_admin_add_contest_exists(client, admin_logged_in, ongoing_contest):
    response = client.post("/api/admin/contest/add", json={
        "name": ongoing_contest.name, "startTime": "2026-01-01T00:00:00", "endTime": "2026-01-02T00:00:00",
    })
    assert response.status_code == 409
    assert response.get_json()["error"] == "contest_exists"

# ========================================
# /api/admin/contest/updateproblems
# ========================================

def test_admin_contest_update_problems_success(client, admin_logged_in, ongoing_contest_with_problem, problems):
    response = client.post("/api/admin/contest/updateproblems", json={
        "contestID": ongoing_contest_with_problem.id,
        "problems": [{
            "problem": {"id": problems.id},
            "correctScore": 100,
            "incorrectPenalty": 10,
            "gradingTimeout": 3.0,
        }],
    })
    assert response.status_code == 204
    assert response.get_json() is None

    link = db.session.query(ContestProblemAssociation).filter_by(
        contest_id=ongoing_contest_with_problem.id, problem_id=problems.id
    ).first()
    assert link.correct_score == 100
    assert link.incorrect_penalty == 10

@pytest.mark.parametrize("correct_score,incorrect_penalty",[
    ("not_a_number", 10),
    (10, "not_a_number"),
    ("not_a_number", "not_a_number")
])
def test_admin_contest_update_problems_invalid_scoring(client, admin_logged_in, ongoing_contest_with_problem, problems, correct_score, incorrect_penalty):
    response = client.post("/api/admin/contest/updateproblems", json={
        "contestID": ongoing_contest_with_problem.id,
        "problems": [{
            "problem": {"id": problems.id},
            "correctScore": correct_score,
            "incorrectPenalty": incorrect_penalty,
            "gradingTimeout": 3.0,
        }],
    })
    assert response.status_code == 400
    assert response.get_json()["error"] == "invalid_scoring"

def test_admin_contest_update_problems_invalid_timeout(client, admin_logged_in, ongoing_contest_with_problem, problems):
    response = client.post("/api/admin/contest/updateproblems", json={
        "contestID": ongoing_contest_with_problem.id,
        "problems": [{
            "problem": {"id": problems.id},
            "correctScore": 60,
            "incorrectPenalty": 5,
            "gradingTimeout": -1.0,
        }],
    })
    assert response.status_code == 400
    assert response.get_json()["error"] == "invalid_timeout"

def test_admin_contest_update_problems_contest_not_found(client, admin_logged_in):
    response = client.post("/api/admin/contest/updateproblems", json={
        "contestID": 999, "problems": [],
    })
    assert response.status_code == 404
    assert response.get_json()["error"] == "contest_not_found"