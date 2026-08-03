import flask
import flask_login

import functools
import re
import logging
import socket
import os
import ctypes

IS_WINDOWS = os.name == "nt"
if IS_WINDOWS:
    import winreg

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
            return {"error": "not_admin"}, 403
        return f(*args, **kwargs)
    return decorated_function

username_pattern = re.compile("\\w{3,25}")

def valid_username(username: str):
    return username_pattern.fullmatch(username) is not None

def valid_name(name: str):
    return len(name) >= 3 and len(name) <= 50

def add_to_user_path(new_path: str) -> bool:
    if not IS_WINDOWS:
        print("This action is only available on Windows")
        return False

    new_path = os.path.normpath(new_path)
    if not os.path.isdir(new_path):
        print(f"'{new_path}' is not a valid directory")
        return False

    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_ALL_ACCESS)
    try:
        try:
            current_path, value_type = winreg.QueryValueEx(key, "Path")
        except FileNotFoundError:
            current_path, value_type = "", winreg.REG_EXPAND_SZ

        existing_entries = [p for p in current_path.split(";") if p]
        if any(os.path.normpath(p).lower() == new_path.lower() for p in existing_entries):
            print(f"'{new_path}' is already in your PATH")
            return True

        existing_entries.append(new_path)
        updated_path = ";".join(existing_entries)
        winreg.SetValueEx(key, "Path", 0, value_type, updated_path)
    finally:
        winreg.CloseKey(key)

    # Notify other running applications of environment change
    HWND_BROADCAST = 0xFFFF
    WM_SETTINGCHANGE = 0x1A
    SMTO_ABORTIFHUNG = 0x0002
    result = ctypes.c_long()
    ctypes.windll.user32.SendMessageTimeoutW(
        HWND_BROADCAST, WM_SETTINGCHANGE, 0, "Environment",
        SMTO_ABORTIFHUNG, 5000, ctypes.byref(result)
    )

    # Make the PATH effective without requiring a restart
    os.environ["PATH"] = os.environ.get("PATH", "") + os.pathsep + new_path

    print(f"Added '{new_path}' to your user PATH")
    return True