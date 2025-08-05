from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from flask_login import UserMixin
from typing import List, Optional
import datetime

class Base(DeclarativeBase):
    pass

class User(UserMixin, Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True)

    username: Mapped[str] = mapped_column(unique=True)
    passphrase: Mapped[str]

    is_admin: Mapped[bool] = mapped_column(default=False)
    password_hash: Mapped[Optional[str]]

    contest_profiles: Mapped[List["ContestProfile"]] = relationship(back_populates="user") 
    submissions:      Mapped[List["Submission"]]     = relationship(back_populates="user")

class ProblemSet(Base):
    __tablename__ = "problem_set"
    
    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(unique=True)

    problems: Mapped[List["Problem"]] = relationship(back_populates="problem_set")
    contests: Mapped[List["Contest"]] = relationship(back_populates="problem_set")

class Problem(Base):
    __tablename__ = "problem"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str]
    note: Mapped[str] = mapped_column(default="")

    use_stdin: Mapped[bool] = mapped_column(default=False)
    input_file_name: Mapped[Optional[str]]
    judge_input: Mapped[str] = mapped_column(default="")
    judge_output: Mapped[str] = mapped_column(default="")

    is_precontest: Mapped[bool] = mapped_column(default=False)
    correct_score: Mapped[int] = mapped_column(default=60)
    incorrect_score: Mapped[int] = mapped_column(default=-5)

    problem_set_id = mapped_column(ForeignKey("problem_set.id"))

    problem_set: Mapped["ProblemSet"]       = relationship(back_populates="problems")
    submissions: Mapped[List["Submission"]] = relationship(back_populates="problem")

class Submission(Base):
    __tablename__ = "submission"

    # Submission Status Legend:
    # 0 = Pending
    # 1 = Accepted
    # 2 = Wrong Answer
    # 3 = Time Limit Exceeded
    # 4 = Memory Limit Exceeded
    # 5 = Server Error

    id: Mapped[int] = mapped_column(primary_key=True)

    status: Mapped[int] = mapped_column(default=0)
    submit_time: Mapped[datetime.datetime]
    filename: Mapped[str]
    code: Mapped[str]
    output: Mapped[str]

    problem_id = mapped_column(ForeignKey("problem.id"))
    user_id = mapped_column(ForeignKey("user.id"))
    contest_profile_id = mapped_column(ForeignKey("contest_profile.id"))

    problem:         Mapped["Problem"]                  = relationship(back_populates="submissions")
    user:            Mapped["User"]                     = relationship(back_populates="submissions")
    contest_profile: Mapped[Optional["ContestProfile"]] = relationship(back_populates="submissions")

class Contest(Base):
    __tablename__ = "contest"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str]
    start_time: Mapped[datetime.datetime]
    end_time: Mapped[datetime.datetime]

    problem_set_id = mapped_column(ForeignKey("problem_set.id"))

    problem_set:      Mapped["ProblemSet"]           = relationship(back_populates="contests")
    contest_profiles: Mapped[List["ContestProfile"]] = relationship(back_populates="contest")

class ContestProfile(Base):
    __tablename__ = "contest_profile"

    id: Mapped[int] = mapped_column(primary_key=True)

    score: Mapped[int] = mapped_column(default=0)

    user_id    = mapped_column(ForeignKey("user.id"))
    contest_id = mapped_column(ForeignKey("contest.id"))

    contest:     Mapped["Contest"]          = relationship(back_populates="contest_profiles")
    user:        Mapped["User"]             = relationship(back_populates="contest_profiles")
    submissions: Mapped[List["Submission"]] = relationship(back_populates="contest_profile")