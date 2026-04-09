from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.core.permissions import require_permissions
from app.models.commission import Commission
from app.models.numbering import NumberingRule
from app.models.user import User
from app.schemas.commission import (
    CommissionCreate,
    CommissionResponse,
    CommissionReview,
    CommissionUpdate,
)
from app.schemas.numbering import NumberingRuleResponse, NumberingRuleUpdate
from app.services import commission_service

router = APIRouter(prefix="/api", tags=["委托管理"])


@router.post("/commissions", response_model=CommissionResponse)
def create_commission(
    data: CommissionCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions("commission:create")),
):
    return commission_service.create_commission(db, data.model_dump(), user.id)


@router.get("/commissions", response_model=list[CommissionResponse])
def list_commissions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: str = "",
    status: str = "",
    project_id: int | None = None,
    db: Session = Depends(get_db),
    _user: User = Depends(require_permissions("commission:read")),
):
    query = db.query(Commission)
    if keyword:
        query = query.filter(
            Commission.commission_no.ilike(f"%{keyword}%")
            | Commission.client_name.ilike(f"%{keyword}%")
            | Commission.description.ilike(f"%{keyword}%")
        )
    if status:
        query = query.filter(Commission.status == status)
    if project_id:
        query = query.filter(Commission.project_id == project_id)
    query = query.order_by(Commission.created_at.desc())
    return query.offset((page - 1) * page_size).limit(page_size).all()


@router.get("/commissions/{commission_id}", response_model=CommissionResponse)
def get_commission(
    commission_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(require_permissions("commission:read")),
):
    commission = db.query(Commission).filter(Commission.id == commission_id).first()
    if not commission:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("委托单不存在")
    return commission


@router.put("/commissions/{commission_id}", response_model=CommissionResponse)
def update_commission(
    commission_id: int,
    data: CommissionUpdate,
    db: Session = Depends(get_db),
    _user: User = Depends(require_permissions("commission:update")),
):
    return commission_service.update_commission(
        db, commission_id, data.model_dump(exclude_unset=True)
    )


@router.post("/commissions/{commission_id}/submit", response_model=CommissionResponse)
def submit_commission(
    commission_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(require_permissions("commission:create")),
):
    return commission_service.submit_commission(db, commission_id)


@router.post("/commissions/{commission_id}/review", response_model=CommissionResponse)
def review_commission(
    commission_id: int,
    data: CommissionReview,
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions("commission:approve")),
):
    return commission_service.review_commission(
        db, commission_id, user.id, data.approved, data.comment
    )


@router.delete("/commissions/{commission_id}")
def delete_commission(
    commission_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(require_permissions("commission:update")),
):
    commission_service.delete_commission(db, commission_id)
    return {"message": "委托单已删除"}


# ========== NumberingRule endpoints ==========

@router.get("/numbering-rules", response_model=list[NumberingRuleResponse])
def list_numbering_rules(
    db: Session = Depends(get_db),
    _user: User = Depends(require_permissions("system:manage")),
):
    return db.query(NumberingRule).all()


@router.put("/numbering-rules/{rule_id}", response_model=NumberingRuleResponse)
def update_numbering_rule(
    rule_id: int,
    data: NumberingRuleUpdate,
    db: Session = Depends(get_db),
    _user: User = Depends(require_permissions("system:manage")),
):
    from app.core.exceptions import NotFoundError
    rule = db.query(NumberingRule).filter(NumberingRule.id == rule_id).first()
    if not rule:
        raise NotFoundError("编号规则不存在")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(rule, field, value)
    db.commit()
    db.refresh(rule)
    return rule
