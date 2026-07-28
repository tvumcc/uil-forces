import pytest
from werkzeug.security import generate_password_hash

from src.app import create_app
from src.models.orm import *

@pytest.fixture
def app():
    app = create_app({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
    })
    with app.app_context():
        db.create_all()
        yield app 
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def user_logged_in(client):
    user = User(
        username="test_user",
        password_hash=generate_password_hash("password"),
        is_admin=False
    )
    db.session.add(user)
    db.session.commit()

    with client.session_transaction() as sess:
        sess["_user_id"] = str(user.id)
        sess["_fresh"] = True

    return user

@pytest.fixture
def admin_logged_in(client):
    admin = User(
        username="test_admin",
        password_hash=generate_password_hash("password"),
        is_admin=True
    )
    db.session.add(admin)
    db.session.commit()

    with client.session_transaction() as sess:
        sess["_user_id"] = str(admin.id)
        sess["_fresh"] = True

    return admin 

@pytest.fixture
def psets():
    psetA = ProblemSet(name="Problem Set A")
    psetB = ProblemSet(name="Problem Set B")
    psetC = ProblemSet(name="Problem Set C")

    db.session.add(psetA)
    db.session.add(psetB)
    db.session.add(psetC)
    db.session.commit()

@pytest.fixture
def problems(psets):
    pset = db.session.get(ProblemSet, 1)
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
    return problem

def make_contest(name, start_offset, end_offset, **kwargs):
    now = datetime.datetime.now(timezone.utc)
    contest = Contest(
        name=name,
        start_time=(now + datetime.timedelta(seconds=start_offset)).replace(tzinfo=None),
        end_time=(now + datetime.timedelta(seconds=end_offset)).replace(tzinfo=None),
        **kwargs,
    )
    db.session.add(contest)
    db.session.commit()
    return contest

@pytest.fixture
def ongoing_contest():
    return make_contest("Ongoing Contest", start_offset=-3600, end_offset=3600)

@pytest.fixture
def upcoming_contest():
    return make_contest("Upcoming Contest", start_offset=3600, end_offset=7200)

@pytest.fixture
def past_contest():
    return make_contest("Past Contest", start_offset=-7200, end_offset=-3600)

@pytest.fixture
def ongoing_contest_with_problem(ongoing_contest, problems):
    link = ContestProblemAssociation(contest=ongoing_contest, problem=problems)
    db.session.add(link)
    ongoing_contest.problem_links.append(link)
    db.session.commit()
    return ongoing_contest

@pytest.fixture
def past_contest_with_problem(past_contest, problems):
    link = ContestProblemAssociation(contest=past_contest, problem=problems)
    db.session.add(link)
    past_contest.problem_links.append(link)
    db.session.commit()
    return past_contest 

@pytest.fixture
def settings():
    db.session.add(Settings(key="docker_grading", value="false"))
    db.session.commit()
    db.session.close()