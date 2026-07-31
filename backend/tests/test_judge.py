import pytest

from tests.utils import *
from src.models.orm import *
from src.judge import *

@pytest.fixture
def judge_setup(client):
    db.session.add(Settings(key="docker_grading", value="false"))
    pset = ProblemSet(name="Problem Set")
    db.session.add(pset)
    db.session.commit()

    problem = Problem(
        name="Problem A", pset=pset, 
        use_stdin=False,
        input_file_name="A.dat",
        student_input="1\n2\n3",
        judge_input="1\n2\n3\n4",
        judge_output="10"
    )

    db.session.add(problem)
    pset.problems.append(problem)

    db.session.add(pset)
    db.session.commit()

    now = datetime.datetime.now(timezone.utc)
    contest = Contest(
        name="Contest",
        start_time=(now + datetime.timedelta(seconds=-3600)).replace(tzinfo=None),
        end_time=(now + datetime.timedelta(seconds=3600)).replace(tzinfo=None),

    )
    db.session.add(contest)
    db.session.commit()

    link = ContestProblemAssociation(contest=contest, problem=problem, grading_timeout=1.5)
    db.session.add(link)
    contest.problem_links.append(link)
    db.session.commit()

    user = User(
        username="test_user",
        password_hash="x",
        is_admin=False
    )
    db.session.add(user)
    db.session.commit()

    contest_profile = ContestProfile(
        contest=contest,
        user=user,
    )
    db.session.add(contest_profile)
    db.session.commit()
    return {
        "contest_profile": contest_profile,
        "user": user,
        "contest": contest,
        "problem": problem,
        "pset": pset,
        "link": link
    }

class JudgeTest:
    def __init__(self, language, expected_status, code, stdin=False):
        self.language = language
        self.expected_status = expected_status
        self.code = code
        self.stdin = stdin

judge_tests = [
    (JudgeTest("Python", Status.Accepted, "print(10)")),
    (JudgeTest("Python", Status.WrongAnswer, "print(9)")),
    (JudgeTest("Python", Status.TimeLimitExceeded, "while True: print(10)")),
    (JudgeTest("Python", Status.ErrorRuntime, "pint(10)")),
    (JudgeTest("Python", Status.Accepted, """with open("A.dat") as f: print(sum([int(line) for line in f.readlines()]))""")),
    (JudgeTest("Python", Status.ErrorRuntime, """with open("B.dat") as f: pass""")),
    (JudgeTest("Python", Status.Accepted, """import sys; print(sum([int(line) for line in sys.stdin.readlines()]))""", stdin=True)),
    (JudgeTest("Java", Status.Accepted, "public class A {public static void main(String[] args) {System.out.println(10);}}")),
    (JudgeTest("Java", Status.WrongAnswer, "public class A {public static void main(String[] args) {System.out.println(9);}}")),
    (JudgeTest("Java", Status.TimeLimitExceeded, "public class A {public static void main(String[] args) {while (true) {}}}")),
    (JudgeTest("Java", Status.ErrorRuntime, "public class A {public static void main(String[] args) throws Exception {throw new Exception();}}")),
    (JudgeTest("Java", Status.ErrorCompile, "public class A {public static void main(String[] args) {System.out.println(10)}}")),
    (JudgeTest("Java", Status.Accepted, """
        import java.util.*;
        import java.io.*;
        public class A {
            public static void main(String[] args) throws Exception {
                Scanner in = new Scanner(new File("A.dat"));
                int sum = 0;
                while (in.hasNextInt()) sum += in.nextInt();
                System.out.println(sum);
            }
        }
    """)),
    (JudgeTest("Java", Status.Accepted, """
        import java.util.*;
        public class A {
            public static void main(String[] args) throws Exception {
                Scanner in = new Scanner(System.in);
                int sum = 0;
                while (in.hasNextInt()) sum += in.nextInt();
                System.out.println(sum);
            }
        }
    """, stdin=True)),
]

@pytest.mark.parametrize("judge_test", judge_tests)
def test_judge_dockerless(app, judge_setup, judge_test, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    submission = make_submission(judge_setup["user"], judge_setup["problem"], contest_profile=judge_setup["contest_profile"], language=judge_test.language, status=Status.Pending.value, code=judge_test.code)

    use_docker = False
    assign_status(app, submission.id, False, use_docker, judge_test.stdin)

    event = get_submission_event(submission.id)
    event.wait(timeout=5)
    db.session.expire(submission)
    
    assert submission.status == judge_test.expected_status.value

@pytest.mark.docker
@pytest.mark.parametrize("judge_test", judge_tests)
def test_judge_docker(app, judge_setup, judge_test, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    submission = make_submission(judge_setup["user"], judge_setup["problem"], contest_profile=judge_setup["contest_profile"], language=judge_test.language, status=Status.Pending.value, code=judge_test.code)

    use_docker = True
    assign_status(app, submission.id, False, use_docker, judge_test.stdin)

    event = get_submission_event(submission.id)
    event.wait(timeout=5)
    db.session.expire(submission)
    
    assert submission.status == judge_test.expected_status.value

def test_dockerless_cleans_up_submission_dir(app, judge_setup, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    submission = make_submission(judge_setup["user"], judge_setup["problem"],
        contest_profile=judge_setup["contest_profile"], language="Python",
        status=Status.Pending.value, code="print(10)")

    assign_status(app, submission.id, False, False, False)
    event = get_submission_event(submission.id)
    event.wait(timeout=5)

    assert not os.path.exists(os.path.join(tmp_path, get_submission_folder_name(submission.id)))

def test_assign_status_skips_already_graded_without_regrade(app, judge_setup, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    submission = make_submission(judge_setup["user"], judge_setup["problem"],
        contest_profile=judge_setup["contest_profile"], language="Python",
        status=Status.Accepted.value, code="print(999)")

    assign_status(app, submission.id, False, False, False)
    db.session.expire(submission)

    assert submission.status == Status.Accepted.value  # unchanged — never re-graded

def test_assign_status_regrade_true_reruns_grading(app, judge_setup, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    submission = make_submission(judge_setup["user"], judge_setup["problem"],
        contest_profile=judge_setup["contest_profile"], language="Python",
        status=Status.Accepted.value, code="print(9)")

    assign_status(app, submission.id, True, False, False)
    event = get_submission_event(submission.id)
    event.wait(timeout=5)
    db.session.expire(submission)

    assert submission.status == Status.WrongAnswer.value

def test_assign_status_missing_link_does_not_crash(app, judge_setup, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    other_pset = ProblemSet(name="Other")
    db.session.add(other_pset)
    db.session.commit()
    unlinked_problem = Problem(name="Unlinked", pset=other_pset, judge_output="", judge_input="")
    db.session.add(unlinked_problem)
    db.session.commit()

    submission = make_submission(judge_setup["user"], unlinked_problem,
        contest_profile=judge_setup["contest_profile"], language="Python",
        status=Status.Pending.value, code="print(1)")

    assign_status(app, submission.id, False, False, False)
    db.session.expire(submission)

    assert submission.status == Status.Pending.value

def test_dockerless_unsupported_language_does_not_crash(app, judge_setup, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    submission = make_submission(judge_setup["user"], judge_setup["problem"],
        contest_profile=judge_setup["contest_profile"], language="C++",
        status=Status.Pending.value, code="int main(){}")

    assign_status(app, submission.id, False, False, False)
    event = get_submission_event(submission.id)
    event.wait(timeout=5)
    db.session.expire(submission)

    assert submission.status == Status.ErrorServer.value