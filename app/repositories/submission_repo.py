from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.submission import Submission


def create(db: Session, data: dict) -> Submission:
    submission = Submission(**data)
    db.add(submission)
    db.commit()
    db.refresh(submission)
    return submission


def list_for_widget(db: Session, widget_id: str, tenant_id: str) -> list[Submission]:
    return (
        db.query(Submission)
        .filter(Submission.widget_id == widget_id, Submission.tenant_id == tenant_id)
        .order_by(Submission.created_at.desc())
        .all()
    )


def stats_for_widget(db: Session, widget_id: str, tenant_id: str) -> dict:
    base = db.query(Submission).filter(
        Submission.widget_id == widget_id, Submission.tenant_id == tenant_id
    )

    total = base.count()

    by_country = (
        base.filter(Submission.geo_country.isnot(None))
        .with_entities(Submission.geo_country, func.count(Submission.id))
        .group_by(Submission.geo_country)
        .all()
    )

    by_day = (
        base.with_entities(
            func.date(Submission.created_at), func.count(Submission.id)
        )
        .group_by(func.date(Submission.created_at))
        .order_by(func.date(Submission.created_at))
        .all()
    )

    return {
        "total": total,
        "by_country": [{"country": c, "count": n} for c, n in by_country],
        "by_day": [{"date": str(d), "count": n} for d, n in by_day],
    }


def overview_for_tenant(db: Session, tenant_id: str) -> dict:
    total = db.query(Submission).filter(Submission.tenant_id == tenant_id).count()

    by_widget = (
        db.query(Submission)
        .filter(Submission.tenant_id == tenant_id)
        .with_entities(Submission.widget_id, func.count(Submission.id))
        .group_by(Submission.widget_id)
        .all()
    )

    return {
        "total_submissions": total,
        "by_widget": [{"widget_id": str(w), "count": n} for w, n in by_widget],
    }