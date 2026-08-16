from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.schemas import SubmissionCreate, SubmissionResponse
from app.repositories import widget_repo, submission_repo

router = APIRouter(tags=["submissions"])

MAX_PAYLOAD_FIELDS = 30
MAX_FIELD_VALUE_LENGTH = 2000


@router.post("/submissions", response_model=SubmissionResponse, status_code=status.HTTP_201_CREATED)
def create_submission(payload: SubmissionCreate, request: Request, db: Session = Depends(get_db)):
    # 1. Validate the widget exists at all
    widget = widget_repo.get_by_id_public(db, payload.widget_id)
    if widget is None:
        raise HTTPException(status_code=404, detail="Widget not found")

    # 2. Reject oversized payloads before touching business logic
    if len(payload.data) > MAX_PAYLOAD_FIELDS:
        raise HTTPException(status_code=413, detail="Too many fields in submission")

    for key, value in payload.data.items():
        if not isinstance(value, str):
            raise HTTPException(status_code=400, detail=f"Field '{key}' must be a string")
        if len(value) > MAX_FIELD_VALUE_LENGTH:
            raise HTTPException(status_code=413, detail=f"Field '{key}' is too long")

    # 3. Validate required fields from the widget's own config are present
    for field_def in widget.fields:
        if field_def.get("required") and not payload.data.get(field_def["name"], "").strip():
            raise HTTPException(status_code=400, detail=f"Field '{field_def['name']}' is required")

    client_ip = request.client.host if request.client else None

    submission = submission_repo.create(db, {
        "widget_id": widget.id,
        "tenant_id": widget.tenant_id,
        "data": payload.data,
        "ip_address": client_ip,
    })

    return submission