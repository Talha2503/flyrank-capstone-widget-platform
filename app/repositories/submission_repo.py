from sqlalchemy.orm import Session
from app.models.submission import Submission


def create(db: Session, data: dict) -> Submission:
    submission = Submission(**data)
    db.add(submission)
    db.commit()
    db.refresh(submission)
    return submission