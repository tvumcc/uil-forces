import flask
import flask_login

import functools
import re
import logging
import socket
import os
import subprocess
import shutil
import glob

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

def check_required_binaries():
    results = {}
    for tool in ["python", "java", "javac"]:
        # Check for an exectuable file (for Windows)
        tool_exe_paths = glob.glob(f"tools/**/{tool}.exe", recursive=True)

        if len(tool_exe_paths) == 0 or not IS_WINDOWS:
            results[tool] = check_required_binary_on_path(tool)
            continue

        tool_exe_path = tool_exe_paths[0]

        try:
            proc = subprocess.run([tool_exe_path, "--version"], capture_output=True, text=True, timeout=5)
            version = (proc.stdout or proc.stderr).strip().splitlines()[0]
            results[tool] = (True, version, tool_exe_path)
        except Exception:
            results[tool] = (True, "version check failed", tool_exe_path)

    return results

def check_required_binary_on_path(tool: str):
    path = shutil.which(tool)

    if path is None:
        return (False, None, None)

    try:
        proc = subprocess.run([tool, "--version"], capture_output=True, text=True, timeout=5)
        version = (proc.stdout or proc.stderr).strip().splitlines()[0]
        if "Python was not found" in version: # Handles app execution alias that redirects to the Microsoft Store version of Python
            return (False, version, None)
        else:
            return (True, version, "PATH")
    except Exception:
        return (True, "version check failed", "PATH")

def print_binary_check():
    print("Checking for required tools... (first in the 'tools' directory then on PATH)")
    results = check_required_binaries()
    all_ok = True
    for tool, (found, version, path) in results.items():
        status = "OK" if found else "MISSING"
        print(f"  [{status}] {tool}" + (f" — {version}" if found or version is not None else "") + f" (Location: {path})")
        if not found:
            all_ok = False
    if not all_ok:
        print("\nWarning: some required tools are missing. Grading for the affected")
        print("language(s) will fail until these are installed into the 'tools' directory or added to PATH.")
    return all_ok

def run_judge_self_test():
    print("Running judge self-test to quickly test correct environment setup (no Docker)...")
    from src.judge import grade_submission, Status

    class FakeProblem:
        use_stdin = False
        input_file_name = "A.dat"
        judge_input = "1\n2\n3\n4"
        judge_output = "10"

    class FakeSubmission:
        problem = FakeProblem()
        def __init__(self, id, language, expected_status, code, stdin=False):
            self.language = language
            self.expected_status = expected_status
            self.code = code
            self.stdin = stdin
            self.id = id

    java_submissions = [
        FakeSubmission(1, "Java", Status.Accepted, "public class A {public static void main(String[] args) {System.out.println(10);}}"),
        FakeSubmission(2, "Java", Status.WrongAnswer, "public class A {public static void main(String[] args) {System.out.println(9);}}"),
        FakeSubmission(3, "Java", Status.TimeLimitExceeded, "public class A {public static void main(String[] args) {while (true) {}}}"),
        FakeSubmission(4, "Java", Status.ErrorRuntime, "public class A {public static void main(String[] args) throws Exception {throw new Exception();}}"),
        FakeSubmission(5, "Java", Status.ErrorCompile, "public class A {public static void main(String[] args) {System.out.println(10)}}"),
        FakeSubmission(6, "Java", Status.Accepted, """
            import java.util.*;
            import java.io.*;
            public class A {
                public static void main(String[] args) throws Exception {
                    Scanner in = new Scanner(new File("A.dat"));
                    int sum = 0;
                    while (in.hasNextInt()) sum += in.nextInt();
                    System.out.println(sum);
                }
            }
        """),
        FakeSubmission(7, "Java", Status.Accepted, """
            import java.util.*;
            public class A {
                public static void main(String[] args) throws Exception {
                    Scanner in = new Scanner(System.in);
                    int sum = 0;
                    while (in.hasNextInt()) sum += in.nextInt();
                    System.out.println(sum);
                }
            }
        """, stdin=True),
    ]

    python_submissions = [
        FakeSubmission(8, "Python", Status.Accepted, "print(10)"),
        FakeSubmission(9, "Python", Status.WrongAnswer, "print(9)"),
        FakeSubmission(10, "Python", Status.TimeLimitExceeded, "while True: pass"),
        FakeSubmission(11, "Python", Status.ErrorRuntime, "pint(10)"),
        FakeSubmission(12, "Python", Status.Accepted, """with open("A.dat") as f: print(sum([int(line) for line in f.readlines()]))"""),
        FakeSubmission(13, "Python", Status.ErrorRuntime, """with open("B.dat") as f: pass"""),
        FakeSubmission(14, "Python", Status.Accepted, """import sys; print(sum([int(line) for line in sys.stdin.readlines()]))""", stdin=True),
    ]

    java_allgood = True
    python_allgood = True
    java_test_idx = 1
    python_test_idx = 1

    from src.app import runtime_dir
    from src.judge import get_submission_folder_name

    for submission in java_submissions:
        status, output = grade_submission(submission, timeout=1.5, stdin=submission.stdin)
        if status != submission.expected_status:
            java_allgood = False
            print(f"\t[FAILED] Java grading: expected status {submission.expected_status.name}, got status {status.name}")
        else:
            print(f"\t[OK] Java Grading Test {java_test_idx} Passed")
        java_test_idx += 1

    for submission in python_submissions:
        status, output = grade_submission(submission, timeout=1.5, stdin=submission.stdin)
        if status != submission.expected_status:
            python_allgood = False
            print(f"\t[FAILED] Python grading: expected status {submission.expected_status.name}, got status {status.name}")
        else:
            print(f"\t[OK] Python Grading Test {python_test_idx} Passed")
        python_test_idx += 1

    if java_allgood:
        print("\t[SUCCESS] Java grading environment setup is correct.")
    else:
        print("\t[FAILURE] Java grading environment setup is incorrect.")

    if python_allgood:
        print("\t[SUCCESS] Python grading environment setup is correct.")
    else:
        print("\t[FAILURE] Python grading environment setup is incorrect.")