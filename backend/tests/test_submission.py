import threading

from tests.utils import *
from src.models.orm import *
from src.judge import Status

# ========================================
# /api/submission/<id>
# ========================================

def test_submission_not_found(client, user_logged_in):
    response = client.get("/api/submission/999")

    assert response.status_code == 404
    assert response.get_json()["error"] == "submission_not_found"

def test_submission_other_users_ongoing_contest_submission_forbidden(client, user_logged_in, ongoing_contest_with_problem, problems):
    other_user = User(username="other", password_hash="x", is_admin=False)
    db.session.add(other_user)
    db.session.commit()
    profile = ContestProfile(user=other_user, contest=ongoing_contest_with_problem)
    db.session.add(profile)
    db.session.commit()

    submission = make_submission(other_user, problems, contest_profile=profile)
    response = client.get(f"/api/submission/{submission.id}")

    assert response.status_code == 403
    assert response.get_json()["error"] == "submission_view_restricted"

def test_submission_own_ongoing_contest_submission_hides_io(client, user_logged_in, ongoing_contest_with_problem, problems):
    profile = ContestProfile(user=user_logged_in, contest=ongoing_contest_with_problem)
    db.session.add(profile)
    db.session.commit()

    submission = make_submission(user_logged_in, problems, contest_profile=profile)
    response = client.get(f"/api/submission/{submission.id}")
    data = response.get_json()["submission"]

    assert response.status_code == 200
    assert "output" not in data
    assert "judgeInput" not in data
    assert "judgeOutput" not in data
    assert "code" in data

def test_submission_past_contest_visible_to_other_users_with_io(client, user_logged_in, past_contest, problems):
    other_user = User(username="other", password_hash="x", is_admin=False)
    db.session.add(other_user)
    db.session.commit()
    profile = ContestProfile(user=other_user, contest=past_contest)
    db.session.add(profile)
    db.session.commit()

    submission = make_submission(other_user, problems, contest_profile=profile)
    response = client.get(f"/api/submission/{submission.id}")
    data = response.get_json()["submission"]

    assert response.status_code == 200
    assert "output" in data
    assert "judgeInput" in data
    assert "judgeOutput" in data
    assert "code" in data

def test_submission_own_upcoming_contest_submission_accessible(client, user_logged_in, upcoming_contest, problems):
    profile = ContestProfile(user=user_logged_in, contest=upcoming_contest)
    db.session.add(profile)
    db.session.commit()

    submission = make_submission(user_logged_in, problems, contest_profile=profile)
    response = client.get(f"/api/submission/{submission.id}")

    assert response.status_code == 200
    data = response.get_json()["submission"]
    assert "output" not in data  # not past -> io still hidden
    assert "judgeInput" not in data
    assert "judgeOutput" not in data
    assert "code" in data

def test_submission_other_users_upcoming_contest_submission_forbidden(client, user_logged_in, upcoming_contest, problems):
    other_user = User(username="other", password_hash="x", is_admin=False)
    db.session.add(other_user)
    db.session.commit()
    profile = ContestProfile(user=other_user, contest=upcoming_contest)
    db.session.add(profile)
    db.session.commit()

    submission = make_submission(other_user, problems, contest_profile=profile)
    response = client.get(f"/api/submission/{submission.id}")

    assert response.status_code == 403
    assert response.get_json()["error"] == "submission_view_restricted"

def test_submission_admin_sees_io_on_ongoing_contest_submission(client, user_logged_in, admin_logged_in, ongoing_contest_with_problem, problems):
    profile = ContestProfile(user=user_logged_in, contest=ongoing_contest_with_problem)
    db.session.add(profile)
    db.session.commit()

    submission = make_submission(user_logged_in, problems, contest_profile=profile)
    response = client.get(f"/api/submission/{submission.id}")
    data = response.get_json()["submission"]

    assert response.status_code == 200
    assert "output" in data
    assert "judgeInput" in data
    assert "judgeOutput" in data
    assert "code" in data

def test_submission_admin_sees_io_on_upcoming_contest_submission(client, user_logged_in, admin_logged_in, upcoming_contest_with_problem, problems):
    profile = ContestProfile(user=user_logged_in, contest=upcoming_contest_with_problem)
    db.session.add(profile)
    db.session.commit()

    submission = make_submission(user_logged_in, problems, contest_profile=profile)
    response = client.get(f"/api/submission/{submission.id}")
    data = response.get_json()["submission"]

    assert response.status_code == 200
    assert "output" in data
    assert "judgeInput" in data
    assert "judgeOutput" in data
    assert "code" in data

