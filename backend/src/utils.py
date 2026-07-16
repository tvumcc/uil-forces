import flask
import flask_login

import functools
import re
import logging
import socket

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y/%m/%d %H:%M:%S",
)

waitress_log = logging.getLogger("waitress")
waitress_log.setLevel(logging.INFO)

log = logging.getLogger("UIL Forces")
log.setLevel(logging.INFO)

def get_all_local_ips():
    hostname = socket.gethostname()
    try:
        ips = socket.gethostbyname_ex(hostname)[2]
        return [ip for ip in ips if not ip.startswith("127.")]
    except socket.gaierror:
        return []

def admin_required(f):
    @functools.wraps(f)
    @flask_login.login_required
    def decorated_function(*args, **kwargs):
        if not flask_login.current_user.is_admin:
            return {"error", "not_admin"}, 403
        return f(*args, **kwargs)
    return decorated_function

username_pattern = re.compile("\\w{3,25}")

def valid_username(username: str):
    return username_pattern.match(username)

def valid_name(name: str):
    return len(name) >= 3 and len(name) <= 50