from sqlalchemy.orm import Session

from app.core.exceptions import AuthenticationError
from app.core.security import create_access_token, create_refresh_token, decode_token, verify_password
from app.models.user import User


def authenticate_user(db: Session, username: str, password: str) -> User:
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        raise AuthenticationError("用户名或密码错误")
    if not user.is_active:
        raise AuthenticationError("用户已被禁用")
    return user


def create_tokens(user: User) -> dict:
    token_data = {"sub": user.username, "user_id": user.id}
    return {
        "access_token": create_access_token(token_data),
        "refresh_token": create_refresh_token(token_data),
        "token_type": "bearer",
    }


def refresh_access_token(refresh_token: str) -> dict:
    payload = decode_token(refresh_token)
    if payload is None or payload.get("type") != "refresh":
        raise AuthenticationError("无效的刷新令牌")
    token_data = {"sub": payload["sub"], "user_id": payload["user_id"]}
    return {
        "access_token": create_access_token(token_data),
        "refresh_token": create_refresh_token(token_data),
        "token_type": "bearer",
    }
