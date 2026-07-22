import pytest
from werkzeug.security import generate_password_hash

from src.app import app as flask_app
from src.models.orm import *

class TestigConfig:
    TESTING = True
    WTF_CSRF_ENABLED = False

@pytest.fixture
def app():
    flask_app.config.update({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
    })
    with flask_app.app_context():
        db.create_all()
        yield flask_app
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