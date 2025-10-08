import flask
import flask_login

import threading
import datetime
from datetime import timezone

from main import app
from src.backend.orm import *
from src.backend.judge import Status, assign_status
from sqlalchemy import desc

@app.route("/api/contests")
@flask_login.login_required
def contests():
    contests = db.session.query(Contest).all()
    out = {
        "upcoming": [],
        "ongoing": [],
        "past": []
    }

    for contest in contests:
        contest_json = contest.shallow_serialize() 
        if contest.past():
            out["past"].append(contest_json)
        elif contest.ongoing():
            out["ongoing"].append(contest_json)
        elif contest.upcoming():
            out["upcoming"].append(contest_json)

    return out

@app.route("/api/contest/<id>")
@flask_login.login_required
def contest(id):
    contest = db.session.get(Contest, id)
    contest_profile = db.session.query(ContestProfile).filter_by(user=flask_login.current_user, contest=contest).first()
    if not contest_profile:
        contest_profile = ContestProfile(user=flask_login.current_user, contest=contest)
        db.session.add(contest_profile)
        db.session.commit()

    submissions = []
    if contest.past(): 
        for profile in contest.contest_profiles:
            submissions += profile.submissions
    elif contest.ongoing():
        submissions = db.session.query(Submission).filter_by(contest_profile=contest_profile).order_by(desc(Submission.submit_time)).all()
    else:
        return contest.shallow_serialize()

    return contest.serialize() | {
        "submissions": [submission.shallow_serialize() for submission in submissions]
    }

@app.route("/api/contest/submit", methods=["POST"])
@flask_login.login_required
def submit_contest_problem():
    response = flask.request.get_json()
    problem = db.session.get(Problem, response["problem_id"])
    contest = db.session.get(Contest, response["contest_id"])
    language = response["language"]
    if not problem:
        return {"message": "invalid problem id"}
    if not contest:
        return {"message": "invalid contest id"}
    if not contest.ongoing():
        return {"message": "contest is not ongoing, submissions are not allowed"}

    contest_profile = db.session.query(ContestProfile).filter_by(user=flask_login.current_user, contest=contest).first()
    if not contest_profile:
        contest_profile = ContestProfile(user=flask_login.current_user, contest=contest)
        db.session.add(contest_profile)
        db.session.commit()

    submission = Submission(
        problem=problem,
        contest_profile=contest_profile,
        user=flask_login.current_user,

        status=Status.Pending.value,
        code=response["code"],
        submit_time=datetime.datetime.now(timezone.utc),
        language=language
    )
    db.session.add(submission)
    db.session.commit()

    thread = threading.Thread(target=assign_status, args=[submission.id, contest_profile.id])
    thread.daemon = True
    thread.start()

    submissions = db.session.query(Submission).filter_by(contest_profile=contest_profile).order_by(desc(Submission.submit_time)).all()
    return {
        "estimated_wait" : 15,
        "submissions": [submission.shallow_serialize() for submission in submissions]
    }

@app.route("/api/contest/<id>/leaderboard")
@flask_login.login_required
def contest_leaderboard(id):
    contest: Contest = db.session.get(Contest, id)
    contest_profiles: List[ContestProfile] = sorted(contest.contest_profiles, key=lambda x: x.score, reverse=True)

    leaderboard = []
    for profile in contest_profiles:
        if len(profile.submissions) > 0:
            leaderboard_entry = {
                "user": profile.user.shallow_serialize(),
                "score": profile.score,
                "problems_solved": profile.problem_status_list()
            }
            leaderboard.append(leaderboard_entry)

    return {
        "leaderboard": leaderboard
    }

# Admin APIs

@app.route("/api/admin/contests")
@flask_login.login_required
def admin_contests():
    if not flask_login.current_user.is_admin:
        return flask.abort(400)
    return {"contests": [contest.shallow_serialize() for contest in db.session.query(Contest).all()]}

