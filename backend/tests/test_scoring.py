from tests.utils import *
from src.models.orm import *
from src.judge import Status

# ========================================
# calculate_score — no submissions
# ========================================

def test_score_zero_with_no_submissions(user_logged_in, ongoing_contest_with_problem):
    profile = make_profile(user_logged_in, ongoing_contest_with_problem)
    assert profile.calculate_score() == 0
    assert profile.score == 0

def test_score_zero_with_no_linked_problems(user_logged_in, ongoing_contest):
    profile = make_profile(user_logged_in, ongoing_contest)
    assert profile.calculate_score() == 0


# ========================================
# calculate_score — single correct submission
# ========================================

def test_score_one_correct_submission(user_logged_in, ongoing_contest_with_problem, problems):
    profile = make_profile(user_logged_in, ongoing_contest_with_problem)
    link = ongoing_contest_with_problem.problem_links[0]

    make_submission(user_logged_in, problems, profile, Status.Accepted.value)

    assert profile.calculate_score() == link.correct_score

def test_score_duplicate_correct_submissions_count_once(user_logged_in, ongoing_contest_with_problem, problems):
    """Solving the same problem twice shouldn't double the awarded score."""
    profile = make_profile(user_logged_in, ongoing_contest_with_problem)
    link = ongoing_contest_with_problem.problem_links[0]

    make_submission(user_logged_in, problems, profile, Status.Accepted.value, minutes_ago=5)
    make_submission(user_logged_in, problems, profile, Status.Accepted.value, minutes_ago=1)

    assert profile.calculate_score() == link.correct_score


# ========================================
# calculate_score — incorrect-only submissions
# ========================================

def test_score_unsolved_problem_incurs_no_penalty(user_logged_in, ongoing_contest_with_problem, problems):
    """
    Documents the behavior implied by `if problem_status[1] > 0:` guarding both
    the score addition AND the penalty subtraction: wrong answers on a problem
    that is never eventually solved contribute NOTHING to the score, positive
    or negative. Only solved problems' wrong attempts count against you.
    """
    profile = make_profile(user_logged_in, ongoing_contest_with_problem)

    make_submission(user_logged_in, problems, profile, Status.WrongAnswer.value)
    make_submission(user_logged_in, problems, profile, Status.WrongAnswer.value)

    assert profile.calculate_score() == 0

def test_score_solved_after_wrong_attempts_applies_penalty(user_logged_in, ongoing_contest_with_problem, problems):
    profile = make_profile(user_logged_in, ongoing_contest_with_problem)
    link = ongoing_contest_with_problem.problem_links[0]

    make_submission(user_logged_in, problems, profile, Status.WrongAnswer.value, minutes_ago=10)
    make_submission(user_logged_in, problems, profile, Status.WrongAnswer.value, minutes_ago=5)
    make_submission(user_logged_in, problems, profile, Status.Accepted.value, minutes_ago=1)

    expected = link.correct_score - (2 * link.incorrect_penalty)
    assert profile.calculate_score() == expected


# ========================================
# calculate_score — non-counting statuses
# ========================================

def test_score_pending_submissions_are_ignored(user_logged_in, ongoing_contest_with_problem, problems):
    profile = make_profile(user_logged_in, ongoing_contest_with_problem)

    make_submission(user_logged_in, problems, profile, Status.Pending.value)

    status_list = profile.problem_status_list()
    assert status_list[0][1] == 0  # correct count
    assert status_list[0][2] == 0  # incorrect count
    assert profile.calculate_score() == 0

def test_score_server_error_submissions_are_ignored(user_logged_in, ongoing_contest_with_problem, problems):
    profile = make_profile(user_logged_in, ongoing_contest_with_problem)

    make_submission(user_logged_in, problems, profile, Status.ErrorServer.value)

    status_list = profile.problem_status_list()
    assert status_list[0][1] == 0
    assert status_list[0][2] == 0

def test_score_compile_and_runtime_and_tle_all_count_as_incorrect(user_logged_in, ongoing_contest_with_problem, problems):
    """
    Everything except Pending(0) and ErrorServer(6) counts toward the incorrect
    tally per `elif submission.status != 0 and submission.status != 6`.
    """
    profile = make_profile(user_logged_in, ongoing_contest_with_problem)

    make_submission(user_logged_in, problems, profile, Status.ErrorCompile.value)
    make_submission(user_logged_in, problems, profile, Status.ErrorRuntime.value)
    make_submission(user_logged_in, problems, profile, Status.TimeLimitExceeded.value)

    status_list = profile.problem_status_list()
    assert status_list[0][2] == 3


# ========================================
# calculate_score — multiple problems
# ========================================

def test_score_sums_independently_across_problems(user_logged_in, ongoing_contest, psets):
    pset = db.session.get(ProblemSet, 1)
    problem_a = Problem(name="A", pset=pset, judge_output="", judge_input="")
    problem_b = Problem(name="B", pset=pset, judge_output="", judge_input="")
    db.session.add_all([problem_a, problem_b])
    db.session.commit()

    link_a = ContestProblemAssociation(contest=ongoing_contest, problem=problem_a, correct_score=60, incorrect_penalty=5)
    link_b = ContestProblemAssociation(contest=ongoing_contest, problem=problem_b, correct_score=100, incorrect_penalty=10)
    db.session.add_all([link_a, link_b])
    db.session.commit()

    profile = make_profile(user_logged_in, ongoing_contest)

    # Problem A: solved after 1 wrong attempt -> 60 - 5 = 55
    make_submission(user_logged_in, problem_a, profile, Status.WrongAnswer.value, minutes_ago=5)
    make_submission(user_logged_in, problem_a, profile, Status.Accepted.value, minutes_ago=1)

    # Problem B: never solved despite 2 wrong attempts -> contributes 0
    make_submission(user_logged_in, problem_b, profile, Status.WrongAnswer.value, minutes_ago=3)
    make_submission(user_logged_in, problem_b, profile, Status.WrongAnswer.value, minutes_ago=1)

    assert profile.calculate_score() == 55

