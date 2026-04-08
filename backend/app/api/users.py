from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.core.exceptions import BadRequestError, NotFoundError
from app.core.permissions import require_roles
from app.core.security import hash_password
from app.models.user import Department, Role, User
from app.schemas.user import (
    DepartmentCreate,
    DepartmentResponse,
    PasswordReset,
    RoleCreate,
    RoleResponse,
    UserCreate,
    UserResponse,
    UserUpdate,
)

router = APIRouter(prefix="/api", tags=["用户管理"])


# --- Users ---
@router.get("/users", response_model=list[UserResponse])
def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: str = "",
    is_active: bool | None = None,
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles("admin", "lab_director")),
):
    query = db.query(User)
    if keyword:
        query = query.filter(
            User.username.ilike(f"%{keyword}%") | User.real_name.ilike(f"%{keyword}%")
        )
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    users = query.offset((page - 1) * page_size).limit(page_size).all()
    return users


@router.post("/users", response_model=UserResponse)
def create_user(
    data: UserCreate,
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles("admin")),
):
    if db.query(User).filter(User.username == data.username).first():
        raise BadRequestError("用户名已存在")
    user = User(
        username=data.username,
        hashed_password=hash_password(data.password),
        real_name=data.real_name,
        email=data.email,
        phone=data.phone,
        department_id=data.department_id,
    )
    if data.role_ids:
        roles = db.query(Role).filter(Role.id.in_(data.role_ids)).all()
        user.roles = roles
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles("admin", "lab_director")),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise NotFoundError("用户不存在")
    return user


@router.put("/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    data: UserUpdate,
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles("admin")),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise NotFoundError("用户不存在")
    for field, value in data.model_dump(exclude_unset=True, exclude={"role_ids"}).items():
        setattr(user, field, value)
    if data.role_ids is not None:
        roles = db.query(Role).filter(Role.id.in_(data.role_ids)).all()
        user.roles = roles
    db.commit()
    db.refresh(user)
    return user


@router.post("/users/{user_id}/reset-password")
def reset_password(
    user_id: int,
    data: PasswordReset,
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles("admin")),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise NotFoundError("用户不存在")
    user.hashed_password = hash_password(data.new_password)
    db.commit()
    return {"message": "密码重置成功"}


# --- Roles ---
@router.get("/roles", response_model=list[RoleResponse])
def list_roles(
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles("admin")),
):
    return db.query(Role).all()


@router.post("/roles", response_model=RoleResponse)
def create_role(
    data: RoleCreate,
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles("admin")),
):
    if db.query(Role).filter(Role.name == data.name).first():
        raise BadRequestError("角色名已存在")
    role = Role(**data.model_dump())
    db.add(role)
    db.commit()
    db.refresh(role)
    return role


# --- Departments ---
@router.get("/departments", response_model=list[DepartmentResponse])
def list_departments(
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles("admin", "lab_director")),
):
    return db.query(Department).order_by(Department.sort_order).all()


@router.post("/departments", response_model=DepartmentResponse)
def create_department(
    data: DepartmentCreate,
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles("admin")),
):
    dept = Department(**data.model_dump())
    db.add(dept)
    db.commit()
    db.refresh(dept)
    return dept
