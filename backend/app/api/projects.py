from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload

from app.core.dependencies import get_db
from app.core.exceptions import BadRequestError, NotFoundError
from app.core.permissions import require_roles
from app.models.project import Division, Project, SubItem, UnitProject
from app.models.user import User
from app.schemas.project import (
    DivisionCreate,
    DivisionResponse,
    DivisionUpdate,
    ProjectCreate,
    ProjectDetailResponse,
    ProjectResponse,
    ProjectUpdate,
    SubItemCreate,
    SubItemResponse,
    SubItemUpdate,
    UnitProjectCreate,
    UnitProjectResponse,
    UnitProjectUpdate,
)

router = APIRouter(prefix="/api", tags=["项目管理"])


# ========== Project (工程) ==========

@router.get("/projects", response_model=list[ProjectResponse])
def list_projects(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: str = "",
    status: str = "",
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles("admin", "lab_director", "project_manager")),
):
    query = db.query(Project)
    if keyword:
        query = query.filter(
            Project.name.ilike(f"%{keyword}%") | Project.code.ilike(f"%{keyword}%")
        )
    if status:
        query = query.filter(Project.status == status)
    query = query.order_by(Project.created_at.desc())
    return query.offset((page - 1) * page_size).limit(page_size).all()


@router.post("/projects", response_model=ProjectResponse)
def create_project(
    data: ProjectCreate,
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles("admin", "project_manager")),
):
    if db.query(Project).filter(Project.code == data.code).first():
        raise BadRequestError("工程编号已存在")
    project = Project(**data.model_dump())
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("/projects/{project_id}", response_model=ProjectDetailResponse)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles("admin", "lab_director", "project_manager")),
):
    project = (
        db.query(Project)
        .options(
            joinedload(Project.unit_projects)
            .joinedload(UnitProject.divisions)
            .joinedload(Division.sub_items)
        )
        .filter(Project.id == project_id)
        .first()
    )
    if not project:
        raise NotFoundError("工程不存在")
    return project


@router.put("/projects/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int,
    data: ProjectUpdate,
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles("admin", "project_manager")),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise NotFoundError("工程不存在")
    update_data = data.model_dump(exclude_unset=True)
    if "code" in update_data:
        existing = db.query(Project).filter(Project.code == update_data["code"], Project.id != project_id).first()
        if existing:
            raise BadRequestError("工程编号已存在")
    for field, value in update_data.items():
        setattr(project, field, value)
    db.commit()
    db.refresh(project)
    return project


@router.delete("/projects/{project_id}")
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles("admin")),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise NotFoundError("工程不存在")
    db.delete(project)
    db.commit()
    return {"message": "工程已删除"}


# ========== UnitProject (单位工程) ==========

@router.post("/unit-projects", response_model=UnitProjectResponse)
def create_unit_project(
    data: UnitProjectCreate,
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles("admin", "project_manager")),
):
    if not db.query(Project).filter(Project.id == data.project_id).first():
        raise NotFoundError("工程不存在")
    unit = UnitProject(**data.model_dump())
    db.add(unit)
    db.commit()
    db.refresh(unit)
    return unit


@router.put("/unit-projects/{unit_id}", response_model=UnitProjectResponse)
def update_unit_project(
    unit_id: int,
    data: UnitProjectUpdate,
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles("admin", "project_manager")),
):
    unit = db.query(UnitProject).filter(UnitProject.id == unit_id).first()
    if not unit:
        raise NotFoundError("单位工程不存在")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(unit, field, value)
    db.commit()
    db.refresh(unit)
    return unit


@router.delete("/unit-projects/{unit_id}")
def delete_unit_project(
    unit_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles("admin", "project_manager")),
):
    unit = db.query(UnitProject).filter(UnitProject.id == unit_id).first()
    if not unit:
        raise NotFoundError("单位工程不存在")
    db.delete(unit)
    db.commit()
    return {"message": "单位工程已删除"}


# ========== Division (分部工程) ==========

@router.post("/divisions", response_model=DivisionResponse)
def create_division(
    data: DivisionCreate,
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles("admin", "project_manager", "lab_director")),
):
    if not db.query(UnitProject).filter(UnitProject.id == data.unit_project_id).first():
        raise NotFoundError("单位工程不存在")
    division = Division(**data.model_dump())
    db.add(division)
    db.commit()
    db.refresh(division)
    return division


@router.put("/divisions/{division_id}", response_model=DivisionResponse)
def update_division(
    division_id: int,
    data: DivisionUpdate,
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles("admin", "project_manager", "lab_director")),
):
    division = db.query(Division).filter(Division.id == division_id).first()
    if not division:
        raise NotFoundError("分部工程不存在")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(division, field, value)
    db.commit()
    db.refresh(division)
    return division


@router.delete("/divisions/{division_id}")
def delete_division(
    division_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles("admin", "project_manager")),
):
    division = db.query(Division).filter(Division.id == division_id).first()
    if not division:
        raise NotFoundError("分部工程不存在")
    db.delete(division)
    db.commit()
    return {"message": "分部工程已删除"}


# ========== SubItem (分项工程) ==========

@router.post("/sub-items", response_model=SubItemResponse)
def create_sub_item(
    data: SubItemCreate,
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles("admin", "project_manager", "lab_director")),
):
    if not db.query(Division).filter(Division.id == data.division_id).first():
        raise NotFoundError("分部工程不存在")
    sub_item = SubItem(**data.model_dump())
    db.add(sub_item)
    db.commit()
    db.refresh(sub_item)
    return sub_item


@router.put("/sub-items/{item_id}", response_model=SubItemResponse)
def update_sub_item(
    item_id: int,
    data: SubItemUpdate,
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles("admin", "project_manager", "lab_director")),
):
    sub_item = db.query(SubItem).filter(SubItem.id == item_id).first()
    if not sub_item:
        raise NotFoundError("分项工程不存在")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(sub_item, field, value)
    db.commit()
    db.refresh(sub_item)
    return sub_item


@router.delete("/sub-items/{item_id}")
def delete_sub_item(
    item_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles("admin", "project_manager")),
):
    sub_item = db.query(SubItem).filter(SubItem.id == item_id).first()
    if not sub_item:
        raise NotFoundError("分项工程不存在")
    db.delete(sub_item)
    db.commit()
    return {"message": "分项工程已删除"}
