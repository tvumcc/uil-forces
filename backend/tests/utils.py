import datetime
from datetime import timezone
import pypdf
import os

from src.models.orm import *
from src.judge import Status

def make_submission(user, problem, contest_profile=None, status=Status.Accepted.value, code="print(1)", language="Java", minutes_ago=0):
    submission = Submission(
        problem=problem,
        user=user,
        contest_profile=contest_profile,
        status=status,
        code=code,
        language=language,
        submit_time=datetime.datetime.now(timezone.utc) - datetime.timedelta(minutes=minutes_ago),
    )
    db.session.add(submission)
    db.session.commit()
    return submission

def make_profile(user, contest):
    profile = ContestProfile(user=user, contest=contest)
    db.session.add(profile)
    db.session.commit()
    return profile

def write_minimal_pdf(path, num_pages=1):
    writer = pypdf.PdfWriter()
    for _ in range(num_pages):
        writer.add_blank_page(width=200, height=200)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        writer.write(f)