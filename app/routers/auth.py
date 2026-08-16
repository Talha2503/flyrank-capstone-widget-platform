from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.schemas import SignupRequest, LoginRequest, TokenResponse
from app.repositories import tenant_repo
from app.security import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    existing = tenant_repo.get_by_email(db, payload.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    tenant = tenant_repo.create(db, payload.email, hash_password(payload.password))
    token = create_access_token(str(tenant.id))
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    tenant = tenant_repo.get_by_email(db, payload.email)
    if not tenant or not verify_password(payload.password, tenant.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token(str(tenant.id))
    return TokenResponse(access_token=token)