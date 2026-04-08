from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.user import LoginRequest, RefreshRequest, TokenResponse, UserMeResponse
from app.services.auth_service import authenticate_user, create_tokens, refresh_access_token

router = APIRouter(prefix="/api/auth", tags=["认证"])


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(db, request.username, request.password)
    return create_tokens(user)


@router.post("/refresh", response_model=TokenResponse)
def refresh(request: RefreshRequest):
    return refresh_access_token(request.refresh_token)


@router.get("/me", response_model=UserMeResponse)
def get_me(user: User = Depends(get_current_user)):
    permissions = set()
    for role in user.roles:
        for perm in role.permissions:
            permissions.add(perm.code)
    return UserMeResponse(
        id=user.id,
        username=user.username,
        real_name=user.real_name,
        roles=user.roles,
        permissions=sorted(permissions),
    )
