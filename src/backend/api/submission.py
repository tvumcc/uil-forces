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

    practice_site = Settings.practice_site_enabled()
    submission = db.session.get(Submission, id)
    if not submission:
        flask.abort(404, description="Submission does not exist")

    pset = submission.problem.problem_set
    user = submission.user
    contest_profile = submission.contest_profile
    is_past_contest = contest_profile and not contest_profile.contest.past()

    if is_past_contest \
        and not flask_login.current_user.is_admin \
        and flask_login.current_user != user:
        flask.abort(403, description="Submission cannot be viewed at this time")

    if not flask_login.current_user.is_admin and \
        (practice_site and pset and pset.hide or is_past_contest):
        return submission.shallow_serialize()

    return {
        "submission": submission.serialize(admin_view=flask_login.current_user.is_admin)
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
    if len(submissions) == 0:
        flask.abort(400)

    return {
        "submissions": [submission.shallow_serialize() for submission in submissions]
    }

@app.route("/api/admin/submission/<id>/delete", methods=["DELETE"])
@flask_login.login_required
def admin_submission_delete(id):
    """Removes the specified submission from the database, updating contest scores accordingly"""

    if not flask_login.current_user.is_admin:
        flask.abort(403)

    submission = db.session.get(Submission, id)
    if not submission:
        return flask.abort(404, description="Submission does not exist")

    if submission.contest_profile:
        submission.contest_profile.calculate_score()
        db.session.add(submission.contest_profile)

    db.session.delete(submission)
    db.session.commit()

    log.info(f"Submission {id} deleted by {flask_login.current_user.username}")

    return f"Successfully deleted submission {id}"