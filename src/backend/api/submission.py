import flask
import flask_login

from main import app
from src.backend.orm import *

@app.route("/api/submission/<id>")
@flask_login.login_required
def submission(id):
    submission = db.session.get(Submission, id)
    settings = db.session.query(Settings).filter_by(key="practice_site").first()
    pset = submission.problem.problem_set if submission else None
    user = submission.user
    
    contest_profile = submission.contest_profile

    if settings and settings.value.lower() == "true" and pset and pset.hide or contest_profile and not contest_profile.contest.past() and not flask_login.current_user.is_admin and not user.id == flask_login.current_user.id:
        return submission.shallow_serialize()

    return submission.serialize(admin_view=flask_login.current_user.is_admin)

@app.route("/api/admin/submissions/<page>")
@flask_login.login_required
def admin_submissions_paged(page):
    if not flask_login.current_user.is_admin:
        return flask.abort(400)

    submissions = db.session.query(Submission).order_by(Submission.submit_time.desc()).limit(20).offset((int(page) - 1) * 20).all()
    return {
        "submissions": [submission.shallow_serialize() for submission in submissions]
    }

@app.route("/api/admin/submission/<id>/delete", methods=["DELETE"])
@flask_login.login_required
def admin_submission_delete(id):
    if not flask_login.current_user.is_admin:
        return flask.abort(400)

    submission = db.session.get(Submission, id)
    if not submission:
        return flask.Response(status=404)

    if submission.contest_profile:
        submission.contest_profile.calculate_score()
        db.session.add(submission.contest_profile)

    db.session.delete(submission)
    db.session.commit()
    return flask.Response(status=200)