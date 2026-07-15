from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey 
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from flask_login import UserMixin

from typing import List, Optional
import datetime
from datetime import timezone
import zoneinfo

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

class ContestProblemAssociation(Base):
    __tablename__ = "contest_problem_link"
    contest_id: Mapped[int] = mapped_column(ForeignKey("contest.id", ondelete="CASCADE"), primary_key=True)
    problem_id: Mapped[int] = mapped_column(ForeignKey("problem.id", ondelete="CASCADE"), primary_key=True)

    correct_score:     Mapped[int] = mapped_column(default=60)
    incorrect_penalty: Mapped[int] = mapped_column(default=5)
    grading_timeout:   Mapped[float] = mapped_column(default=5.0)

    contest: Mapped["Contest"] = relationship(back_populates="problem_links")
    problem: Mapped["Problem"] = relationship(back_populates="contest_links")

class Settings(db.Model):
    __tablename__ = "settings"

    key:   Mapped[str] = mapped_column(primary_key=True)
    value: Mapped[str]

    def docker_grading_enabled():
        docker_grading = db.session.query(Settings).filter_by(key="docker_grading").first()
        return docker_grading and docker_grading.value.lower() == "true"

class User(UserMixin, db.Model):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True)

    username: Mapped[str]  = mapped_column(unique=True)
    password_hash: Mapped[str]
    is_admin: Mapped[bool] = mapped_column(default=False)

    contest_profiles: Mapped[List["ContestProfile"]] = relationship(back_populates="user") 
    submissions:      Mapped[List["Submission"]]     = relationship(back_populates="user")

    def num_problems_solved(self):
        problems = set()
        submission: Submission
        for submission in self.submissions:
            if submission.valid() and submission.status == 1:
                problems.add(submission.problem.id)
        return len(problems)

    def shallow_serialize(self):
        return {
            "id": self.id,
            "username": self.username,
            "isAdmin": self.is_admin
        }

class ProblemSet(db.Model):
    __tablename__ = "pset"
    
    id: Mapped[int] = mapped_column(primary_key=True)

    name:     Mapped[str]  = mapped_column(unique=True)

    problems: Mapped[List["Problem"]] = relationship(back_populates="pset")

    def get_pdf_name(self):
        return f"pset{self.id}.pdf"

    def serialize(self):
        return self.shallow_serialize() | {
            "problems": [problem.shallow_serialize() for problem in self.problems]
        }

    def shallow_serialize(self):
        return {
            "id": self.id,
            "name": self.name,
        }

