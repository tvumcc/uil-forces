import flask
import flask_login
from sqlalchemy import desc

import threading
import datetime
from datetime import timezone
import os
import shutil

from src.app import app
from src.models.orm import *
from src.judge import Status, enqueue_submission 
from src.utils import admin_required, valid_name

@app.route("/api/contests")
@flask_login.login_required
def contests():
    """Returns JSON of 3 lists of contests: upcoming, ongoing, and past, all based on their start and end times"""

    out = {
        "upcoming": [],
        "ongoing": [],
        "past": []
    }

    for contest in db.session.query(Contest).all():
        contest_json = contest.shallow_serialize()
        match contest_json["status"]:
            case "past": out["past"].append(contest_json)
            case "ongoing": out["ongoing"].append(contest_json)
            case "upcoming": out["upcoming"].append(contest_json)

    return out

@app.route("/api/contest/<id>")
@flask_login.login_required
def contest(id):
    """
    Returns JSON data for the specfied contest depending on if it is upcoming, ongoing, or past
    This also creates a new contest profile for the requesting user if they do not already have a contest profile associated with the contest
    """

    contest = db.session.get(Contest, id)
    if not contest:
        return {"error": "contest_not_found"}, 404
    contest_profile = db.session.query(ContestProfile).filter_by(user=flask_login.current_user, contest=contest).first()
    if not contest_profile:
        contest_profile = ContestProfile(user=flask_login.current_user, contest=contest)
        db.session.add(contest_profile)
        db.session.commit()

    submissions = []
    if contest.is_past(): 
        for profile in contest.contest_profiles:
            submissions += profile.valid_submissions()
    elif contest.is_ongoing():
        submissions = contest_profile.valid_submissions()
    else:
        return {"contest": contest.shallow_serialize()}

    return {
        "contest": contest.serialize() | {
            "submissions": [submission.shallow_serialize() for submission in sorted(submissions, key=lambda submission: submission.submit_time, reverse=True)]
        }
    }

@app.route("/api/contest/submit", methods=["POST"])
@flask_login.login_required
def submit_contest_problem():
    """
    Processes a user's request to submit code to a problem in this contest.
    This will create a new submission on the database and spawn another thread to run and assign a status to it.

    Whether the submission is ran using a local interpreter/compiler or a Docker container is based on the
    site-wide setting 'docker_grading'

    The client will continue to poll every 1 second `estimated_wait` times to check if a new status has been assigned to the submission.
    """

    request = flask.request.get_json()
    problem = db.session.get(Problem, request["problemID"])
    contest = db.session.get(Contest, request["contestID"])
    language = request["language"]

    if not problem:
        return {"error": "problem_not_found"}, 404
    if not contest:
        return {"error": "contest_not_found"}, 404
    if not contest.is_ongoing():
        return {"error": "contest_not_ongoing"}, 403
    if language not in contest.allowed_languages.split(" "):
        return {"error": "invalid_language"}, 400

    contest_profile = db.session.query(ContestProfile).filter_by(user=flask_login.current_user, contest=contest).first()
    if not contest_profile:
        contest_profile = ContestProfile(user=flask_login.current_user, contest=contest)
        db.session.add(contest_profile)
        db.session.commit()

    submission_cooldown_seconds = 5
    latest_submission = db.session.query(Submission).filter_by(user=flask_login.current_user).order_by(desc(Submission.submit_time)).first()

    if latest_submission is not None:
        last_time = latest_submission.submit_time.replace(tzinfo=timezone.utc)
        curr_time = datetime.datetime.now(timezone.utc)
        if (curr_time - last_time).total_seconds() <= submission_cooldown_seconds:
            return {"error": "submission_cooldown_ongoing"}, 429

    submission = Submission(
        problem=problem,
        contest_profile=contest_profile,
        user=flask_login.current_user,

        status=Status.Pending.value,
        code=request["code"],
        submit_time=datetime.datetime.now(timezone.utc),
        language=language
    )
    db.session.add(submission)
    db.session.commit()

    enqueue_submission(submission.id, contest_profile.id)

    return {"submission": submission.shallow_serialize()}

