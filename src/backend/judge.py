from sqlalchemy.orm import Session

from .orm import *
from main import app

import os
import shutil
import subprocess
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
    return f"submission{id}"

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

def assign_status(submission_id, docker=True):
    with app.app_context():
        submission: Submission = db.session.get(Submission, submission_id)
        if submission.status == Status.Pending.value:
            status, submission.output = grade_submission_docker(submission) if docker else grade_submission(submission)
            submission.status = status.value
            db.session.commit()

def grade_submission(submission: Submission, timeout: int = 5):
    id = submission.id
    filename, _ = os.path.splitext(os.path.basename(submission.filename))
    submission_folder_name = get_submission_folder_name(id)
    submission_dir = setup_submission_for_grading(submission)

    try:
        # Language specific setup
        match submission.language:
            case "Java":
                # Set up Custom Security Manager Policy
                policy_file_text = f'grant {{\n\tpermission java.io.FilePermission "{os.path.join(submission_dir, (submission.problem.name).lower())}.dat", "read";\n}};'
                with open(os.path.join(submission_folder_name, "grading.policy"), "w") as f:
                    f.write(policy_file_text)
            case "Python": pass
            case "C++": pass

        # Compilation
        language_compile_command = {
            "Java":   f"javac {filename}.java".split(),
            "Python": "echo".split(),
            "C++":    f"g++ {filename}.cpp -o {filename}".split()
        }

        compile_status = subprocess.run(
            language_compile_command[submission.language],
            capture_output=True,
            cwd=submission_dir
        )

        if compile_status.returncode != 0:
            return (Status.ErrorCompile, compile_status.stderr.decode("utf-8"))
        
        # Running
        language_run_command = {
            "Java":   f"java -Djava.security.manager -Djava.security.policy=grading.policy {filename}".split(),
            "Python": f"python {filename}.py".split(),
            "C++":    f"./{filename}".split()
        }

        try:
            run_status = subprocess.run(
                language_run_command[submission.language], 
                capture_output=True, 
                timeout=timeout, 
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
        except:
            return (Status.ErrorServer, "")
    finally:
        try: shutil.rmtree(submission_dir)
        except: pass

def grade_submission_docker(submission: Submission, timeout: int = 5):
    id = submission.id
    filename, _ = os.path.splitext(os.path.basename(submission.filename))
    submission_folder_name = get_submission_folder_name(id)
    submission_dir = setup_submission_for_grading(submission)
    container_id = ""

    language_image = {
        "Java":   "openjdk:11",
        "Python": "alpine:3.14",
        "C++":    "alpine:3.14"
    }

    try:
        container_id = subprocess.check_output(f"docker run -d --name {submission_folder_name} --memory=512m --mount type=bind,src={submission_dir},dst=/user/src/app -w /user/src/app {language_image[submission.language]} tail -f /dev/null".split()).decode("utf-8")

        language_compile_command = {
            "Java":   f"docker exec {container_id} javac {filename}.java".split(),
            "Python": f"docker exec {container_id} apk add python3".split(),
            "C++":    f'docker exec {container_id} sh -c'.split() + [f'apk add g++ && g++ {filename}.cpp -o {filename}']
        }

        compile_status = subprocess.run(
            language_compile_command[submission.language], 
            capture_output=True,
            cwd=submission_dir
        )
        if compile_status.returncode != 0:
            return (Status.ErrorCompile, compile_status.stderr.decode("utf-8"))

        language_run_command = {
            "Java":   f"docker exec {container_id} timeout {timeout} java {filename}".split(),
            "Python": f"docker exec {container_id} timeout {timeout} python3 {filename}.py".split(),
            "C++":    f"docker exec {container_id} timeout {timeout} ./{filename}".split()
        }

        try:
            run_status = subprocess.run(language_run_command[submission.language], capture_output=True)

            print(run_status.returncode)
            print(run_status.stdout.decode("utf-8"))
            print(run_status.stderr.decode("utf-8"))
            if run_status.returncode == 124 or run_status.returncode == 143:
                raise subprocess.TimeoutExpired("", "")
            if run_status.returncode == 1 or run_status.returncode == 139:
                raise subprocess.CalledProcessError(1, "", stderr=run_status.stderr)

            run_output = run_status.stdout.decode("utf-8")     
            submission_output = "\n".join([x.rstrip() for x in run_output.strip().splitlines()])
            judge_output = "\n".join([x.rstrip() for x in submission.problem.judge_output.strip().splitlines()])
            return (Status.Accepted if submission_output == judge_output else Status.WrongAnswer, submission_output)
        except subprocess.TimeoutExpired as e:
            return (Status.TimeLimitExceeded, "")
        except subprocess.CalledProcessError as e:
            return (Status.ErrorRuntime, e.stderr.decode("utf-8"))
        except:
            return (Status.ErrorServer, "")
    finally:
        try: shutil.rmtree(submission_dir)
        except: pass
        subprocess.run(f"docker stop -t 0 {container_id}".split())
        subprocess.run(f"docker rm {container_id}".split())