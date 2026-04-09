from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.core.exceptions import NotFoundError
from app.core.permissions import require_permissions
from app.models.sample import Sample
from app.models.user import User
from app.schemas.sample import (
    SampleCreate,
    SampleReceive,
    SampleResponse,
    SampleStatusUpdate,
    SampleUpdate,
)
from app.services import sample_service

router = APIRouter(prefix="/api", tags=["样品管理"])


@router.post("/samples", response_model=SampleResponse)
def create_sample(
    data: SampleCreate,
    db: Session = Depends(get_db),
    _user: User = Depends(require_permissions("sample:create")),
):
    return sample_service.create_sample(db, data.model_dump())


@router.get("/samples", response_model=list[SampleResponse])
def list_samples(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: str = "",
    status: str = "",
    commission_id: int | None = None,
    material_type: str = "",
    db: Session = Depends(get_db),
    _user: User = Depends(require_permissions("sample:read")),
):
    query = db.query(Sample)
    if keyword:
        query = query.filter(
            Sample.sample_no.ilike(f"%{keyword}%")
            | Sample.name.ilike(f"%{keyword}%")
        )
    if status:
        query = query.filter(Sample.status == status)
    if commission_id:
        query = query.filter(Sample.commission_id == commission_id)
    if material_type:
        query = query.filter(Sample.material_type == material_type)
    query = query.order_by(Sample.created_at.desc())
    return query.offset((page - 1) * page_size).limit(page_size).all()


@router.get("/samples/{sample_id}", response_model=SampleResponse)
def get_sample(
    sample_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(require_permissions("sample:read")),
):
    sample = db.query(Sample).filter(Sample.id == sample_id).first()
    if not sample:
        raise NotFoundError("样品不存在")
    return sample


@router.put("/samples/{sample_id}", response_model=SampleResponse)
def update_sample(
    sample_id: int,
    data: SampleUpdate,
    db: Session = Depends(get_db),
    _user: User = Depends(require_permissions("sample:update")),
):
    sample = db.query(Sample).filter(Sample.id == sample_id).first()
    if not sample:
        raise NotFoundError("样品不存在")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(sample, field, value)
    db.commit()
    db.refresh(sample)
    return sample


@router.post("/samples/{sample_id}/receive", response_model=SampleResponse)
def receive_sample(
    sample_id: int,
    data: SampleReceive,
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions("sample:update")),
):
    return sample_service.receive_sample(db, sample_id, user.id, data.storage_location)


@router.post("/samples/{sample_id}/status", response_model=SampleResponse)
def update_sample_status(
    sample_id: int,
    data: SampleStatusUpdate,
    db: Session = Depends(get_db),
    _user: User = Depends(require_permissions("sample:update")),
):
    return sample_service.update_status(db, sample_id, data.status)