@app.route("/api/admin/contest/<id>")
@flask_login.login_required
def admin_contest(id):
    if not flask_login.current_user.is_admin:
        return flask.abort(400)
    contest = db.session.get(Contest, id)
    return {"contest": contest.serialize()}

@app.route("/api/admin/contest/<id>/add/problem", methods=["POST"])
@flask_login.login_required
def admin_contest_add_problem(id):
    if not flask_login.current_user.is_admin:
        return flask.abort(400)

    request = flask.request.get_json()
    pset_name = request["pset_name"]
    problem_name = request["problem_name"]

    contest = db.session.get(Contest, id)
    problem_set = db.session.query(ProblemSet).filter_by(name=pset_name).first()
    if problem_set is None:
        return flask.abort(400)

    problem = db.session.query(Problem).filter_by(problem_set=problem_set, name=problem_name).first()

    if problem is None:
        return flask.abort(400)

    for p in contest.problem_links:
        if p.problem == problem.id:
            return flask.abort(400)

    problem_link = ContestProblemAssociation(problem=problem)
    db.session.add(problem_link)

    contest.problem_links.append(problem_link)
    db.session.add(contest)
    db.session.commit()

    return flask.Response(status=200)

@app.route("/api/admin/contest/<id>/add/pset", methods=["POST"])
@flask_login.login_required
def admin_contest_add_pset(id):
    if not flask_login.current_user.is_admin:
        return flask.abort(400)

    request = flask.request.get_json()
    pset_name = request["pset_name"]

    contest = db.session.get(Contest, id)
    problem_set = db.session.query(ProblemSet).filter_by(name=pset_name).first()
    if problem_set is None:
        return flask.abort(400)

    for problem in problem_set.problems:
        if not problem in contest.problems():
            problem_link = ContestProblemAssociation(problem=problem)
            db.session.add(problem_link)
            contest.problem_links.append(problem_link)

    db.session.add(contest)
    db.session.commit()

    return flask.Response(status=200)

@app.route("/api/admin/contest/unlinkproblem", methods=["POST"])
@flask_login.login_required
def admin_contest_unlink_problem():
    if not flask_login.current_user.is_admin:
        return flask.abort(400)

    request = flask.request.get_json()
    contest_id = request["contest_id"]
    problem_id = request["problem_id"]

    contest: Contest = db.session.get(Contest, contest_id)
    problem = db.session.get(Problem, problem_id)

    if contest is None:
        return flask.abort(404)
    if problem is None:
        return flask.abort(404)

    try:
        problem_link_to_remove = None
        for problem_link in contest.problem_links:
            if problem_link.problem == problem:
                problem_link_to_remove = problem_link
                break

        contest.problem_links.remove(problem_link_to_remove)
        db.session.add(contest)
        db.session.commit()
    except ValueError:
        return flask.abort(400)

    return flask.Response(status=200)

@app.route("/api/admin/update/contest", methods=["POST"])
@flask_login.login_required
def admin_update_contest():
    if not flask_login.current_user.is_admin:
        return flask.abort(400)
    
    request = flask.request.get_json()
    id = request["id"]
    name = request["name"]
    start_time = request["start_time"]
    end_time = request["end_time"]

    contest = db.session.get(Contest, id)
    contest.name = name
    contest.start_time = datetime.datetime.fromisoformat(start_time)
    contest.end_time = datetime.datetime.fromisoformat(end_time)

    db.session.add(contest)
    db.session.commit()

    return flask.Response(status=200)

@app.route("/api/admin/add/contest", methods=["POST"])
@flask_login.login_required
def admin_add_contest():
    if not flask_login.current_user.is_admin:
        return flask.abort(400)
    
    request = flask.request.get_json()

    name = request["name"]
    start_time = datetime.datetime.fromisoformat(request["start_time"])
    end_time = datetime.datetime.fromisoformat(request["end_time"])

    db.session.add(Contest(
        name=name,
        start_time=start_time,
        end_time=end_time
    ))
    db.session.commit()

    return flask.Response(status=200)