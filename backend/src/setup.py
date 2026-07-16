import yaml
import sqlalchemy
from werkzeug.security import generate_password_hash 
from sqlalchemy.orm import Session

import os
import shutil

from src.models.orm import *
from src.utils import log

db_name = "main.db"
pdfs_path = "pdfs"

setup_file_name = "setup.yaml"
setup_psets_path = "psets"
setup_pdfs_path = "pdfs"
setup_student_data_path = "student_data"

def init_new_db():
    if os.path.exists(db_name):
        print(f"{db_name} already exists! Use setup to make an entirely new database.")
        return False

    engine = sqlalchemy.create_engine(
        f"sqlite:///{db_name}", 
        connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(engine)
    session: Session = Session(engine)
    
    session.add(Settings(key="docker_grading", value="false"))
    session.commit()
    session.close()

    return True


def import_from_directory(import_dir):
    pset_count = 0

    from src.app import app

    with app.app_context():
        with open(os.path.join(import_dir, setup_file_name), "r") as setup_file:
            document = setup_file.read()
            setup_config = yaml.safe_load(document)

            docker_grading = setup_config.get("docker_grading", False)

            db.session.merge(Settings(key="docker_grading", value="true" if docker_grading else "false"))

            for user_config in setup_config["users"]:
                username = user_config["username"]
                password = user_config["password"]
                is_admin = user_config.get("admin", False)

                existing_user = db.session.query(User).filter_by(username=username).first()
                if existing_user is not None:
                    db.session.merge(User(id=existing_user.id, username=username, password_hash=generate_password_hash(password), is_admin=is_admin))
                else:
                    db.session.add(User(username=username, password_hash=generate_password_hash(password), is_admin=is_admin))

            for pset_config in setup_config["psets"]:
                pset_name = pset_config["name"]

                existing_pset = db.session.query(ProblemSet).filter_by(name=pset_name).first()

                pset_pdf_path = pset_config.get("pdf_path", "")
                student_input_path = os.path.join(import_dir, setup_psets_path, pset_name, setup_student_data_path)
                judge_io_path = os.path.join(import_dir, setup_psets_path, pset_name)
                pset = existing_pset if existing_pset else ProblemSet(name=pset_name)

                for problem in pset_config["problems"]:
                    problem_name = problem["name"]
                    note = problem.get("note", "")
                    pages = problem.get("pages", "")
                    use_stdin = problem.get("use_stdin", False)

                    input_data_file = problem.get("input_data_file", str(problem_name).lower() + ".dat")
                    output_data_file = problem.get("output_data_file", str(problem_name).lower() + ".out")
                    student_data_file = problem.get("student_input_file", input_data_file)

                    student_input = ""
                    judge_input = ""
                    judge_output = ""

                    try:
                        student_input = open(os.path.join(student_input_path, student_data_file), "r").read()
                    except FileNotFoundError:
                        log.warning(f"Problem {problem_name} student input file '{student_data_file}' does not exist in {student_input_path}; Student input data will be blank")

                    try:
                        judge_input = open(os.path.join(judge_io_path, input_data_file), "r").read()
                    except FileNotFoundError:
                        log.warning(f"Problem {problem_name} input file '{input_data_file}' does not exist in {judge_io_path}; Input data will be blank")

                    try:
                        judge_output = open(os.path.join(judge_io_path, output_data_file), "r").read()
                    except FileNotFoundError:
                        log.error(f"Problem {problem_name} output file '{output_data_file}' does not exist in {judge_io_path}; Aborting")

                    existing_problem = db.session.query(Problem).filter_by(name=problem_name).first() if existing_pset else None

                    if existing_problem:
                        db.session.merge(Problem(
                            id=existing_problem.id,
                            name=problem_name,
                            note=note,
                            pages=pages,
                            use_stdin=use_stdin,
                            input_file_name=input_data_file,
                            student_input=student_input,
                            judge_input=judge_input,
                            judge_output=judge_output,
                            pset=pset
                        ))
                    else:
                        db.session.add(Problem(
                            name=problem_name,
                            note=note,
                            pages=pages,
                            use_stdin=use_stdin,
                            input_file_name=input_data_file,
                            student_input=student_input,
                            judge_input=judge_input,
                            judge_output=judge_output,
                            pset=pset
                        ))

                db.session.add(pset)
                db.session.commit()

                if not os.path.exists(pdfs_path):
                    os.mkdir(pdfs_path)
                shutil.copyfile(os.path.join(import_dir, setup_pdfs_path, pset_pdf_path), os.path.join(pdfs_path, pset.get_pdf_name()))

                if not existing_pset:
                    pset_count += 1

        log.info(f"Successfully imported {pset_count} new problem set(s)")
        return pset_count

def export_psets(export_dir):
    pdfs_dir = os.path.join(export_dir, setup_pdfs_path)
    psets_dir = os.path.join(export_dir, setup_psets_path)
    setup_file_path = os.path.join(export_dir, setup_file_name)

    os.mkdir(export_dir)
    os.mkdir(pdfs_dir)
    os.mkdir(psets_dir)

    psets = db.session.query(ProblemSet).all()
    psets_json = []
    
    for pset in psets:
        pset_dir = os.path.join(psets_dir, pset.name)
        student_data_dir = os.path.join(pset_dir, "student_data")

        os.mkdir(pset_dir)
        os.mkdir(student_data_dir)

        psets_json.append({
            "name": pset.name,
            "pdf_path": pset.get_pdf_name(),
            "problems": [{
                "name": problem.name,
                "note": problem.note,
                "pages": problem.pages,
                "use_stdin": problem.use_stdin,
                "student_data_file": problem.input_file_name,
                "input_data_file": problem.input_file_name,
                "output_data_file": os.path.splitext(problem.input_file_name)[0] + ".out" 
            } for problem in pset.problems]
        })

        for problem in pset.problems:
            output_file_name = os.path.splitext(problem.input_file_name)[0] + ".out"

            if len(problem.student_input) > 0:
                with open(os.path.join(student_data_dir, problem.input_file_name), "w") as f:
                    f.write(problem.student_input)
            
            if len(problem.judge_input) > 0:
                with open(os.path.join(pset_dir, problem.input_file_name), "w") as f:
                    f.write(problem.judge_input)

            with open(os.path.join(pset_dir, output_file_name), "w") as f:
                f.write(problem.judge_output)

        shutil.copyfile(os.path.join("pdfs", pset.get_pdf_name()), os.path.join(pdfs_dir, pset.get_pdf_name()))

    setup_config = {
        "psets": psets_json 
    }

    with open(setup_file_path, "w") as f:
        yaml.dump(setup_config, f)

    shutil.make_archive(export_dir, "zip", export_dir)