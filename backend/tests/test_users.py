from src.models.orm import *
from werkzeug.security import generate_password_hash

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
    assert response.get_json() == None

def test_user_login_invalid_password(client):
    setup_test_user()

    response = client.post("/api/login", json={
        "username": "test_user",
        "password": "password1"
    })

    assert response.status_code == 400
    assert response.get_json()["error"] == "invalid_credentials"

def test_user_login_invalid_username(client):
    setup_test_user()

    response = client.post("/api/login", json={
        "username": "test_user1",
        "password": "password"
    })

    assert response.status_code == 400
    assert response.get_json()["error"] == "invalid_credentials"

def test_user_login_requires_csrf(app, client):
    setup_test_user()
    app.config["WTF_CSRF_ENABLED"] = True

    response = client.post("/api/login", json={
        "username": "test_user",
        "password": "password"
    })

    assert response.status_code == 400
    assert response.get_json()["error"] == "csrf_invalid"

# ========================================
# /api/logout
# ========================================

def test_user_logout(client, user_logged_in):
    response2 = client.get("/api/user")
    assert response2.status_code == 200
    assert response2.get_json()["user"] == user_logged_in.shallow_serialize()

    response1 = client.get("/api/logout")
    assert response1.status_code == 204

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

def test_user_register_invalid_username_symbols_and_whitespace(client):
    response = client.post("/api/register", json={
        "username": "test-use r?",
        "password": "password"
    })

    user = db.session.query(User).filter_by(username="test-user r?").first()

    assert user == None
    assert response.status_code == 400
    assert response.get_json()["error"] == "invalid_username"

def test_user_register_invalid_username_too_short(client):
    response = client.post("/api/register", json={
        "username": "ab",
        "password": "password"
    })

    user = db.session.query(User).filter_by(username="ab").first()

    assert user == None
    assert response.status_code == 400
    assert response.get_json()["error"] == "invalid_username"

def test_user_register_invalid_username_too_long(client):
    response = client.post("/api/register", json={
        "username": "abcdefghijklmnopqrstuvwxyz",
        "password": "password"
    })

    user = db.session.query(User).filter_by(username="abcdefghijklmnopqrstuvwxyz").first()

    assert user == None
    assert response.status_code == 400
    assert response.get_json()["error"] == "invalid_username"

def test_user_register_user_exists(client):
    setup_test_user()

    response = client.post("/api/register", json={
        "username": "test_user",
        "password": "password"
    })

    assert db.session.query(User).filter_by(username="test_user").count() == 1
    assert response.status_code == 409
    assert response.get_json()["error"] == "user_exists"

def test_user_register_requires_csrf(app, client):
    app.config["WTF_CSRF_ENABLED"] = True

    response = client.post("/api/register", json={
        "username": "test_user",
        "password": "password"
    })

    user = db.session.query(User).filter_by(username="test_user").first()

    assert user == None
    assert response.status_code == 400
    assert response.get_json()["error"] == "csrf_invalid"

# ========================================
# /api/user
# ========================================

def test_user_data_requires_login(client):
    response = client.get("/api/user")

    assert response.status_code == 401
    assert response.get_json()["error"] == "unauthorized"

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

def test_users_leaderboard_requires_login(client):
    response = client.get("/api/users/leaderboard")

    assert response.status_code == 401
    assert response.get_json()["error"] == "unauthorized"

def test_users_leaderboard_empty(client, user_logged_in):
    response = client.get("/api/users/leaderboard")

    assert response.status_code == 200

    ranks = response.get_json()
    assert len(ranks) == 1
    assert ranks[0]["user"] == user_logged_in.shallow_serialize()
    assert ranks[0]["problemsSolved"] == 0

# TODO: Write a test for /api/users/leaderboard with users who have actually solved prolems