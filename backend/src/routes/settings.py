import flask
import flask_login

from src.app import app
from src.models.orm import *
from src.utils import log, admin_required

@app.route("/api/admin/settings")
@admin_required
def admin_settings():
    """Returns JSON data for the current configuration of the site-wide settings"""

    settings = db.session.query(Settings).all()
    out = {}
    for setting in settings:
        if setting.key == "docker_grading":
            out[setting.key] = setting.value.lower() == "true"

    return {"settings": out}

@app.route("/api/admin/settings/update", methods=["POST"])
@admin_required
def admin_update_settings():
    """Updates the site-wide settings with new values"""

    request = flask.request.get_json()
    for key, value in request.items():
        if key != "docker_grading":
            continue
        setting = db.session.query(Settings).filter_by(key=key).first()
        if setting:
            setting.value = "true" if value else "false"
            db.session.add(setting)
    db.session.commit()

    log.info(f"Site-wide settings updated by {flask_login.current_user.username}")

    return "", 204