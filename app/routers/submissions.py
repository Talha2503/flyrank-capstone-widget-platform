from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.database import get_db
from app.models.schemas import SubmissionCreate, SubmissionResponse
from app.repositories import widget_repo, submission_repo
from app.integrations.geo import enrich_ip

router = APIRouter(tags=["submissions"])

MAX_PAYLOAD_FIELDS = 30
MAX_FIELD_VALUE_LENGTH = 2000

limiter = Limiter(key_func=get_remote_address)


@router.post("/submissions", response_model=SubmissionResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
def create_submission(payload: SubmissionCreate, request: Request, db: Session = Depends(get_db)):
    if payload.website.strip():
        return SubmissionResponse(
            id="00000000-0000-0000-0000-000000000000",
            widget_id=payload.widget_id,
            created_at="1970-01-01T00:00:00Z",
        )

    widget = widget_repo.get_by_id_public(db, payload.widget_id)
    if widget is None:
        raise HTTPException(status_code=404, detail="Widget not found")

    if len(payload.data) > MAX_PAYLOAD_FIELDS:
        raise HTTPException(status_code=413, detail="Too many fields in submission")

    for key, value in payload.data.items():
        if not isinstance(value, str):
            raise HTTPException(status_code=400, detail=f"Field '{key}' must be a string")
        if len(value) > MAX_FIELD_VALUE_LENGTH:
            raise HTTPException(status_code=413, detail=f"Field '{key}' is too long")

    for field_def in widget.fields:
        if field_def.get("required") and not payload.data.get(field_def["name"], "").strip():
            raise HTTPException(status_code=400, detail=f"Field '{field_def['name']}' is required")

    client_ip = request.headers.get("X-Debug-IP") or (request.client.host if request.client else None)

    # Enrichment is a courtesy, never a requirement -- enrich_ip() never
    # raises, and its failure/unavailability must not block storage.
    geo = enrich_ip(client_ip)

    submission = submission_repo.create(db, {
        "widget_id": widget.id,
        "tenant_id": widget.tenant_id,
        "data": payload.data,
        "ip_address": client_ip,
        "geo_country": geo["country"],
        "geo_city": geo["city"],
        "geo_provider_used": geo["provider_used"],
    })

    return submission