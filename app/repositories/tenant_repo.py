from sqlalchemy.orm import Session
from app.models.tenant import Tenant


def get_by_email(db: Session, email: str) -> Tenant | None:
    return db.query(Tenant).filter(Tenant.email == email).first()


def get_by_id(db: Session, tenant_id: str) -> Tenant | None:
    return db.query(Tenant).filter(Tenant.id == tenant_id).first()


def create(db: Session, email: str, password_hash: str) -> Tenant:
    tenant = Tenant(email=email, password_hash=password_hash)
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return tenant