from sqlalchemy.orm import Session

import os
import shutil
import subprocess
import enum
import re

from src.backend.orm import *
from src.backend.log import *

class Status(enum.Enum):
    Pending = 0
    Accepted = 1
    WrongAnswer = 2
    ErrorCompile = 3
    ErrorRuntime = 4
    TimeLimitExceeded = 5
    ErrorServer = 6 

def get_submission_folder_name(id):
    return f"submission{id}"

def get_submission_file_name(submission: Submission):
    """
    Returns the source file name for a submission, including the file extension
    This is mainly for Java since the source file name must be the same as the name of the sole public class
    """

    match submission.language:
        case "Java":
            regex = r"public\s+class\s+([A-Za-z$_][A-Za-z0-9$_]*).*\{*"
            match = re.search(regex, submission.code)
            return match.group(1) + ".java" if match else "error"
        case "Python":
            return get_submission_folder_name(submission.id) + ".py"
        case "C++":
            return get_submission_folder_name(submission.id) + ".cpp"
        case _:
            return None

def setup_submission_for_grading(submission: Submission) -> str:
    """Helper function to prepare a directory for grading the given submission"""

    id = submission.id
    filename = get_submission_file_name(submission)
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

def assign_status(submission, contest_profile, docker=False):
    """
    Calls the appropriate function to grade the given submission using Docker or a compiler/interpreter on PATH
    After the submission has been graded, if a contest profile was supplied, its score will be recalculated
    """

    from main import app
    with app.app_context():
        if submission.status == Status.Pending.value:
            if docker:
                status, submission.output = grade_submission_docker(submission, submission.problem.pset.grading_timeout)
            else:
                status, submission.output = grade_submission(submission, submission.problem.pset.grading_timeout)
            submission.status = status.value
            if contest_profile is not None:
                contest_profile = db.session.merge(contest_profile)
                contest_profile.calculate_score()
            submission = db.session.merge(submission)
            db.session.add(submission)
            db.session.commit()

def grade_submission(submission: Submission, timeout: float = 5.0):
    """
    Compiles (if necessary) and runs the code for the given submission using a local compiler/interpreter on PATH.
    If the amount of time it takes for the code to run exceeds the specified timeout, the status will be TimeLimitExceeded.

    Returns a tuple of the form (status, output)
    """

    id = submission.id
    filename = get_submission_file_name(submission)
    submission_folder_name = get_submission_folder_name(id)
    submission_dir = setup_submission_for_grading(submission)
    use_stdin = submission.problem.use_stdin

    try:
        # Compilation
        language_compile_command = {
            "Java":   f"javac {filename}".split(),
            "C++":    f"g++ {filename} -o {submission_folder_name}".split()
        }

        if submission.language in language_compile_command.keys():
            compile_status = subprocess.run(
                language_compile_command[submission.language],
                capture_output=True,
                cwd=submission_dir
            )

            if compile_status.returncode != 0:
                return (Status.ErrorCompile, compile_status.stderr.decode("utf-8"))
        
        # Running
        language_run_command = {
            "Java":   f"java {os.path.splitext(filename)[0]}".split(),
            "Python": f"python {filename}".split(),
            "C++":    f"./{submission_folder_name}".split()
        }

        try:
            if use_stdin:
                with open(os.path.join(submission_folder_name, submission.problem.input_file_name), "rb") as f:
                    run_status = subprocess.run(
                        language_run_command[submission.language], 
                        capture_output=True, 
                        timeout=timeout, 
                        cwd=submission_dir,
                        check=True,
                        stdin=f
                    )
            else:
                run_status = subprocess.run(
                    language_run_command[submission.language], 
                    capture_output=True, 
                    timeout=timeout, 
                    cwd=submission_dir,
                    check=True,
                )

            # Check Output
            run_output = run_status.stdout.decode("utf-8")
            submission_output = run_output.replace("\r\n", "\n").replace("\r", "\n")
            submission_output = "\n".join([x.rstrip() for x in submission_output.strip().splitlines()])
            judge_output = submission.problem.judge_output.replace("\r\n", "\n").replace("\r", "\n")
            judge_output = "\n".join([x.rstrip() for x in judge_output.strip().splitlines()])
            return (Status.Accepted if submission_output == judge_output else Status.WrongAnswer, submission_output)
        except subprocess.TimeoutExpired as e:
            return (Status.TimeLimitExceeded, "")
        except subprocess.CalledProcessError as e:
            return (Status.ErrorRuntime, e.stdout.decode("utf-8")) 
        except Exception as e:
            print(e)
            return (Status.ErrorServer, "")
    finally:
        try: shutil.rmtree(submission_dir)
        except: pass

