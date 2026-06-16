import flask

from main import app
from src.backend.utils import user_required, admin_required

# Publicly accessible pages

@app.route("/login")
def login_page():
    return flask.send_from_directory(app.static_folder, "src/frontend/html/login.html")

@app.route("/register")
def register_page():
    return flask.send_from_directory(app.static_folder, "src/frontend/html/register.html")

# User accessible pages

@app.route("/")
@user_required
def index_page():
    return flask.send_from_directory(app.static_folder, "src/frontend/html/home.html")

@app.route("/contest")
@user_required
def contest_page():
    return flask.send_from_directory(app.static_folder, "src/frontend/html/contest.html")

@app.route("/contests")
@user_required
def contest_list_page():
    return flask.send_from_directory(app.static_folder, "src/frontend/html/contestList.html")

@app.route("/submission")
@user_required
def submission_page():
    return flask.send_from_directory(app.static_folder, "src/frontend/html/submission.html")

# Admin accessible pages

@app.route("/admin/users")
@admin_required
def admin_user_list_page():
    return flask.send_from_directory(app.static_folder, "src/frontend/html/adminUserList.html")

@app.route("/admin/contests")
@admin_required
def admin_contest_list_page():
    return flask.send_from_directory(app.static_folder, "src/frontend/html/adminContestList.html")

@app.route("/admin/contest")
@admin_required
def admin_contest_page():
    return flask.send_from_directory(app.static_folder, "src/frontend/html/adminContest.html")

@app.route("/admin/pset")
@admin_required
def admin_pset_page():
    return flask.send_from_directory(app.static_folder, "src/frontend/html/adminProblemSet.html")

@app.route("/admin/settings")
@admin_required
def admin_settings_page():
    return flask.send_from_directory(app.static_folder, "src/frontend/html/adminSettings.html")

@app.route("/admin/submissions")
@admin_required
def admin_submission_list_page():
    return flask.send_from_directory(app.static_folder, "src/frontend/html/adminSubmissionList.html")

@app.route("/admin/psets")
@admin_required
def admin_pset_list_page():
    return flask.send_from_directory(app.static_folder, "src/frontend/html/adminProblemSetList.html")

@app.route("/admin/problem")
@admin_required
def admin_problem_page():
    return flask.send_from_directory(app.static_folder, "src/frontend/html/adminProblem.html")

@app.route("/admin")
@admin_required
def admin_home_page():
    return flask.send_from_directory(app.static_folder, "src/frontend/html/adminHome.html")