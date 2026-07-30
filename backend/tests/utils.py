import datetime
from datetime import timezone
import pypdf
import os
import subprocess
import shutil

from src.models.orm import *
from src.judge import Status

def make_submission(user, problem, contest_profile=None, status=Status.Accepted.value, code="print(1)", language="Java", minutes_ago=0):
    submission = Submission(
        problem=problem,
        user=user,
        contest_profile=contest_profile,
        status=status,
        code=code,
        language=language,
        submit_time=datetime.datetime.now(timezone.utc) - datetime.timedelta(minutes=minutes_ago),
    )
    db.session.add(submission)
    db.session.commit()
    return submission

def make_profile(user, contest):
    profile = ContestProfile(user=user, contest=contest)
    db.session.add(profile)
    db.session.commit()
    return profile

def write_minimal_pdf(path, num_pages=1):
    writer = pypdf.PdfWriter()
    for _ in range(num_pages):
        writer.add_blank_page(width=200, height=200)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        writer.write(f)

def check_required_binaries():
    results = {}
    for tool, version_cmd in [
        ("python", ["python", "--version"]),
        ("java", ["java", "--version"]),
        ("javac", ["javac", "--version"]),
    ]:
        path = shutil.which(tool)
        if path is None:
            results[tool] = (False, None)
            continue
        try:
            proc = subprocess.run(version_cmd, capture_output=True, text=True, timeout=5)
            version = (proc.stdout or proc.stderr).strip().splitlines()[0]
            results[tool] = (True, version)
        except Exception:
            results[tool] = (True, "version check failed")
    return results

def print_binary_check():
    print("Checking for required tools on PATH...")
    results = check_required_binaries()
    all_ok = True
    for tool, (found, version) in results.items():
        status = "OK" if found else "MISSING"
        print(f"  [{status}] {tool}" + (f" — {version}" if found else ""))
        if not found:
            all_ok = False
    if not all_ok:
        print("\nWarning: some required tools are missing. Grading for the affected")
        print("language(s) will fail until these are installed and added to PATH.")
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
        id = 99999
        problem = FakeProblem()
        def __init__(self, language, expected_status, code, stdin=False):
            self.language = language
            self.expected_status = expected_status
            self.code = code
            self.stdin = stdin

    java_submissions = [
        FakeSubmission("Java", Status.Accepted, "public class A {public static void main(String[] args) {System.out.println(10);}}"),
        FakeSubmission("Java", Status.WrongAnswer, "public class A {public static void main(String[] args) {System.out.println(9);}}"),
        FakeSubmission("Java", Status.TimeLimitExceeded, "public class A {public static void main(String[] args) {while (true) {}}}"),
        FakeSubmission("Java", Status.ErrorRuntime, "public class A {public static void main(String[] args) throws Exception {throw new Exception();}}"),
        FakeSubmission("Java", Status.ErrorCompile, "public class A {public static void main(String[] args) {System.out.println(10)}}"),
        FakeSubmission("Java", Status.Accepted, """
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
        FakeSubmission("Java", Status.Accepted, """
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
        FakeSubmission("Python", Status.Accepted, "print(10)"),
        FakeSubmission("Python", Status.WrongAnswer, "print(9)"),
        FakeSubmission("Python", Status.TimeLimitExceeded, "while True: print(10)"),
        FakeSubmission("Python", Status.ErrorRuntime, "pint(10)"),
        FakeSubmission("Python", Status.Accepted, """with open("A.dat") as f: print(sum([int(line) for line in f.readlines()]))"""),
        FakeSubmission("Python", Status.ErrorRuntime, """with open("B.dat") as f: pass"""),
        FakeSubmission("Python", Status.Accepted, """import sys; print(sum([int(line) for line in sys.stdin.readlines()]))""", stdin=True),
    ]

    java_allgood = True
    python_allgood = True
    java_test_idx = 1
    python_test_idx = 1

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