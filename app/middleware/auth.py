from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.security import decode_access_token

bearer_scheme = HTTPBearer()


def get_current_tenant_id(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> str:
    tenant_id = decode_access_token(credentials.credentials)
    if tenant_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    return tenant_id