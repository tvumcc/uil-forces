from src.models.orm import *
from werkzeug.security import generate_password_hash
import pytest

def setup_test_user():
    user = User(
        username="test_user",
        password_hash=generate_password_hash("password"),
        is_admin=False
    )
    db.session.add(user)
    db.session.commit()

# ========================================
# /api/login
# ========================================

def test_user_login_success(client):
    setup_test_user()

    response = client.post("/api/login", json={
        "username": "test_user",
        "password": "password"
    })

    assert response.status_code == 204
    assert response.get_json() is None

@pytest.mark.parametrize("username,password", [
    ("test_user","password1"),
    ("test_user1","password"),
    ("test_user1","password1"),
])
def test_user_login_invalid_credentials(client, username, password):
    setup_test_user()

    response = client.post("/api/login", json={
        "username": username,
        "password": password
    })

    assert response.status_code == 400
    assert response.get_json()["error"] == "invalid_credentials"

# ========================================
# /api/logout
# ========================================

def test_user_logout_success(client, user_logged_in):
    response2 = client.get("/api/user")
    assert response2.status_code == 200
    assert response2.get_json()["user"] == user_logged_in.shallow_serialize()

    response1 = client.get("/api/logout")
    assert response1.status_code == 204
    assert response1.get_json() is None

    response2 = client.get("/api/user")
    assert response2.status_code == 401
    assert response2.get_json()["error"] == "unauthorized"
    
# ========================================
# /api/register
# ========================================

def test_user_register_success(client):
    response = client.post("/api/register", json={
        "username": "test_user",
        "password": "password"
    })

    user = db.session.query(User).filter_by(username="test_user").first()
    
    assert response.status_code == 201
    assert user.username == "test_user"
    assert user.is_admin == False

@pytest.mark.parametrize("username", [
    ("AB"),
    ("ABCDEFGHIJKLMNOPQRSTUVWXYZABCDEFGHIJKLMNOPQRSTUVWXY"),
    ("test-use r?"),
])
def test_user_register_invalid_name(client, username):
    response = client.post("/api/register", json={
        "username": username,
        "password": "password"
    })

    user = db.session.query(User).filter_by(username=username).first()

    assert user is None
    assert response.status_code == 400
    assert response.get_json()["error"] == "invalid_username"

def test_user_register_user_exists(client):
    setup_test_user()

    response = client.post("/api/register", json={
        "username": "test_user",
        "password": "password"
    })

    user_count = db.session.query(User).filter_by(username="test_user").count()

    assert user_count == 1
    assert response.status_code == 409
    assert response.get_json()["error"] == "user_exists"

# ========================================
# /api/user
# ========================================

def test_user_data_user_logged_in(client, user_logged_in):
    response = client.get("/api/user")

    assert response.status_code == 200
    assert response.get_json()["user"]["username"] == user_logged_in.username 
    assert response.get_json()["user"]["id"] == user_logged_in.id
    assert response.get_json()["user"]["isAdmin"] == user_logged_in.is_admin

def test_user_data_admin_logged_in(client, admin_logged_in):
    response = client.get("/api/user")

    assert response.status_code == 200
    assert response.get_json()["user"]["username"] == admin_logged_in.username 
    assert response.get_json()["user"]["id"] == admin_logged_in.id
    assert response.get_json()["user"]["isAdmin"] == admin_logged_in.is_admin

# ========================================
# /api/users/leaderboard
# ========================================

def test_users_leaderboard_one_user(client, user_logged_in):
    response = client.get("/api/users/leaderboard")

    assert response.status_code == 200

    ranks = response.get_json()
    assert len(ranks) == 1
    assert ranks[0]["user"] == user_logged_in.shallow_serialize()
    assert ranks[0]["problemsSolved"] == 0

# TODO: Write a test for /api/users/leaderboard with users who have actually solved prolems

# ========================================
# /api/admin/users
# ========================================

def test_user_list_success(client, admin_logged_in):
    user1 = User(
        username="user1",
        password_hash=generate_password_hash("password"),
        is_admin=False
    )
    db.session.add(user1)
    db.session.commit()

    response = client.get("/api/admin/users")

    users = response.get_json()["users"]

    assert response.status_code == 200
    assert users[0] == admin_logged_in.shallow_serialize()
    assert users[1] == user1.shallow_serialize()

# ========================================
# /api/admin/user/add
# ========================================

def test_user_add_success(client, admin_logged_in):
    response = client.post("/api/admin/user/add", json={
        "username": "user",
        "password": "password",
        "isAdmin": False
    })

    user = db.session.query(User).filter_by(username="user").first()

    assert user.username == "user"
    assert user.is_admin == False
    assert response.status_code == 201

@pytest.mark.parametrize("username", [
    ("AB"),
    ("ABCDEFGHIJKLMNOPQRSTUVWXYZABCDEFGHIJKLMNOPQRSTUVWXY"),
    ("test-use r?")
])
def test_user_add_invalid_username(client, admin_logged_in, username):
    response = client.post("/api/admin/user/add", json={
        "username": username,
        "password": "password",
        "isAdmin": False
    })

    user = db.session.query(User).filter_by(username=username).first()

    assert user is None
    assert response.status_code == 400
    assert response.get_json()["error"] == "invalid_username"

def test_user_add_user_exists(client, admin_logged_in):
    response = client.post("/api/admin/user/add", json={
        "username": "test_admin",
        "password": "password",
        "isAdmin": False
    })

    user_count = db.session.query(User).filter_by(username="test_admin").count()

    assert user_count == 1
    assert response.status_code == 409
    assert response.get_json()["error"] == "user_exists"