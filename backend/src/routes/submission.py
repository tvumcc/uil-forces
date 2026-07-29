import flask
import flask_login

import json

from src.models.orm import *
from src.utils import log, admin_required
from src.judge import get_submission_event, delete_submission_event, enqueue_submission

bp = flask.Blueprint("submission", __name__)

@bp.route("/api/submission/<id>")
@flask_login.login_required
def submission(id):
    """
    Returns JSON data for the queried submission
    
    The submission's output, judge input, and judge output are hidden
    while the submission belongs to an ongoing or upcoming contest.
    
    If the submission belongs to an ongoing or upcoming contest,
    the submission cannot be accessed (even without the i/o) if the submission
    does not belong to the requesting user.
    """

    submission = db.session.get(Submission, id)
    if submission is None or not submission.valid():
        return {"error": "submission_not_found"}, 404

    contest_profile = submission.contest_profile
    past_contest = contest_profile and contest_profile.contest.is_past()

    if not past_contest \
        and not flask_login.current_user.is_admin \
        and flask_login.current_user != submission.user:
        return {"error": "submission_view_restricted"}, 403

    return {
        "submission": submission.serialize(admin_view=flask_login.current_user.is_admin)
    }

@bp.route("/api/submission/<int:id>/stream")
@flask_login.login_required
def submission_stream(id):
    @flask.stream_with_context
    def event_stream():
        submission = db.session.get(Submission, id)
        if submission is None:
            yield f"event: error\ndata: {json.dumps({"error": "submission_not_found"})}\n\n"
            return
        db.session.expire(submission)

        event = get_submission_event(id)
        event.wait(timeout=30)

        submission = db.session.get(Submission, id)
        if submission is None:
            yield f"event: error\ndata: {json.dumps({"error": "judge_error"})}\n\n"
            return

        yield f"event: done\ndata: {json.dumps({"problemName": submission.problem.name, "status": submission.status})}\n\n"

        delete_submission_event(id)

    return flask.Response(event_stream(), mimetype="text/event-stream")



# Admin API



@bp.route("/api/admin/submissions/<int:page>")
@admin_required
def admin_submissions_paged(page: int):
    """Returns a 1-indexed page out of all of the submissions in the database"""

    per_page = 50
    submissions = db.session.query(Submission).order_by(Submission.submit_time.desc()).limit(per_page).offset((int(page) - 1) * per_page).all()

    submissions_json = []
    for submission in submissions:
        if submission is not None and submission.valid():
            submissions_json.append(submission.shallow_serialize())

    return {
        "submissions": submissions_json
    }

@bp.route("/api/admin/submission/<int:id>/delete", methods=["DELETE"])
@admin_required
def admin_submission_delete(id: int):
    """Removes the specified submission from the database"""

    submission = db.session.get(Submission, id)
    if not submission:
        return {"error": "submission_not_found"}, 404

    db.session.delete(submission)
    db.session.commit()

    log.info(f"Submission {id} deleted by {flask_login.current_user.username}")

    return "", 204

@bp.route("/api/admin/submission/<int:id>/regrade", methods=["POST"])
@admin_required
def admin_submission_regrade(id: int):
    """Reruns the grader on the specified submission"""

    submission = db.session.get(Submission, id)
    if not submission:
        return {"error": "submission_not_found"}, 404

    enqueue_submission(id, regrade=True)

    log.info(f"Submission {id} regraded by {flask_login.current_user.username}")

    return "", 204