import pytest

from src.models.orm import *

# ========================================
# /api/admin/settings
# ========================================

def test_settings_success(client, admin_logged_in, settings):
    response = client.get("/api/admin/settings")

    assert response.status_code == 200
    assert response.get_json()["settings"]["docker_grading"] == Settings.docker_grading_enabled()

# ========================================
# /api/admin/settings/update
# ========================================

@pytest.mark.parametrize("map,expected",[
    ({"docker_grading": True}, True),
    ({"docker_grading": False}, False),
    ({"docker_grading": "adfakldfj;lk", "abcdef": "cxnvmmxcvmnxc"}, True),
    ({}, False)
])
def test_settings_update_success(client, admin_logged_in, settings, map, expected):
    response = client.post("/api/admin/settings/update", json=map)

    assert response.status_code == 204
    assert response.get_json() is None
    assert Settings.docker_grading_enabled() == expected