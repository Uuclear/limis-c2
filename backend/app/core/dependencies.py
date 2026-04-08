from typing import Generator
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.exceptions import AuthenticationError
from app.core.security import decode_token
from app.database import SessionLocal
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    payload = decode_token(token)
    if payload is None or payload.get("type") != "access":
        raise AuthenticationError("无效的访问令牌")
    user_id = payload.get("user_id")
    if user_id is None:
        raise AuthenticationError("令牌中缺少用户信息")
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise AuthenticationError("用户不存在")
    if not user.is_active:
        raise AuthenticationError("用户已被禁用")
    return user

def get_current_active_user(user: User = Depends(get_current_user)) -> User:
    return user
