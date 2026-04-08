from typing import Callable
from fastapi import Depends
from app.core.dependencies import get_current_user
from app.core.exceptions import PermissionDeniedError
from app.models.user import User

def require_permissions(*required_perms: str) -> Callable:
    def checker(user: User = Depends(get_current_user)) -> User:
        user_perms = set()
        for role in user.roles:
            for perm in role.permissions:
                user_perms.add(perm.code)
        role_names = {role.name for role in user.roles}
        if "admin" in role_names:
            return user
        missing = set(required_perms) - user_perms
        if missing:
            raise PermissionDeniedError(f"缺少权限: {', '.join(missing)}")
        return user
    return checker

def require_roles(*required_roles: str) -> Callable:
    def checker(user: User = Depends(get_current_user)) -> User:
        user_roles = {role.name for role in user.roles}
        if not user_roles & set(required_roles):
            raise PermissionDeniedError(f"需要以下角色之一: {', '.join(required_roles)}")
        return user
    return checker