def test_submission_invalid_returns_not_found(client, user_logged_in, problems, monkeypatch):
    submission = make_submission(user_logged_in, problems)
    monkeypatch.setattr(Submission, "valid", lambda self: False)

    response = client.get(f"/api/submission/{submission.id}")

    assert response.status_code == 404
    assert response.get_json()["error"] == "submission_not_found"

# ========================================
# /api/submission/<int:id>/stream
# ========================================

def test_stream_submission_not_found(client, user_logged_in):
    response = client.get("/api/submission/999999/stream")
    body = response.get_data(as_text=True)
    assert "event: error" in body
    assert "submission_not_found" in body

def test_stream_returns_verdict_when_event_already_set(client, user_logged_in, ongoing_contest_with_problem, problems, monkeypatch):
    profile = ContestProfile(user=user_logged_in, contest=ongoing_contest_with_problem)
    db.session.add(profile)
    db.session.commit()
    submission = make_submission(user_logged_in, problems, contest_profile=profile)

    fake_event = threading.Event()
    fake_event.set()
    monkeypatch.setattr("src.routes.submission.get_submission_event", lambda id: fake_event)
    monkeypatch.setattr("src.routes.submission.delete_submission_event", lambda id: None)

    response = client.get(f"/api/submission/{submission.id}/stream")
    body = response.get_data(as_text=True)

    assert "event: done" in body
    assert problems.name in body

def test_stream_judge_error_when_submission_removed_during_wait(client, user_logged_in, problems, monkeypatch):
    submission = make_submission(user_logged_in, problems, status=Status.Pending.value)
    submission_id = submission.id

    fake_event = threading.Event()

    def fake_wait(timeout=None):
        sub = db.session.get(Submission, submission_id)
        db.session.delete(sub)
        db.session.commit()
        return True

    fake_event.wait = fake_wait
    monkeypatch.setattr("src.routes.submission.get_submission_event", lambda id: fake_event)
    monkeypatch.setattr("src.routes.submission.delete_submission_event", lambda id: None)

    response = client.get(f"/api/submission/{submission_id}/stream")
    body = response.get_data(as_text=True)

    assert "event: error" in body
    assert "judge_error" in body

# ========================================
# /api/admin/submissions/<page>
# ========================================

def test_admin_submissions_paged_basic(client, user_logged_in, admin_logged_in, problems):
    for _ in range(3):
        make_submission(user_logged_in, problems)

    response = client.get("/api/admin/submissions/1")
    assert response.status_code == 200
    assert len(response.get_json()["submissions"]) == 3

def test_admin_submissions_paged_respects_page_size_and_order(client, user_logged_in, admin_logged_in, problems):
    submissions = [make_submission(user_logged_in, problems) for _ in range(55)]

    response1 = client.get("/api/admin/submissions/1")
    page1 = response1.get_json()["submissions"]

    response2 = client.get("/api/admin/submissions/2")
    page2 = response2.get_json()["submissions"]

    assert len(page1) == 50
    assert len(page2) == 5
    assert page1[0]["id"] == submissions[-1].id

def test_admin_submissions_paged_empty_page(client, admin_logged_in):
    response = client.get("/api/admin/submissions/1")
    assert response.status_code == 200
    assert response.get_json()["submissions"] == []

# ========================================
# /api/admin/submission/<id>/delete
# ========================================

def test_admin_submission_delete_success(client, user_logged_in, admin_logged_in, problems):
    submission = make_submission(user_logged_in, problems)
    response = client.delete(f"/api/admin/submission/{submission.id}/delete")

    assert response.status_code == 204
    assert response.get_json() is None
    assert db.session.get(Submission, submission.id) is None

def test_admin_submission_delete_not_found(client, admin_logged_in):
    response = client.delete("/api/admin/submission/999/delete")
    assert response.status_code == 404
    assert response.get_json()["error"] == "submission_not_found"

# ========================================
# /api/admin/submission/<id>/regrade
# ========================================

def test_admin_submission_regrade_success(client, user_logged_in, admin_logged_in, problems, monkeypatch):
    submission = make_submission(user_logged_in, problems)

    calls = []
    monkeypatch.setattr(
        "src.routes.submission.enqueue_submission",
        lambda submission_id, regrade=False: calls.append((submission_id, regrade))
    )

    response = client.post(f"/api/admin/submission/{submission.id}/regrade")

    assert response.status_code == 204
    assert response.get_json() is None
    assert len(calls) == 1
    assert calls[0][1] is True

def test_admin_submission_regrade_success(client, admin_logged_in, monkeypatch):
    calls = []
    monkeypatch.setattr(
        "src.routes.submission.enqueue_submission",
        lambda submission_id, regrade=False: calls.append((submission_id, regrade))
    )

    response = client.post(f"/api/admin/submission/999/regrade")

    assert response.status_code == 404
    assert response.get_json()["error"] == "submission_not_found"
    assert len(calls) == 0