from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import DateTime, ForeignKey, Table, Column, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from flask_login import UserMixin
from typing import List, Optional
import datetime
from datetime import timezone

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

class ContestProblemAssociation(Base):
    __tablename__ = "contest_problem_link"
    contest_id: Mapped[int] = mapped_column(ForeignKey("contest.id"), primary_key=True)
    problem_id: Mapped[int] = mapped_column(ForeignKey("problem.id"), primary_key=True)
    correct_score: Mapped[int] = mapped_column(default=60)
    incorrect_penalty: Mapped[int] = mapped_column(default=5)
    problem: Mapped["Problem"] = relationship()

class User(UserMixin, db.Model):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True)

    username:   Mapped[str] = mapped_column(unique=True)
    passphrase: Mapped[str]

    is_admin:      Mapped[bool] = mapped_column(default=False)
    password_hash: Mapped[Optional[str]]

    contest_profiles: Mapped[List["ContestProfile"]] = relationship(back_populates="user") 
    submissions:      Mapped[List["Submission"]]     = relationship(back_populates="user")

    def serialize(self):
        return self.shallow_serialize() | {
            "passphrase": self.passphrase,
            "is_admin": self.is_admin
        }

    def shallow_serialize(self):
        return {
            "id": self.id,
            "username": self.username
        }

class ProblemSet(db.Model):
    __tablename__ = "problem_set"
    
    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(unique=True)
    pdf_path: Mapped[str] = mapped_column(default="")

    problems: Mapped[List["Problem"]] = relationship(back_populates="problem_set")

    def serialize(self):
        return self.shallow_serialize() | {
            "problems": [problem.shallow_serialize() for problem in self.problems]
        }

    def shallow_serialize(self):
        return {
            "id": self.id,
            "name": self.name
        }

class Problem(db.Model):
    __tablename__ = "problem"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str]
    note: Mapped[str] = mapped_column(default="")
    pages: Mapped[str] = mapped_column(default="")

    use_stdin:       Mapped[bool] = mapped_column(default=False)
    input_file_name: Mapped[Optional[str]]
    judge_input:     Mapped[str]  = mapped_column(default="")
    judge_output:    Mapped[str]  = mapped_column(default="")
    output:          Mapped[str]  = mapped_column(default="")

    is_precontest:   Mapped[bool] = mapped_column(default=False)
    correct_score:   Mapped[int]  = mapped_column(default=60)
    incorrect_score: Mapped[int]  = mapped_column(default=-5)

    problem_set_id = mapped_column(ForeignKey("problem_set.id"))

    problem_set: Mapped["ProblemSet"]       = relationship(back_populates="problems")
    submissions: Mapped[List["Submission"]] = relationship(back_populates="problem")

    def shallow_serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "is_precontest": self.is_precontest,
        }

class Submission(db.Model):
    __tablename__ = "submission"

    # Submission Status Legend:
    # 0 = Pending
    # 1 = Accepted
    # 2 = Wrong Answer
    # 3 = Compilation Error
    # 4 = Runtime Error
    # 5 = Time Limit Exceeded
    # 6 = Memory Limit Exceeded
    # 7 = Server Error

    id: Mapped[int] = mapped_column(primary_key=True)

    status:      Mapped[int] = mapped_column(default=0)
    submit_time: Mapped[datetime.datetime]
    code:        Mapped[str]
    output:      Mapped[str] = mapped_column(default="")
    language:    Mapped[str]

    problem_id         = mapped_column(ForeignKey("problem.id"))
    user_id            = mapped_column(ForeignKey("user.id"))
    contest_profile_id = mapped_column(ForeignKey("contest_profile.id"))

    problem:         Mapped["Problem"]                  = relationship(back_populates="submissions")
    user:            Mapped["User"]                     = relationship(back_populates="submissions")
    contest_profile: Mapped[Optional["ContestProfile"]] = relationship(back_populates="submissions")

    def serialize(self, admin_view=False):
        output = {} if self.contest_profile and not self.contest_profile.contest.past() and not admin_view else {"output": self.output}

        return self.shallow_serialize() | output | {
            "code": self.code
        }

    def shallow_serialize(self):
        return {
            "id": self.id,
            "status": self.status,
            "submit_time": self.submit_time,
            "user": self.user.shallow_serialize(),
            "problem": self.problem.shallow_serialize(),
            "language": self.language
        } | ({} if self.contest_profile is None else {"contest_profile": self.contest_profile.shallow_serialize()})