class Problem(db.Model):
    __tablename__ = "problem"

    id: Mapped[int] = mapped_column(primary_key=True)

    name:  Mapped[str] = mapped_column()
    note:  Mapped[str] = mapped_column(default="")
    pages: Mapped[str] = mapped_column(default="")

    use_stdin:       Mapped[bool] = mapped_column(default=False)
    input_file_name: Mapped[Optional[str]]
    student_input:   Mapped[str]  = mapped_column(default="")
    judge_input:     Mapped[str]  = mapped_column(default="")
    judge_output:    Mapped[str]  = mapped_column(default="")

    pset_id = mapped_column(ForeignKey("pset.id"), nullable=False)

    pset: Mapped["ProblemSet"]       = relationship(back_populates="problems")
    submissions: Mapped[List["Submission"]] = relationship(back_populates="problem", passive_deletes=True)
    contest_links: Mapped[List["ContestProblemAssociation"]] = relationship(back_populates="problem", passive_deletes=True)

    def serialize(self):
        return self.shallow_serialize() | {
            "pages": self.pages,
            "useStdin": self.use_stdin,
            "inputFileName": self.input_file_name,
            "studentInput": self.student_input,
            "judgeInput": self.judge_input,
            "judgeOutput": self.judge_output,
            "psetID": self.pset_id,
        }

    def shallow_serialize(self):
        return {
            "id": self.id,
            "name": self.name,
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

    problem_id         = mapped_column(ForeignKey("problem.id", ondelete="CASCADE"))
    user_id            = mapped_column(ForeignKey("user.id"))
    contest_profile_id = mapped_column(ForeignKey("contest_profile.id"))

    problem:         Mapped["Problem"]                  = relationship(back_populates="submissions")
    user:            Mapped["User"]                     = relationship(back_populates="submissions")
    contest_profile: Mapped[Optional["ContestProfile"]] = relationship(back_populates="submissions")

    def serialize(self, user=None, admin_view=False):
        io = {} if self.contest_profile and not self.contest_profile.contest.is_past() \
                    and not admin_view else {
            "output": self.output,
            "judgeInput": self.problem.judge_input,
            "judgeOutput": self.problem.judge_output
        }

        code = {} if user and user != self.user and not admin_view else {
            "code": self.code
        }

        return self.shallow_serialize() | io | code

    def shallow_serialize(self):
        return {
            "id": self.id,
            "status": self.status,
            "submitTime": self.submit_time,
            "user": self.user.shallow_serialize(),
            "problem": self.problem.shallow_serialize(),
            "language": self.language
        } | ({} if not self.contest_profile else {"contestProfile": self.contest_profile.shallow_serialize()})

    def valid(self):
        return self.problem is not None


class Contest(db.Model):
    __tablename__ = "contest"

    id: Mapped[int] = mapped_column(primary_key=True)

    name:       Mapped[str]
    start_time: Mapped[datetime.datetime]
    end_time:   Mapped[datetime.datetime]

    allowed_languages: Mapped[str] = mapped_column(default="Java")
    show_leaderboard:  Mapped[bool] = mapped_column(default=True)
    show_pdf:          Mapped[bool] = mapped_column(default=False)

    problem_links:    Mapped[List["ContestProblemAssociation"]] = relationship(back_populates="contest")
    contest_profiles: Mapped[List["ContestProfile"]] = relationship(back_populates="contest")

    def problems(self):
        return [problem_link.problem for problem_link in self.problem_links]

    def is_past(self):
        now = datetime.datetime.now().astimezone(tz=timezone.utc)
        end = self.end_time.replace(tzinfo=zoneinfo.ZoneInfo("UTC"))

        return now > end

    def is_ongoing(self):
        now = datetime.datetime.now().astimezone(tz=timezone.utc)
        start = self.start_time.replace(tzinfo=zoneinfo.ZoneInfo("UTC"))
        end = self.end_time.replace(tzinfo=zoneinfo.ZoneInfo("UTC"))

        return start < now and now < end

    def is_upcoming(self):
        now = datetime.datetime.now().astimezone(tz=timezone.utc)
        start = self.start_time.replace(tzinfo=zoneinfo.ZoneInfo("UTC"))

        return now < start

    def serialize(self):
        return self.shallow_serialize() | {
            "problems": [{
                "problem": problem.shallow_serialize(),
                "correctScore": next((pl.correct_score for pl in self.problem_links if pl.problem_id == problem.id), 60),
                "incorrectPenalty": next((pl.incorrect_penalty for pl in self.problem_links if pl.problem_id == problem.id), 5),
                "gradingTimeout": next((pl.grading_timeout for pl in self.problem_links if pl.problem_id == problem.id), 5)   
            } for problem in self.problems()],
            "contestProfiles": [contest_profile.shallow_serialize() for contest_profile in sorted(self.contest_profiles, key=lambda x: x.score)]
        }

    def shallow_serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "startTime": self.start_time.replace(tzinfo=timezone.utc).isoformat(),
            "endTime": self.end_time.replace(tzinfo=timezone.utc).isoformat(),
            "status": self.is_past() and "past" or self.is_ongoing() and "ongoing" or "upcoming",
            "allowedLanguages": self.allowed_languages,
            "showLeaderboard": self.show_leaderboard,
            "showPdf": self.show_pdf
        }

class ContestProfile(db.Model):
    __tablename__ = "contest_profile"

    id: Mapped[int] = mapped_column(primary_key=True)

    score: Mapped[int] = mapped_column(default=0)

    user_id    = mapped_column(ForeignKey("user.id"), nullable=False)
    contest_id = mapped_column(ForeignKey("contest.id"), nullable=False)

    contest:     Mapped["Contest"]          = relationship(back_populates="contest_profiles")
    user:        Mapped["User"]             = relationship(back_populates="contest_profiles")
    submissions: Mapped[List["Submission"]] = relationship(back_populates="contest_profile")

    def problem_status_list(self):
        # [Problem ID, # Correct, # Incorrect, Correct Score, Incorrect Penalty] 
        problem_status_list = [[0, 0, 0, 0, 0] for _ in range(len(self.contest.problem_links))]

        for idx, problem_link in enumerate(self.contest.problem_links):
            problem_status_list[idx][0] = problem_link.problem.id
            problem_status_list[idx][3] = problem_link.correct_score
            problem_status_list[idx][4] = problem_link.incorrect_penalty

        for submission in self.valid_submissions():
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
            if problem_status[1] > 0:
                score += problem_status[3]
                score -= problem_status[2] * problem_status[4]

        self.score = score
        return score

    def valid_submissions(self):
        return sorted([submission for submission in self.submissions if submission.problem in self.contest.problems()], key=lambda x: x.submit_time, reverse=True)

    def serialize(self):
        return self.shallow_serialize() | {
            "submissions": [submission.shallow_serialize() for submission in self.valid_submissions()]
        }

    def shallow_serialize(self):
        return {
            "id": self.id,
            "score": self.score,
            "user": self.user.shallow_serialize(),
            "contest": self.contest.shallow_serialize(),
        }