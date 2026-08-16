from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.middleware.auth import get_current_tenant_id
from app.models.schemas import WidgetCreate, WidgetUpdate, WidgetResponse
from app.repositories import widget_repo

router = APIRouter(prefix="/api/widgets", tags=["widgets"])


@router.post("", response_model=WidgetResponse, status_code=status.HTTP_201_CREATED)
def create_widget(
    payload: WidgetCreate,
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    data = payload.model_dump()
    data["fields"] = [f for f in data["fields"]]  # plain dicts for JSON column
    widget = widget_repo.create(db, tenant_id, data)
    return widget


@router.get("", response_model=list[WidgetResponse])
def list_widgets(
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    return widget_repo.list_for_tenant(db, tenant_id)


@router.get("/{widget_id}", response_model=WidgetResponse)
def get_widget(
    widget_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    widget = widget_repo.get_by_id_for_tenant(db, widget_id, tenant_id)
    if widget is None:
        raise HTTPException(status_code=404, detail="Widget not found")
    return widget


@router.put("/{widget_id}", response_model=WidgetResponse)
def update_widget(
    widget_id: str,
    payload: WidgetUpdate,
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    widget = widget_repo.get_by_id_for_tenant(db, widget_id, tenant_id)
    if widget is None:
        raise HTTPException(status_code=404, detail="Widget not found")

    data = payload.model_dump(exclude_unset=True)
    if "fields" in data and data["fields"] is not None:
        data["fields"] = [f for f in data["fields"]]

    return widget_repo.update(db, widget, data)


@router.delete("/{widget_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_widget(
    widget_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    widget = widget_repo.get_by_id_for_tenant(db, widget_id, tenant_id)
    if widget is None:
        raise HTTPException(status_code=404, detail="Widget not found")
    widget_repo.delete(db, widget)


@router.get("/{widget_id}/embed")
def get_embed_snippet(
    widget_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    widget = widget_repo.get_by_id_for_tenant(db, widget_id, tenant_id)
    if widget is None:
        raise HTTPException(status_code=404, detail="Widget not found")

    snippet = f'<script src="http://localhost:8000/widget.js?id={widget.id}"></script>'
    return {"snippet": snippet}