from datetime import datetime
from pydantic import BaseModel


# --- SubItem (分项工程) ---
class SubItemBase(BaseModel):
    name: str
    code: str
    description: str | None = None

class SubItemCreate(SubItemBase):
    division_id: int

class SubItemUpdate(BaseModel):
    name: str | None = None
    code: str | None = None
    description: str | None = None

class SubItemResponse(SubItemBase):
    id: int
    division_id: int
    created_at: datetime | None = None
    model_config = {"from_attributes": True}


# --- Division (分部工程) ---
class DivisionBase(BaseModel):
    name: str
    code: str
    description: str | None = None

class DivisionCreate(DivisionBase):
    unit_project_id: int

class DivisionUpdate(BaseModel):
    name: str | None = None
    code: str | None = None
    description: str | None = None

class DivisionResponse(DivisionBase):
    id: int
    unit_project_id: int
    created_at: datetime | None = None
    sub_items: list[SubItemResponse] = []
    model_config = {"from_attributes": True}


# --- UnitProject (单位工程) ---
class UnitProjectBase(BaseModel):
    name: str
    code: str
    description: str | None = None

class UnitProjectCreate(UnitProjectBase):
    project_id: int

class UnitProjectUpdate(BaseModel):
    name: str | None = None
    code: str | None = None
    description: str | None = None

class UnitProjectResponse(UnitProjectBase):
    id: int
    project_id: int
    created_at: datetime | None = None
    divisions: list[DivisionResponse] = []
    model_config = {"from_attributes": True}


# --- Project (工程) ---
class ProjectBase(BaseModel):
    name: str
    code: str
    description: str | None = None
    location: str | None = None
    client_name: str | None = None
    contact_person: str | None = None
    contact_phone: str | None = None

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    name: str | None = None
    code: str | None = None
    description: str | None = None
    location: str | None = None
    client_name: str | None = None
    contact_person: str | None = None
    contact_phone: str | None = None
    status: str | None = None

class ProjectResponse(ProjectBase):
    id: int
    status: str
    created_at: datetime | None = None
    updated_at: datetime | None = None
    model_config = {"from_attributes": True}

class ProjectDetailResponse(ProjectResponse):
    """包含完整层级树的项目详情"""
    unit_projects: list[UnitProjectResponse] = []
