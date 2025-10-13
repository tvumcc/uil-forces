import flask
import flask_login

from main import app

# Publicly accessible pages
@app.route("/login")
def login_page():
    return flask.send_from_directory(app.static_folder, "src/frontend/html/login.html")

@app.route("/register")
def register_page():
    return flask.send_from_directory(app.static_folder, "src/frontend/html/register.html")

# User accessible pages
@app.route("/")
@flask_login.login_required
def index_page():
    return flask.send_from_directory(app.static_folder, "src/frontend/html/home.html")

@app.route("/contest")
@flask_login.login_required
def contest_page():
    return flask.send_from_directory(app.static_folder, "src/frontend/html/contest.html")

@app.route("/contests")
@flask_login.login_required
def contest_list_page():
    return flask.send_from_directory(app.static_folder, "src/frontend/html/contestList.html")

@app.route("/submission")
@flask_login.login_required
def submission_page():
    return flask.send_from_directory(app.static_folder, "src/frontend/html/submission.html")

@app.route("/pset")
@flask_login.login_required
def pset_page():
    return flask.send_from_directory(app.static_folder, "src/frontend/html/problemSet.html")

@app.route("/psets")
@flask_login.login_required
def pset_list_page():
    return flask.send_from_directory(app.static_folder, "src/frontend/html/problemSetList.html")

# Admin accessible pages
@app.route("/admin/users")
@flask_login.login_required
def admin_user_list_page():
    if not flask_login.current_user.is_admin:
        return flask.abort(400)
    return flask.send_from_directory(app.static_folder, "src/frontend/html/adminUserList.html")

@app.route("/admin/contests")
@flask_login.login_required
def admin_contest_list_page():
    if not flask_login.current_user.is_admin:
        return flask.abort(400)
    return flask.send_from_directory(app.static_folder, "src/frontend/html/adminContestList.html")

@app.route("/admin/contest")
@flask_login.login_required
def admin_contest_page():
    if not flask_login.current_user.is_admin:
        return flask.abort(400)
    return flask.send_from_directory(app.static_folder, "src/frontend/html/adminContest.html")

@app.route("/admin/pset")
@flask_login.login_required
def admin_pset_page():
    if not flask_login.current_user.is_admin:
        return flask.abort(400)
    return flask.send_from_directory(app.static_folder, "src/frontend/html/adminProblemSet.html")

@app.route("/admin/settings")
@flask_login.login_required
def admin_settings_page():
    if not flask_login.current_user.is_admin:
        return flask.abort(400)
    return flask.send_from_directory(app.static_folder, "src/frontend/html/adminSettings.html")

@app.route("/admin/submissions")
@flask_login.login_required
def admin_submission_list_page():
    if not flask_login.current_user.is_admin:
        return flask.abort(400)
    return flask.send_from_directory(app.static_folder, "src/frontend/html/adminSubmissionList.html")

@app.route("/admin/psets")
@flask_login.login_required
def admin_pset_list_page():
    if not flask_login.current_user.is_admin:
        return flask.abort(400)
    return flask.send_from_directory(app.static_folder, "src/frontend/html/adminProblemSetList.html")

@app.route("/admin/problem")
@flask_login.login_required
def admin_problem_page():
    if not flask_login.current_user.is_admin:
        return flask.abort(400)
    return flask.send_from_directory(app.static_folder, "src/frontend/html/adminProblem.html")

@app.route("/admin")
@flask_login.login_required
def admin_home_page():
    if not flask_login.current_user.is_admin:
        return flask.abort(400)
    return flask.send_from_directory(app.static_folder, "src/frontend/html/adminHome.html")