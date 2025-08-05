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

        use_practice = setup_config["use_practice"]
        branch = setup_config["branch"]

        for user in setup_config["users"]:
            username = user["username"]
            password = user["password"]

            session.add(User(username=username, passphrase=password))

        for problem_set in setup_config["problem_sets"]:
            pset_name = problem_set["name"]
            pset = ProblemSet(name=pset_name)

            for problem in problem_set["problems"]:
                prob_name = problem["name"]

                input_data_file = problem["input_data_file"]
                output_data_file = problem["output_data_file"]

                judge_input = open(os.path.join(problem_set_path, pset_name, input_data_file), "r").read()
                judge_output = open(os.path.join(problem_set_path, pset_name, output_data_file), "r").read()

                session.add(Problem(
                    name=prob_name,
                    input_file_name=input_data_file,
                    judge_input=judge_input,
                    judge_output=judge_output,
                    problem_set=pset
                ))

            session.add(pset)
        
        for contest in setup_config["contests"]:
            contest_name = contest["name"]
            pset = contest["problem_set"]
            start_time = contest["start_time"]
            end_time = contest["end_time"]

            session.add(Contest(
                name=contest_name,
                problem_set=session.query(ProblemSet).filter_by(name=pset).first(),
                start_time=start_time,
                end_time=end_time
            ))
            
    session.commit()
    session.close()

setup()