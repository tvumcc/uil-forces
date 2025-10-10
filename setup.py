import yaml
import os
import sqlalchemy
import datetime
from sqlalchemy.orm import Session
from src.backend.orm import *

db_name = "main.db"
setup_file_name = "setup.yaml"
config_file_name = "config.yaml"
problem_set_path = "problemsets"

# Set up a new database
def setup():
    if os.path.exists(db_name):
        print(f"{db_name} already exists! Use setup to make an entirely new database.")
        return

    engine = sqlalchemy.create_engine(f"sqlite:///{db_name}")
    Base.metadata.create_all(engine)
    session: Session = Session(engine)

    with open(setup_file_name, "r") as setup_file:
        document = setup_file.read()
        setup_config = yaml.safe_load(document)

        practice_site = setup_config.get("practice_site", False)
        docker_grading = setup_config.get("docker_grading", False)

        session.add(Settings(key="practice_site", value="true" if practice_site else "false"))
        session.add(Settings(key="docker_grading", value="true" if docker_grading else "false"))

        for user in setup_config["users"]:
            username = user["username"]
            password = user["password"]
            is_admin = user.get("admin", False)

            session.add(User(username=username, passphrase=password, is_admin=is_admin))

        for problem_set in setup_config["problem_sets"]:
            pset_name = problem_set["name"]
            pdf_path = problem_set.get("pdf_path", "")
            dataout_path = os.path.join(problem_set_path, pset_name)
            pset = ProblemSet(name=pset_name, pdf_path=pdf_path)

            for problem in problem_set["problems"]:
                prob_name = problem["name"]
                note = problem.get("note", "")
                pages = problem.get("pages", "")

                input_data_file = problem.get("input_data_file", str(prob_name).lower() + ".dat")
                output_data_file = problem.get("output_data_file", str(prob_name).lower() + ".out")

                judge_input = ""
                judge_output = ""

                try:
                    judge_input = open(os.path.join(dataout_path, input_data_file), "r").read()
                except FileNotFoundError:
                    print(f"WARNING: problem {prob_name} input file '{input_data_file}' does not exist in {dataout_path}; Input data will be blank")

                try:
                    judge_output = open(os.path.join(dataout_path, output_data_file), "r").read()
                except FileNotFoundError:
                    print(f"ERROR: problem {prob_name} output file '{input_data_file}' does not exist in {dataout_path}; Aborting")

                session.add(Problem(
                    name=prob_name,
                    note=note,
                    pages=pages,
                    input_file_name=input_data_file,
                    judge_input=judge_input,
                    judge_output=judge_output,
                    problem_set=pset
                ))

            session.add(pset)
        
        for contest in setup_config["contests"]:
            contest_name = contest["name"]
            pset = contest.get("problem_set")
            problems = contest.get("problems")
            start_time = contest["start_time"]
            end_time = contest["end_time"]

            contest_problems = []

            if pset is not None:
                contest_problems += session.query(ProblemSet).filter_by(name=pset).first().problems
            if problems is not None:
                for problem_path in problems:
                    problem_set_name = problem_path.split("/")[0]
                    problem_set = session.query(ProblemSet).filter_by(name=problem_set_name).first()
                    problem_name = problem_path.split("/")[1]
                    problem = session.query(Problem).filter_by(problem_set=problem_set, name=problem_name).first()

                    if not problem in contest_problems:
                        contest_problems.append(problem)

            contest = Contest(
                name=contest_name,
                problems=[],
                start_time=start_time,
                end_time=end_time
            )
            session.add(contest)
            session.flush()

            for i in range(len(contest_problems)):
                contest_problem_association = ContestProblemAssociation(problem=contest_problems[i], contest_id=contest.id)
                session.add(contest_problem_association)
                contest.problems.append(contest_problem_association)
            
    session.commit()
    session.close()

setup()