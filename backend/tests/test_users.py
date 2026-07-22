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
    

def test_user_logged_in_data(client, user_logged_in):
    response = client.get("/api/user")

    assert response.status_code == 200
    assert response.get_json()["user"]["username"] == user_logged_in.username 
    assert response.get_json()["user"]["id"] == user_logged_in.id