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