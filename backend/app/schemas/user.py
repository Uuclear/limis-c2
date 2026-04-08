from datetime import datetime
from pydantic import BaseModel

# --- Auth ---
class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshRequest(BaseModel):
    refresh_token: str

# --- Role ---
class RoleBase(BaseModel):
    name: str
    display_name: str
    description: str | None = None

class RoleCreate(RoleBase):
    pass

class RoleResponse(RoleBase):
    id: int
    model_config = {"from_attributes": True}

# --- Permission ---
class PermissionResponse(BaseModel):
    id: int
    code: str
    name: str
    module: str
    model_config = {"from_attributes": True}

# --- Department ---
class DepartmentBase(BaseModel):
    name: str
    parent_id: int | None = None
    sort_order: int = 0

class DepartmentCreate(DepartmentBase):
    pass

class DepartmentResponse(DepartmentBase):
    id: int
    model_config = {"from_attributes": True}

# --- User ---
class UserBase(BaseModel):
    username: str
    real_name: str
    email: str | None = None
    phone: str | None = None
    department_id: int | None = None

class UserCreate(UserBase):
    password: str
    role_ids: list[int] = []

class UserUpdate(BaseModel):
    real_name: str | None = None
    email: str | None = None
    phone: str | None = None
    department_id: int | None = None
    is_active: bool | None = None
    role_ids: list[int] | None = None

class PasswordReset(BaseModel):
    new_password: str

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime | None = None
    roles: list[RoleResponse] = []
    model_config = {"from_attributes": True}

class UserMeResponse(BaseModel):
    id: int
    username: str
    real_name: str
    roles: list[RoleResponse] = []
    permissions: list[str] = []
    model_config = {"from_attributes": True}