@app.route("/api/contest/<id>/leaderboard")
@flask_login.login_required
def contest_leaderboard(id):
    """Returns the current leaderboard for this contest as long as the setting is enabled to show leaderboard and the contest is ongoing or past"""

    contest = db.session.get(Contest, id)
    if not contest:
        return {"error": "contest_not_found"}, 404

    if contest.show_leaderboard and not contest.is_upcoming():
        contest_profiles = sorted(contest.contest_profiles, key=lambda x: x.score, reverse=True)

        leaderboard = []
        for profile in contest_profiles:
            profile.calculate_score()
            db.session.add(profile)

            if len(profile.valid_submissions()) > 0:
                leaderboard_entry = {
                    "user": profile.user.shallow_serialize(),
                    "score": profile.score,
                    "problemsSolved": profile.problem_status_list()
                }
                leaderboard.append(leaderboard_entry)

        db.session.commit()

        return {"leaderboard": leaderboard}
    else: return {}

@app.route("/api/contest/<id>/data")
@flask_login.login_required
def contest_data(id):
    contest = db.session.get(Contest, id)
    if not contest:
        return {"error": "contest_not_found"}, 404

    try:
        dirname = f"contest{contest.id}-student-data"
        os.mkdir(dirname)

        for problem in contest.problems():
            if len(problem.student_input) > 0:
                with open(os.path.join(dirname, problem.input_file_name), "w") as f:
                    f.write(problem.student_input)

        shutil.make_archive(dirname, "zip", dirname)
        return flask.send_file(f"{dirname}.zip")
    finally:
        try:
            shutil.rmtree(dirname)
            os.remove(f"{dirname}.zip")
        except: pass



# Admin API



@app.route("/api/admin/contests")
@admin_required
def admin_contests():
    """Returns a list of all contests (upcoming, ongoing, past) contained within the database"""

    return {"contests": [contest.shallow_serialize() for contest in db.session.query(Contest).all()]}

@app.route("/api/admin/contest/<id>")
@admin_required
def admin_contest(id):
    """Returns JSON data for the queried contest"""

    contest = db.session.get(Contest, id)
    if not contest:
        return {"error": "contest_not_found"}, 404

    return {"contest": contest.serialize()}

@app.route("/api/admin/contest/<id>/add/problem", methods=["POST"])
@admin_required
def admin_contest_add_problem(id):
    """Creates a link between and an existing problem and the specified contest"""

    request = flask.request.get_json()
    pset_name = request["psetName"]
    problem_name = request["problemName"]

    contest = db.session.get(Contest, id)
    pset = db.session.query(ProblemSet).filter_by(name=pset_name).first()
    if not contest:
        return {"error": "contest_not_found"}, 404
    if not pset:
        return {"error": "pset_not_found"}, 404
    problem = db.session.query(Problem).filter_by(pset=pset, name=problem_name).first()
    if not problem:
        return {"error": "problem_not_found"}, 404

    for p in contest.problem_links:
        if p.problem == problem:
            return {"error": "problem_already_linked"}, 400

    problem_link = ContestProblemAssociation(problem=problem)
    db.session.add(problem_link)

    contest.problem_links.append(problem_link)
    db.session.add(contest)
    db.session.commit()

    return "", 204

@app.route("/api/admin/contest/<id>/add/pset", methods=["POST"])
@admin_required
def admin_contest_add_pset(id):
    """Creates a link between all of the problems in a problem set and the specified contest"""

    request = flask.request.get_json()
    pset_name = request["psetName"]

    contest = db.session.get(Contest, id)
    pset = db.session.query(ProblemSet).filter_by(name=pset_name).first()
    if not pset:
        return {"error": "pset_not_found"}, 404

    for problem in pset.problems:
        if not problem in contest.problems():
            problem_link = ContestProblemAssociation(problem=problem)
            db.session.add(problem_link)
            contest.problem_links.append(problem_link)

    db.session.add(contest)
    db.session.commit()

    return "", 204

