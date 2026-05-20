import flask
import flask_login

from main import app
from src.backend.orm import *
from src.backend.log import log

@app.route("/api/submission/<id>")
@flask_login.login_required
def submission(id):
    """
    Returns JSON data for the queried submission
    
    The submission's output, judge input, and judge output can potentially
    be hidden based on multiple factors:
    - if both the practice site and associated ProblemSet are hidden
    - or if the submission belongs to an ongoing or upcoming contest
    
    If the submission belongs to an ongoing or upcoming contest,
    the submission cannot be accessed (even without the i/o) if the submission
    does not belong to the requesting user.
    """

    submission = db.session.get(Submission, id)
    if submission is None or not submission.valid():
        flask.abort(404, description="Submission does not exist")

    user = submission.user
    contest_profile = submission.contest_profile
    past_contest = contest_profile and contest_profile.contest.past()

    if not past_contest \
        and not flask_login.current_user.is_admin \
        and flask_login.current_user != user:
        flask.abort(403, description="Submission cannot be viewed at this time")

    return {
        "submission": submission.serialize(user=user, admin_view=flask_login.current_user.is_admin)
    }



# Admin API



@app.route("/api/admin/submissions/<page>")
@flask_login.login_required
def admin_submissions_paged(page):
    """Returns a 1-indexed page out of all of the submissions in the database"""

    if not flask_login.current_user.is_admin: 
        flask.abort(403)

    per_page = 20
    submissions = db.session.query(Submission).order_by(Submission.submit_time.desc()).limit(per_page).offset((int(page) - 1) * per_page).all()

    submissions_json = []
    for submission in submissions:
        if submission is not None and submission.valid():
            submissions_json.append(submission.shallow_serialize())

    return {
        "submissions": submissions_json
    }

@app.route("/api/admin/submission/<id>/delete", methods=["DELETE"])
@flask_login.login_required
def admin_submission_delete(id):
    """Removes the specified submission from the database"""

    if not flask_login.current_user.is_admin:
        flask.abort(403)

    submission = db.session.get(Submission, id)
    if not submission:
        return flask.abort(404, description="Submission does not exist")

    db.session.delete(submission)
    db.session.commit()

    log.info(f"Submission {id} deleted by {flask_login.current_user.username}")

    return f"Successfully deleted submission {id}"