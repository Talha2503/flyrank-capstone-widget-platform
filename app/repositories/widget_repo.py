from sqlalchemy.orm import Session
from app.models.widget import Widget


def create(db: Session, tenant_id: str, data: dict) -> Widget:
    widget = Widget(tenant_id=tenant_id, **data)
    db.add(widget)
    db.commit()
    db.refresh(widget)
    return widget


def get_by_id_for_tenant(db: Session, widget_id: str, tenant_id: str) -> Widget | None:
    return (
        db.query(Widget)
        .filter(Widget.id == widget_id, Widget.tenant_id == tenant_id)
        .first()
    )


def list_for_tenant(db: Session, tenant_id: str) -> list[Widget]:
    return db.query(Widget).filter(Widget.tenant_id == tenant_id).all()


def update(db: Session, widget: Widget, data: dict) -> Widget:
    for key, value in data.items():
        if value is not None:
            setattr(widget, key, value)
    widget.version += 1
    db.commit()
    db.refresh(widget)
    return widget


def delete(db: Session, widget: Widget) -> None:
    db.delete(widget)
    db.commit()