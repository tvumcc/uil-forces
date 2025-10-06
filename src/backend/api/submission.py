import flask_login

from main import app
from src.backend.orm import *

@app.route("/api/submission/<id>")
@flask_login.login_required
def submission(id):
    submission = db.session.get(Submission, id)
    user = submission.user
    
    contest_profile = submission.contest_profile
    if contest_profile and not contest_profile.contest.past() and not user.is_admin and not user.id == flask_login.current_user.id:
        return {"message": "Submission cannot be viewed at this time"}

    return submission.serialize(admin_view=flask_login.current_user.is_admin)