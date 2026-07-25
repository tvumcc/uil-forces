from src.models.orm import *

# ========================================
# /api/admin/settings
# ========================================

def test_settings_success(client, admin_logged_in, settings):
    response = client.get("/api/admin/settings")

    assert response.status_code == 200
    assert response.get_json()["settings"]["docker_grading"] == Settings.docker_grading_enabled()

def test_settings_requires_admin(client, user_logged_in, settings):
    response = client.get("/api/admin/settings")

    assert response.status_code == 403
    assert response.get_json()["error"] == "not_admin"

# ========================================
# /api/admin/settings/update
# ========================================

def test_settings_update_success_1(client, admin_logged_in, settings):
    response = client.post("/api/admin/settings/update", json={
        "docker_grading": True
    })

    assert response.status_code == 204
    assert Settings.docker_grading_enabled() == True
    
def test_settings_update_success_2(client, admin_logged_in, settings):
    response = client.post("/api/admin/settings/update", json={
        "docker_grading": False
    })

    assert response.status_code == 204
    assert Settings.docker_grading_enabled() == False

def test_settings_update_garbage_becomes_true(client, admin_logged_in, settings):
    response = client.post("/api/admin/settings/update", json={
        "docker_grading": "adfakldfj;lk",
        "abcdef": "cxnvmmxcvmnxc"
    })

    assert response.status_code == 204
    assert Settings.docker_grading_enabled() == True

def test_settings_update_empty(client, admin_logged_in, settings):
    response = client.post("/api/admin/settings/update", json={})

    assert response.status_code == 204
    assert Settings.docker_grading_enabled() == False

def test_settings_update_requires_admin(client, user_logged_in, settings):
    response = client.post("/api/admin/settings/update", json={
        "docker_grading": True
    })

    assert response.status_code == 403
    assert response.get_json()["error"] == "not_admin"

def test_settings_update_requires_csrf(app, client, admin_logged_in, settings):
    app.config["WTF_CSRF_ENABLED"] = True

    response = client.post("/api/admin/settings/update", json={
        "docker_grading": True
    })

    assert response.status_code == 400
    assert response.get_json()["error"] == "csrf_invalid"