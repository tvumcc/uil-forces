import pytest

LOGIN_REQUIRED_ROUTES = [
    # Contest
    ("GET", "/api/contests"),
    ("GET", "/api/contest/1"),
    ("POST", "/api/contest/submit"),
    ("GET", "/api/contest/1/leaderboard"),
    ("GET", "/api/contest/1/data"),
    ("GET", "/api/admin/contests"),
    ("GET", "/api/admin/contest/1"),
    ("POST", "/api/admin/contest/1/add/problem"),
    ("POST", "/api/admin/contest/1/add/pset"),
    ("POST", "/api/admin/contest/unlinkproblem"),
    ("POST", "/api/admin/contest/update"),
    ("POST", "/api/admin/contest/add"),
    ("POST", "/api/admin/contest/updateproblems"),

    # Problem
    ("GET", "/api/problem/1/pdf"),
    ("GET", "/api/admin/problem/1"),
    ("POST", "/api/admin/problem/update"),
    ("DELETE", "/api/admin/problem/1/delete"),

    # Problem Set
    ("GET", "/api/admin/psets"),
    ("GET", "/api/admin/pset/1"),
    ("POST", "/api/admin/pset/update"),
    ("POST", "/api/admin/pset/add"),
    ("POST", "/api/admin/pset/add/problem"),
    ("GET", "/api/admin/pset/1/pdf"),
    ("POST", "/api/admin/pset/1/uploadpdf"),

    # Settings
    ("GET", "/api/admin/settings"),
    ("POST", "/api/admin/settings/update"),

    # Submission
    ("GET", "/api/submission/1"),
    ("GET", "/api/submission/1/stream"),
    ("GET", "/api/admin/submissions/1"),
    ("DELETE", "/api/admin/submission/1/delete"),
    ("POST", "/api/admin/submission/1/regrade"),

    # User
    ("GET", "/api/user"),
    ("GET", "/api/users/leaderboard"),
    ("GET", "/api/admin/users"),
    ("POST", "/api/admin/user/add"),
]

ADMIN_REQUIRED_ROUTES = [
    # Contest
    ("GET", "/api/admin/contests"),
    ("GET", "/api/admin/contest/1"),
    ("POST", "/api/admin/contest/1/add/problem"),
    ("POST", "/api/admin/contest/1/add/pset"),
    ("POST", "/api/admin/contest/unlinkproblem"),
    ("POST", "/api/admin/contest/update"),
    ("POST", "/api/admin/contest/add"),
    ("POST", "/api/admin/contest/updateproblems"),

    # Problem
    ("GET", "/api/admin/problem/1"),
    ("POST", "/api/admin/problem/update"),
    ("DELETE", "/api/admin/problem/1/delete"),

    # Problem Set
    ("GET", "/api/admin/psets"),
    ("GET", "/api/admin/pset/1"),
    ("POST", "/api/admin/pset/update"),
    ("POST", "/api/admin/pset/add"),
    ("POST", "/api/admin/pset/add/problem"),
    ("GET", "/api/admin/pset/1/pdf"),
    ("POST", "/api/admin/pset/1/uploadpdf"),

    # Settings
    ("GET", "/api/admin/settings"),
    ("POST", "/api/admin/settings/update"),

    # Submission
    ("GET", "/api/admin/submissions/1"),
    ("DELETE", "/api/admin/submission/1/delete"),
    ("POST", "/api/admin/submission/1/regrade"),

    # User
    ("GET", "/api/admin/users"),
    ("POST", "/api/admin/user/add"),

]

CSRF_REQUIRED_ROUTES = [
    # Contest
    ("POST", "/api/contest/submit"),
    ("POST", "/api/admin/contest/1/add/problem"),
    ("POST", "/api/admin/contest/1/add/pset"),
    ("POST", "/api/admin/contest/unlinkproblem"),
    ("POST", "/api/admin/contest/update"),
    ("POST", "/api/admin/contest/add"),
    ("POST", "/api/admin/contest/updateproblems"),

    # Problem
    ("POST", "/api/admin/problem/update"),
    ("DELETE", "/api/admin/problem/1/delete"),

    # Problem Set
    ("POST", "/api/admin/pset/update"),
    ("POST", "/api/admin/pset/add"),
    ("POST", "/api/admin/pset/add/problem"),
    ("POST", "/api/admin/pset/1/uploadpdf"),

    # Settings
    ("POST", "/api/admin/settings/update"),

    # Submission
    ("DELETE", "/api/admin/submission/1/delete"),
    ("POST", "/api/admin/submission/1/regrade"),

    # User
    ("POST", "/api/login"),
    ("POST", "/api/register"),
    ("POST", "/api/admin/user/add"),
]

@pytest.mark.parametrize("method,route", LOGIN_REQUIRED_ROUTES)
def test_requires_login(client, method, route):
    response = client.open(route, method=method, json={})

    assert response.status_code == 401
    assert response.get_json()["error"] == "unauthorized"


@pytest.mark.parametrize("method,route", ADMIN_REQUIRED_ROUTES)
def test_requires_admin(client, user_logged_in, method, route):
    response = client.open(route, method=method, json={})

    assert response.status_code == 403
    assert response.get_json()["error"] == "not_admin"


@pytest.mark.parametrize("method,route", CSRF_REQUIRED_ROUTES)
def test_requires_csrf(app, client, admin_logged_in, method, route):
    app.config["WTF_CSRF_ENABLED"] = True
    response = client.open(route, method=method, json={})

    assert response.status_code == 400
    assert response.get_json()["error"] == "csrf_invalid"