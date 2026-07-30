import os
import shutil
import subprocess
import enum
import re
import threading
import psutil
import uuid
import signal
from concurrent.futures import ThreadPoolExecutor

from src.models.orm import *
from src.utils import *

submission_events: dict[int, threading.Event] = {}
submission_events_lock = threading.Lock()
grading_pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix="grader")

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

def normalize_output(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return "\n".join(line.rstrip() for line in text.rstrip().splitlines())

def output_equal(text_a: str, text_b: str) -> bool:
    a = normalize_output(text_a)
    b = normalize_output(text_b)
    return a == b

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
        case _:
            return None

def get_submission_event(submission_id: int) -> threading.Event:
    with submission_events_lock:
        if not submission_id in submission_events:
            submission_events[submission_id] = threading.Event()
        return submission_events[submission_id]

def delete_submission_event(submission_id: int):
    with submission_events_lock:
        submission_events.pop(submission_id, None)

def mark_submission_complete(submission_id: int):
    event = get_submission_event(submission_id)
    event.set()

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
    if len(submission.problem.judge_input) > 0 and len(submission.problem.input_file_name) > 0:
        with open(os.path.join(submission_folder_name, f"{submission.problem.input_file_name}"), "w") as f:
            f.write(submission.problem.judge_input.replace("\r\n", "\n"))

    return submission_dir

def enqueue_submission(submission_id: int, regrade: bool = False):
    app = flask.current_app._get_current_object()
    grading_pool.submit(assign_status, app, submission_id, regrade, Settings.docker_grading_enabled())

def assign_status(app, submission_id: int, regrade: bool, docker: bool, stdin: bool = False):
    """
    Calls the appropriate function to grade the given submission using Docker or a compiler/interpreter on PATH
    After the submission has been graded, if a contest profile was supplied, its score will be recalculated
    """

    with app.app_context():
        try:
            submission = db.session.get(Submission, submission_id)
            if submission is None:
                raise Exception(f"Cannot grade submission: submission with ID {submission_id} not found")

            contest_profile_id = submission.contest_profile_id
            contest_profile = db.session.get(ContestProfile, contest_profile_id)
            if contest_profile is None:
                raise Exception(f"Cannot grade submission: contest profile with ID {contest_profile_id} not found")

            contest_problem_link = db.session.query(ContestProblemAssociation).filter_by(contest_id=contest_profile.contest_id, problem_id=submission.problem_id).first()
            if contest_problem_link is None:
                raise Exception(f"Cannot grade submission: link between contest with ID {contest_profile.contest_id} and problem with ID {submission.problem_id} not found")

            if submission.status == Status.Pending.value or regrade:
                try:
                    if docker:
                        status, submission.output = grade_submission_docker(submission, contest_problem_link.grading_timeout, stdin)
                    else:
                        status, submission.output = grade_submission(submission, contest_problem_link.grading_timeout, stdin)
                except Exception as e:
                    log.error(f"Unhandled exception grading submission {submission_id}: {e}")
                    status = Status.ErrorServer
                    submission.output = ""

                submission.status = status.value
                contest_profile = db.session.merge(contest_profile)
                contest_profile.calculate_score()
                submission = db.session.merge(submission)

                db.session.add(submission)
                db.session.commit()
                mark_submission_complete(submission.id)

                log.info(f"Judge: finished grading submission {submission.id} for {contest_profile.user.username}")
        except Exception as e:
            log.error(e)
            db.session.rollback() 

def kill_process_tree(pid, known_descendants: set[int] | None = None): 
    """
    Kill the process itself plus any descendants seen at any point during its lifetime,
    including ones reparented away before the parent process was killed
    """
    if known_descendants is None:
        known_descendants = set()

    try:
        parent = psutil.Process(pid)
        for child in parent.children(recursive=True):
            known_descendants.add(child.pid)
        try:
            parent.kill()
        except psutil.NoSuchProcess:
            pass
    except psutil.NoSuchProcess:
        pass

    for pid in known_descendants:
        try:
            psutil.Process(pid).kill()
        except psutil.NoSuchProcess:
            pass

def run_and_capture(cmd, timeout, cwd, stdin_file=None):
    """
    Runs code with standard input (if enabled) and returns the contents of standard error and output and the return code.
    Guaranteed process-tree cleanup on every exit path (success, timeout, or error).

    Returns a tuple of the form (returncode, stdout_bytes, stderr_bytes)
    Raises subprocess.TimeoutExpired if the timeout is hit.
    """

    popen_kwargs = {}
    use_process_group = hasattr(os, "setsid")  # POSIX only, no-op path for Windows
    if use_process_group:
        popen_kwargs["start_new_session"] = True

    proc = subprocess.Popen(
        cmd,
        cwd=cwd,
        stdin=stdin_file if stdin_file is not None else subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        **popen_kwargs,
    )

    known_descendants: set[int] = set()
    stop_watching = threading.Event()

    def watch_descendants():
        try:
            parent = psutil.Process(proc.pid)
        except psutil.NoSuchProcess:
            return
        while not stop_watching.is_set():
            try:
                for child in parent.children(recursive=True):
                    known_descendants.add(child.pid)
            except psutil.NoSuchProcess:
                pass
            stop_watching.wait(0.01)

    watcher = threading.Thread(target=watch_descendants, daemon=True)
    watcher.start()

    try:
        stdout, stderr = proc.communicate(timeout=timeout)
        return proc.returncode, stdout, stderr
    except subprocess.TimeoutExpired:
        raise
    finally:
        stop_watching.set()
        watcher.join(timeout=1)

        if use_process_group:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass

        kill_process_tree(proc.pid, known_descendants)

def grade_submission(submission: Submission, timeout: float = 5.0, stdin: bool = False):
    """
    Compiles (if necessary) and runs the code for the given submission using a local compiler/interpreter on PATH.
    If the amount of time it takes for the code to run exceeds the specified timeout, the status will be TimeLimitExceeded.

    Returns a tuple of the form (status, output)
    """

    try:
        filename = get_submission_file_name(submission)
        if filename is None: raise Exception("Invalid language")

        submission_dir = setup_submission_for_grading(submission)
        use_stdin = submission.problem.use_stdin or stdin

        # Compilation
        language_compile_command = {
            "Java":   f"javac {filename}".split(),
        }

        if submission.language in language_compile_command.keys():
            compile_status = subprocess.run(
                language_compile_command[submission.language],
                capture_output=True,
                cwd=submission_dir
            )

            if compile_status.returncode != 0:
                return (Status.ErrorCompile, compile_status.stderr.decode("utf-8", errors="replace"))
        
        # Running
        language_run_command = {
            "Java":   f"java {os.path.splitext(filename)[0]}".split(),
            "Python": f"python {filename}".split(),
        }

        try:
            if use_stdin:
                input_path = os.path.join(submission_dir, submission.problem.input_file_name)
                with open(input_path, "rb") as f:
                    return_code, stdout, stderr = run_and_capture(
                        language_run_command[submission.language],
                        timeout=timeout,
                        cwd=submission_dir,
                        stdin_file=f
                    )
            else:
                return_code, stdout, stderr = run_and_capture(
                    language_run_command[submission.language],
                    timeout=timeout,
                    cwd=submission_dir,
                )


            if return_code != 0:
                return (Status.ErrorRuntime, stderr.decode("utf-8", errors="replace")) 

            # Check Output

            submission_output = stdout.decode("utf-8", errors="replace")
            equal = output_equal(submission_output, submission.problem.judge_output)

            return (Status.Accepted if equal else Status.WrongAnswer, submission_output)
        except subprocess.TimeoutExpired as e:
            return (Status.TimeLimitExceeded, "")
        except Exception as e:
            log.error(f"Unexpected error grading submission {submission.id}: {e}")
            return (Status.ErrorServer, "")
    except Exception as e:
        return (Status.ErrorServer, "")
    finally:
        try: 
            shutil.rmtree(submission_dir)
        except: 
            pass

def grade_submission_docker(submission: Submission, timeout: float = 5.0, stdin: bool = False):
    """
    Compiles (if necessary) and runs the code for the given submission using Docker containers.
    If the amount of time it takes for the code to run exceeds the specified timeout, the status will be TimeLimitExceeded.

    Returns a tuple of the form (status, output)
    """

    try:
        filename = get_submission_file_name(submission)
        if filename is None: raise Exception("Invalid language")

        container_name = f"{get_submission_folder_name(submission.id)}-{uuid.uuid4().hex[:8]}"
        submission_dir = setup_submission_for_grading(submission)
        container_id = ""
        use_stdin = submission.problem.use_stdin or stdin

        language_image = {
            "Java":   "eclipse-temurin:21-jdk",
            "Python": "python:3.14-alpine",
        }

        # Container creation
        try:
            container_id = subprocess.check_output(
                [
                    "docker", "run", "-d", "--rm", "--name", container_name,
                    "--memory=512m", "--cpus=1", "--pids-limit=100", "--network=none",
                    "--security-opt=no-new-privileges",
                    "-v", f"{submission_dir}:/user/src/app:Z",
                    "-w", "/user/src/app",
                    language_image[submission.language], "tail", "-f", "/dev/null",
                ],
                timeout=30,
            ).decode("utf-8").strip()
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            log.error(f"Failed to start grading container for submission {submission.id}: {e}")
            return (Status.ErrorServer, "")

        # Compilation
        language_compile_command = {
            "Java":   f'docker exec -w /user/src/app {container_id} javac'.split() + [filename],
        }

        if submission.language in language_compile_command:
            compile_status = subprocess.run(
                language_compile_command[submission.language], 
                capture_output=True,
                cwd=submission_dir,
                timeout=30,
            )
            if compile_status.returncode != 0:
                return (Status.ErrorCompile, compile_status.stderr.decode("utf-8", errors="replace"))

        # Running
        language_run_command = {
            "Java":   f'docker exec -w /user/src/app -i {container_id} timeout -k 1 {timeout} java'.split() + [os.path.splitext(filename)[0]],
            "Python": f'docker exec -w /user/src/app -i {container_id} timeout -k 1 {timeout} python3'.split() + [filename],
        }

        try:
            if use_stdin:
                with open(os.path.join(submission_dir, submission.problem.input_file_name), "rb") as f:
                    run_status = subprocess.run(
                        language_run_command[submission.language],
                        stdin=f,
                        capture_output=True,
                        timeout=timeout + 5,
                    )
            else:
                run_status = subprocess.run(
                    language_run_command[submission.language], 
                    capture_output=True,
                    timeout=timeout + 5,
                )

            if run_status.returncode in (124, 137, 143):
                raise subprocess.TimeoutExpired(language_run_command[submission.language], timeout)
            if run_status.returncode != 0:
                return (Status.ErrorRuntime, run_status.stderr.decode("utf-8", errors="replace"))

            submission_output = run_status.stdout.decode("utf-8", errors="replace")
            equal = output_equal(submission_output, submission.problem.judge_output)

            return (Status.Accepted if equal else Status.WrongAnswer, submission_output)
        except subprocess.TimeoutExpired as e:
            return (Status.TimeLimitExceeded, "")
        except Exception as e:
            log.error(f"Unexpected error grading submission {submission.id}: {e}")
            return (Status.ErrorServer, "")
    except Exception as e:
        return (Status.ErrorServer, "")
    finally:
        if container_id:
            try:
                subprocess.run(["docker", "stop", "-t", "0", container_id], timeout=10, capture_output=True)
            except Exception:
                pass

        try: 
            shutil.rmtree(submission_dir)
        except:
            pass