def grade_submission_docker(submission: Submission, timeout: float = 5.0):
    """
    Compiles (if necessary) and runs the code for the given submission using Docker containers.
    If the amount of time it takes for the code to run exceeds the specified timeout, the status will be TimeLimitExceeded.

    Returns a tuple of the form (status, output)
    """

    id = submission.id
    filename = get_submission_file_name(submission)
    submission_folder_name = get_submission_folder_name(id)
    submission_dir = setup_submission_for_grading(submission)
    container_id = ""
    use_stdin = submission.problem.use_stdin

    language_image = {
        "Java":   "openjdk:21",
        "Python": "alpine:3.14",
        "C++":    "alpine:3.14"
    }

    try:
        # Compilation
        container_id = subprocess.check_output(f"docker run -d --name {submission_folder_name} --memory=512m --mount type=bind,src={submission_dir},dst=/user/src/app -w /user/src/app {language_image[submission.language]} tail -f /dev/null".split()).decode("utf-8")

        language_compile_command = {
            "Java":   f'docker exec {container_id} javac'.split() + [f'{filename}'],
            "Python": f"docker exec {container_id} apk add python3".split(),
            "C++":    f'docker exec {container_id} sh -c'.split() + [f'apk add g++ && g++ "{filename}" -o "{submission_folder_name}"']
        }

        compile_status = subprocess.run(
            language_compile_command[submission.language], 
            capture_output=True,
            cwd=submission_dir
        )

        print(compile_status.stdout.decode("utf-8"))
        print(compile_status.stderr.decode("utf-8"))

        if compile_status.returncode != 0:
            return (Status.ErrorCompile, compile_status.stderr.decode("utf-8"))

        # Running
        language_run_command = {
            "Java":   f'docker exec -i {container_id} timeout {timeout} java'.split() + [f'{os.path.splitext(filename)[0]}'],
            "Python": f'docker exec {container_id} timeout {timeout} python3'.split() + [f'{filename}'],
            "C++":    f'docker exec {container_id} timeout {timeout} ./{submission_folder_name}'.split()
        }

        try:
            if use_stdin:
                with open(os.path.join(submission_folder_name, submission.problem.input_file_name), "rb") as f:
                    run_status = subprocess.run(language_run_command[submission.language], stdin=f, capture_output=True)
            else:
                run_status = subprocess.run(language_run_command[submission.language], capture_output=True)

            print(run_status.returncode)
            print(run_status.stdout.decode("utf-8"))
            print(run_status.stderr.decode("utf-8"))
            if run_status.returncode == 124 or run_status.returncode == 143:
                raise subprocess.TimeoutExpired("", "")
            if run_status.returncode == 1 or run_status.returncode == 139:
                raise subprocess.CalledProcessError(1, "", stderr=run_status.stderr)

            # Check Output
            run_output = run_status.stdout.decode("utf-8")     
            submission_output = run_output.replace("\r\n", "\n").replace("\r", "\n")
            submission_output = "\n".join([x.rstrip() for x in submission_output.strip().splitlines()])
            judge_output = submission.problem.judge_output.replace("\r\n", "\n").replace("\r", "\n")
            judge_output = "\n".join([x.rstrip() for x in judge_output.strip().splitlines()])
            return (Status.Accepted if submission_output == judge_output else Status.WrongAnswer, submission_output)
        except subprocess.TimeoutExpired as e:
            return (Status.TimeLimitExceeded, "")
        except subprocess.CalledProcessError as e:
            return (Status.ErrorRuntime, e.stderr.decode("utf-8"))
        except Exception as e:
            log.error(e)
            return (Status.ErrorServer, "")
    finally:
        try: shutil.rmtree(submission_dir)
        except: pass
        subprocess.run(f"docker stop -t 0 {container_id}".split())
        subprocess.run(f"docker rm {container_id}".split())