class Contest(db.Model):
    __tablename__ = "contest"

    id: Mapped[int] = mapped_column(primary_key=True)

    name:       Mapped[str]
    start_time: Mapped[datetime.datetime]
    end_time:   Mapped[datetime.datetime]

    problem_links:         Mapped[List["ContestProblemAssociation"]] = relationship()
    contest_profiles: Mapped[List["ContestProfile"]] = relationship(back_populates="contest")

    def problems(self):
        return [problem_link.problem for problem_link in self.problem_links]

    def past(self):
        return datetime.datetime.now() > self.end_time

    def ongoing(self):
        return self.start_time < datetime.datetime.now() and datetime.datetime.now() < self.end_time

    def upcoming(self):
        return datetime.datetime.now() < self.start_time

    def serialize(self):
        return self.shallow_serialize() | {
            "problems": [problem.shallow_serialize() for problem in sorted(self.problems(), key=lambda x: x.name)],
            "contest_profiles": [contest_profile.shallow_serialize() for contest_profile in sorted(self.contest_profiles, key=lambda x: x.score)]
        }

    def shallow_serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "start_time": self.start_time.replace(tzinfo=timezone.utc).isoformat(),
            "end_time": self.end_time.replace(tzinfo=timezone.utc).isoformat(),
            "status": self.past() and "past" or self.ongoing() and "ongoing" or "upcoming"
        }

class ContestProfile(db.Model):
    __tablename__ = "contest_profile"

    id: Mapped[int] = mapped_column(primary_key=True)

    score: Mapped[int] = mapped_column(default=0)

    user_id    = mapped_column(ForeignKey("user.id"))
    contest_id = mapped_column(ForeignKey("contest.id"))

    contest:     Mapped["Contest"]          = relationship(back_populates="contest_profiles")
    user:        Mapped["User"]             = relationship(back_populates="contest_profiles")
    submissions: Mapped[List["Submission"]] = relationship(back_populates="contest_profile")

    def problem_status_list(self):
        problem_status_list = [[0, 0, 0, 0, 0] for _ in range(len(self.contest.problem_links))]

        for idx, problem_link in enumerate(self.contest.problem_links):
            problem_status_list[idx][0] = problem_link.problem.id
            problem_status_list[idx][3] = problem_link.correct_score
            problem_status_list[idx][4] = problem_link.incorrect_penalty

        for submission in self.submissions:
            problem_idx = None
            for idx, problem_link in enumerate(self.contest.problem_links):
                if problem_link.problem.id == submission.problem.id:
                    problem_idx = idx
                    break
                    
            if submission.status == 1:
                problem_status_list[problem_idx][1] += 1
            elif submission.status != 0:
                problem_status_list[problem_idx][2] += 1

        return problem_status_list

    def calculate_score(self):
        score = 0

        for problem_status in self.problem_status_list():
            problem_link = db.session.query(ContestProblemAssociation).filter_by(contest_id=self.contest_id, problem_id=problem_status[0]).first()

            if problem_status[1] > 0:
                score += problem_link.correct_score
                score -= problem_status[2] * problem_link.incorrect_penalty

        self.score = score
        return score

    def serialize(self):
        return self.shallow_serialize() | {
            "submissions": [submission.shallow_serialize() for submission in self.submissions]
        }

    def shallow_serialize(self):
        return {
            "id": self.id,
            "score": self.score,
            "user": self.user.shallow_serialize(),
            "contest": self.contest.shallow_serialize(),
        }