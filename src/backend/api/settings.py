import flask
import flask_login

from main import app
from src.backend.orm import *
from src.backend.log import log

@app.route("/api/admin/settings")
@flask_login.login_required
def admin_settings():
    """Returns JSON data for the current configuration of the site-wide settings"""

    if not flask_login.current_user.is_admin:
        flask.abort(403)

    settings = db.session.query(Settings).all()
    out = {}
    for setting in settings:
        match setting.key:
            case "practice_site" | "docker_grading":
                out[setting.key] = True if setting.value.lower() == "true" else False

    return {"settings": out}

@app.route("/api/admin/update/settings", methods=["POST"])
@flask_login.login_required
def admin_update_settings():
    """Updates the site-wide settings with new values"""

    if not flask_login.current_user.is_admin:
        flask.abort(403)

    request = flask.request.get_json()
    for key, value in request.items():
        setting = db.session.query(Settings).filter_by(key=key).first()
        if setting:
            match key:
                case "practice_site" | "docker_grading":
                    setting.value = "true" if value else "false"
            db.session.add(setting)
    db.session.commit()

    log.info(f"Site-wide settings updated by {flask_login.current_user.username}")

    return "Successfully updated site-wide settings"