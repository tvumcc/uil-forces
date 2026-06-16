import functools
import flask
import flask_login
import logging

log = logging.getLogger(__name__)
console_handler = logging.StreamHandler()
formatter = logging.Formatter(
    "[{asctime}] {funcName} - {levelname}: {message}",
    style="{",
    datefmt="%Y/%m/%d %H:%M:%S",
)

log.addHandler(console_handler)
console_handler.setFormatter(formatter)
log.setLevel(logging.INFO)

def user_required(f):
    @functools.wraps(f)
    @flask_login.login_required
    def decorated_function(*args, **kwargs):
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @functools.wraps(f)
    @flask_login.login_required
    def decorated_function(*args, **kwargs):
        if not flask_login.current_user.is_admin:
            flask.abort(403)
        return f(*args, **kwargs)
    return decorated_function