@app.route("/api/admin/contest/unlinkproblem", methods=["POST"])
@admin_required
def admin_contest_unlink_problem():
    """Removes the link between the specified contest and problem"""

    request = flask.request.get_json()
    contest_id = request["contestID"]
    problem_id = request["problemID"]

    contest = db.session.get(Contest, contest_id)
    problem = db.session.get(Problem, problem_id)

    if not contest:
        return {"error": "contest_not_found"}, 404
    if not problem:
        return {"error": "problem_not_found"}, 404

    problem_link_to_remove = None
    for problem_link in contest.problem_links:
        if problem_link.problem == problem:
            problem_link_to_remove = problem_link
            break

    if not problem_link_to_remove:
        return {"error": "problem_not_linked"}, 400

    db.session.delete(problem_link_to_remove)
    db.session.add(contest)
    db.session.commit()

    return "", 204

@app.route("/api/admin/update/contest", methods=["POST"])
@admin_required
def admin_update_contest():
    """Updates the specified contest with the provided new values"""
    
    request = flask.request.get_json()
    id = request["id"]
    name = request["name"]
    start_time = request["startTime"]
    end_time = request["endTime"]
    show_pdf = request["showPdf"]
    show_leaderboard = request["showLeaderboard"]
    allowed_languages = " ".join(str(request["allowedLanguages"]).split())

    contest = db.session.get(Contest, id)

    if not valid_name(name):
        return {"error": "invalid_name"}, 400
    if contest.name != name and db.session.query(Contest).filter_by(name=name).first() is not None:
        return {"error": "contest_exists"}, 409

    contest.name = name
    contest.start_time = datetime.datetime.fromisoformat(start_time)
    contest.end_time = datetime.datetime.fromisoformat(end_time)
    contest.show_pdf = show_pdf
    contest.show_leaderboard = show_leaderboard
    contest.allowed_languages = allowed_languages

    db.session.add(contest)
    db.session.commit()

    return "", 204

@app.route("/api/admin/add/contest", methods=["POST"])
@admin_required
def admin_add_contest():
    """Creates a new contest with a name, start time, and end time"""
    
    request = flask.request.get_json()

    name = request["name"]
    start_time = datetime.datetime.fromisoformat(request["startTime"])
    end_time = datetime.datetime.fromisoformat(request["endTime"])

    if not valid_name(name):
        return {"error": "invalid_name"}, 400
    if db.session.query(Contest).filter_by(name=name).first() is not None:
        return {"error": "contest_exists"}, 409

    contest = Contest(
        name=name,
        start_time=start_time,
        end_time=end_time
    )
    db.session.add(contest)
    db.session.commit()

    return "", 201

@app.route("/api/admin/contest/updateproblems", methods=["POST"])
@admin_required
def admin_update_contest_problems():
    """Updates the scoring of the specified contest's problems and refreshes all contest profiles' scores accordingly"""
    
    request = flask.request.get_json()
    contest_id = request["contestID"]
    problems = request["problems"]

    contest: Contest = db.session.get(Contest, contest_id)
    if not contest:
        return {"error": "contest_not_found"}, 404

    for problem in problems:
        problem_link = db.session.query(ContestProblemAssociation).filter_by(contest_id=contest.id, problem_id=problem["problem"]["id"]).first()
        if problem_link:
            try:
                problem_link.correct_score = int(problem["correctScore"])
                problem_link.incorrect_penalty = int(problem["incorrectPenalty"])
            except:
                return {"error": "invalid_scoring"}, 400

            try:
                problem_link.grading_timeout = float(problem["gradingTimeout"])
                if problem_link.grading_timeout <= 0.0: raise
            except:
                return {"error": "invalid_timeout"}, 400

            db.session.add(problem_link)

    for contest_profile in contest.contest_profiles:
        contest_profile.calculate_score()
        db.session.add(contest_profile)

    db.session.commit()

    return "", 204