from sqlalchemy.orm import Session

from .orm import *
from main import app

import os
import shutil
import subprocess
import threading
import time
import re
import enum

class Status(enum.Enum):
    Pending = 0
    Accepted = 1
    WrongAnswer = 2
    ErrorCompile = 3
    ErrorRuntime = 4
    TimeLimitExceeded = 5
    ErrorServer = 6 

def get_submission_folder_name(id):
    return f"./submission{id}"

def setup_submission_for_grading(submission: Submission) -> str:
    id = submission.id
    filename = os.path.basename(submission.filename)
    submission_folder_name = get_submission_folder_name(id)

    # Create a source file for the submitted code in its own submission directory
    os.mkdir(submission_folder_name)
    submission_dir = os.path.abspath(submission_folder_name)
    with open(os.path.join(submission_folder_name, filename), "w") as f:
        f.write(submission.code)

    # Write the problem's judge input data to a file
    if submission.problem.input_file_name:
        with open(os.path.join(submission_folder_name, f"{submission.problem.input_file_name}"), "w") as f:
            f.write(submission.problem.judge_input.replace("\r\n", "\n"))

    return submission_dir

def grade_pending_submissions(session: Session):
    pending_submissions = session.query(Submission).filter_by(status=Status.Pending).all()

    for submission in pending_submissions:
        status, output = grade_java_submission(submission)
        submission.status = status
        submission.output = output
        session.commit()

def assign_status(submission_id):
    with app.app_context():
        submission = db.session.get(Submission, submission_id)
        if submission.status == Status.Pending.value:
            status = Status.Pending
            output = ""
            print(submission.filename)
            match submission.language:
                case "Java":
                    status, output = grade_java_submission(submission)
                case "Python":
                    status, output = grade_python_submission(submission)
                case "C++":
                    status, output = grade_cpp_submission(submission)
                case _:
                    pass

            submission.status = status.value
            submission.output = output
            db.session.commit()

def grade_java_submission(submission: Submission):
    id = submission.id
    filename, _ = os.path.splitext(os.path.basename(submission.filename))
    submission_folder_name = get_submission_folder_name(id)
    submission_dir = setup_submission_for_grading(submission)

    # Set up Custom Security Manager Policy
    policy_file_text = f'grant {{\n\tpermission java.io.FilePermission "{os.path.join(submission_dir, (submission.problem.name).lower())}.dat", "read";\n}};'
    with open(os.path.join(submission_folder_name, "grading.policy"), "w") as f:
        f.write(policy_file_text)

    # Compile the Java source file
    compile_status = subprocess.run(
        ["javac", f"{filename}.java"],
        capture_output=True,
        cwd=submission_dir
    )

    if compile_status.returncode != 0:
        try: shutil.rmtree(submission_dir)
        except: pass
        return (Status.ErrorCompile, compile_status.stderr.decode("utf-8"))

    # Run the compiled Java class
    try:
        run_status = subprocess.run(
            ["java", "-Djava.security.manager", "-Djava.security.policy=grading.policy", filename], 
            capture_output=True, 
            timeout=5, 
            cwd=submission_dir,
            check=True
        )
        run_output = run_status.stdout.decode("utf-8")
        submission_output = "\n".join([x.rstrip() for x in run_output.strip().splitlines()])
        judge_output = "\n".join([x.rstrip() for x in submission.problem.judge_output.strip().splitlines()])
        return (Status.Accepted if submission_output == judge_output else Status.WrongAnswer, submission_output)
    except subprocess.TimeoutExpired as e:
        return (Status.TimeLimitExceeded, "")
    except subprocess.CalledProcessError as e:
        output = "\n".join(e.stderr.decode("utf-8").splitlines()[2:]) # Get rid of Security Manager warning
        return (Status.ErrorRuntime, output) 
    finally:
        try: shutil.rmtree(submission_dir)
        except: pass

def grade_python_submission(submission: Submission):
    id = submission.id
    filename, _ = os.path.splitext(os.path.basename(submission.filename))
    submission_dir = setup_submission_for_grading(submission)

    # Run the Python program
    try:
        run_status = subprocess.run(
            ["python", f"{filename}.py"], 
            capture_output=True, 
            timeout=5, 
            cwd=submission_dir,
            check=True
        )
        run_output = run_status.stdout.decode("utf-8")
        submission_output = "\n".join([x.rstrip() for x in run_output.strip().splitlines()])
        judge_output = "\n".join([x.rstrip() for x in submission.problem.judge_output.strip().splitlines()])
        return (Status.Accepted if submission_output == judge_output else Status.WrongAnswer, submission_output)
    except subprocess.TimeoutExpired as e:
        return (Status.TimeLimitExceeded, "")
    except subprocess.CalledProcessError as e:
        return (Status.ErrorRuntime, e.stderr.decode("utf-8")) 
    finally:
        try: shutil.rmtree(submission_dir)
        except: pass

def grade_cpp_submission(submission: Submission):
    id = submission.id
    filename, _ = os.path.splitext(os.path.basename(submission.filename))
    submission_dir = setup_submission_for_grading(submission)

    # Compile the C++ source file
    compile_status = subprocess.run(
        ["g++", f"{filename}.cpp", "-o", filename],
        capture_output=True,
        cwd=submission_dir
    )

    if compile_status.returncode != 0:
        try: shutil.rmtree(submission_dir)
        except: pass
        return (Status.ErrorCompile, compile_status.stderr.decode("utf-8"))

    # Run the compiled C++ executable
    try:
        run_status = subprocess.run(
            [f"./{filename}"], 
            capture_output=True, 
            timeout=5, 
            cwd=submission_dir,
            check=True
        )
        run_output = run_status.stdout.decode("utf-8")
        submission_output = "\n".join([x.rstrip() for x in run_output.strip().splitlines()])
        judge_output = "\n".join([x.rstrip() for x in submission.problem.judge_output.strip().splitlines()])
        return (Status.Accepted if submission_output == judge_output else Status.WrongAnswer, submission_output)
    except subprocess.TimeoutExpired as e:
        return (Status.TimeLimitExceeded, "")
    except subprocess.CalledProcessError as e:
        return (Status.ErrorRuntime, e.stderr.decode("utf-8")) 
    finally:
        try: shutil.rmtree(submission_dir)
        except: pass