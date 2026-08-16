from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.middleware.auth import get_current_tenant_id
from app.models.schemas import SubmissionListItem
from app.repositories import widget_repo, submission_repo

router = APIRouter(prefix="/api", tags=["dashboard"])


@router.get("/widgets/{widget_id}/submissions", response_model=list[SubmissionListItem])
def get_widget_submissions(
    widget_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    # Confirm the widget actually belongs to this tenant before listing --
    # same isolation pattern as widget CRUD.
    widget = widget_repo.get_by_id_for_tenant(db, widget_id, tenant_id)
    if widget is None:
        raise HTTPException(status_code=404, detail="Widget not found")

    return submission_repo.list_for_widget(db, widget_id, tenant_id)


@router.get("/widgets/{widget_id}/stats")
def get_widget_stats(
    widget_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    widget = widget_repo.get_by_id_for_tenant(db, widget_id, tenant_id)
    if widget is None:
        raise HTTPException(status_code=404, detail="Widget not found")

    return submission_repo.stats_for_widget(db, widget_id, tenant_id)


@router.get("/dashboard/overview")
def get_dashboard_overview(
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    return submission_repo.overview_for_tenant(db, tenant_id)