def test_score_uses_correct_score_and_penalty_per_problem_link(user_logged_in, ongoing_contest, psets):
    """Different problems in the same contest can have different scoring parameters."""
    pset = db.session.get(ProblemSet, 1)
    problem_a = Problem(name="A", pset=pset, judge_output="", judge_input="")
    db.session.add(problem_a)
    db.session.commit()

    link = ContestProblemAssociation(contest=ongoing_contest, problem=problem_a, correct_score=200, incorrect_penalty=25)
    db.session.add(link)
    db.session.commit()

    profile = make_profile(user_logged_in, ongoing_contest)
    make_submission(user_logged_in, problem_a, profile, Status.Accepted.value)

    assert profile.calculate_score() == 200


# ========================================
# valid_submissions
# ========================================

def test_valid_submissions_excludes_submissions_to_unlinked_problems(user_logged_in, ongoing_contest, psets):
    pset = db.session.get(ProblemSet, 1)
    linked_problem = Problem(name="Linked", pset=pset, judge_output="", judge_input="")
    unlinked_problem = Problem(name="Unlinked", pset=pset, judge_output="", judge_input="")
    db.session.add_all([linked_problem, unlinked_problem])
    db.session.commit()

    link = ContestProblemAssociation(contest=ongoing_contest, problem=linked_problem)
    db.session.add(link)
    db.session.commit()

    profile = make_profile(user_logged_in, ongoing_contest)
    valid_sub = make_submission(user_logged_in, linked_problem, profile, Status.Accepted.value)
    make_submission(user_logged_in, unlinked_problem, profile, Status.Accepted.value)

    result_ids = [s.id for s in profile.valid_submissions()]
    assert result_ids == [valid_sub.id]

def test_valid_submissions_ordered_newest_first(user_logged_in, ongoing_contest_with_problem, problems):
    profile = make_profile(user_logged_in, ongoing_contest_with_problem)

    oldest = make_submission(user_logged_in, problems, profile, Status.WrongAnswer.value, minutes_ago=10)
    middle = make_submission(user_logged_in, problems, profile, Status.WrongAnswer.value, minutes_ago=5)
    newest = make_submission(user_logged_in, problems, profile, Status.Accepted.value, minutes_ago=0)

    result_ids = [s.id for s in profile.valid_submissions()]
    assert result_ids == [newest.id, middle.id, oldest.id]

def test_valid_submissions_unaffected_by_unlinking_after_submission(user_logged_in, ongoing_contest, psets):
    """
    If a problem is unlinked from a contest after a submission was made,
    that submission should no longer count as valid, since valid_submissions()
    filters against the CURRENT problem_links, not what existed at submit time.
    """
    pset = db.session.get(ProblemSet, 1)
    problem = Problem(name="A", pset=pset, judge_output="", judge_input="")
    db.session.add(problem)
    db.session.commit()

    link = ContestProblemAssociation(contest=ongoing_contest, problem=problem)
    db.session.add(link)
    db.session.commit()

    profile = make_profile(user_logged_in, ongoing_contest)
    submission = make_submission(user_logged_in, problem, profile, Status.Accepted.value)

    assert len(profile.valid_submissions()) == 1

    db.session.delete(link)
    db.session.commit()
    db.session.expire(ongoing_contest)

    assert len(profile.valid_submissions()) == 0


# ========================================
# problem_status_list — shape/structure
# ========================================

def test_problem_status_list_shape_with_no_submissions(user_logged_in, ongoing_contest_with_problem, problems):
    profile = make_profile(user_logged_in, ongoing_contest_with_problem)
    link = ongoing_contest_with_problem.problem_links[0]

    status_list = profile.problem_status_list()

    assert len(status_list) == 1
    assert status_list[0] == [problems.id, 0, 0, link.correct_score, link.incorrect_penalty]

def test_problem_status_list_one_entry_per_linked_problem(user_logged_in, ongoing_contest, psets):
    pset = db.session.get(ProblemSet, 1)
    problem_a = Problem(name="A", pset=pset, judge_output="", judge_input="")
    problem_b = Problem(name="B", pset=pset, judge_output="", judge_input="")
    db.session.add_all([problem_a, problem_b])
    db.session.commit()

    db.session.add_all([
        ContestProblemAssociation(contest=ongoing_contest, problem=problem_a),
        ContestProblemAssociation(contest=ongoing_contest, problem=problem_b),
    ])
    db.session.commit()

    profile = make_profile(user_logged_in, ongoing_contest)
    assert len(profile.problem_status_list()) == 2


# ========================================
# serialize / shallow_serialize
# ========================================

def test_shallow_serialize_shape(user_logged_in, ongoing_contest_with_problem):
    profile = make_profile(user_logged_in, ongoing_contest_with_problem)
    data = profile.shallow_serialize()

    assert data["id"] == profile.id
    assert data["score"] == profile.score
    assert data["user"] == user_logged_in.shallow_serialize()
    assert data["contest"] == ongoing_contest_with_problem.shallow_serialize()
    assert "submissions" not in data

def test_serialize_includes_valid_submissions(user_logged_in, ongoing_contest_with_problem, problems):
    profile = make_profile(user_logged_in, ongoing_contest_with_problem)
    submission = make_submission(user_logged_in, problems, profile, Status.Accepted.value)

    data = profile.serialize()

    assert len(data["submissions"]) == 1
    assert data["submissions"][0]["id"] == submission.id