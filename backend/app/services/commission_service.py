from datetime import datetime

from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestError, NotFoundError
from app.models.commission import Commission
from app.models.project import Project, SubItem
from app.services.numbering_service import generate_number


def create_commission(db: Session, data: dict, user_id: int) -> Commission:
    if not db.query(Project).filter(Project.id == data["project_id"]).first():
        raise NotFoundError("工程不存在")
    if not db.query(SubItem).filter(SubItem.id == data["sub_item_id"]).first():
        raise NotFoundError("分项工程不存在")

    commission_no = generate_number(db, "commission")
    commission = Commission(
        commission_no=commission_no,
        submitted_by=user_id,
        **data,
    )
    db.add(commission)
    db.commit()
    db.refresh(commission)
    return commission


def submit_commission(db: Session, commission_id: int) -> Commission:
    commission = db.query(Commission).filter(Commission.id == commission_id).first()
    if not commission:
        raise NotFoundError("委托单不存在")
    if commission.status != "draft":
        raise BadRequestError("只有草稿状态的委托单可以提交")
    commission.status = "submitted"
    db.commit()
    db.refresh(commission)
    return commission


def review_commission(
    db: Session, commission_id: int, reviewer_id: int, approved: bool, comment: str
) -> Commission:
    commission = db.query(Commission).filter(Commission.id == commission_id).first()
    if not commission:
        raise NotFoundError("委托单不存在")
    if commission.status != "submitted":
        raise BadRequestError("只有已提交的委托单可以审核")
    commission.status = "approved" if approved else "rejected"
    commission.reviewed_by = reviewer_id
    commission.review_comment = comment
    commission.reviewed_at = datetime.now()
    db.commit()
    db.refresh(commission)
    return commission


def update_commission(db: Session, commission_id: int, data: dict) -> Commission:
    commission = db.query(Commission).filter(Commission.id == commission_id).first()
    if not commission:
        raise NotFoundError("委托单不存在")
    if commission.status not in ("draft", "rejected"):
        raise BadRequestError("只有草稿或已退回的委托单可以编辑")
    if commission.status == "rejected":
        commission.status = "draft"
        commission.reviewed_by = None
        commission.review_comment = None
        commission.reviewed_at = None
    for field, value in data.items():
        setattr(commission, field, value)
    db.commit()
    db.refresh(commission)
    return commission


def delete_commission(db: Session, commission_id: int) -> None:
    commission = db.query(Commission).filter(Commission.id == commission_id).first()
    if not commission:
        raise NotFoundError("委托单不存在")
    if commission.status != "draft":
        raise BadRequestError("只有草稿状态的委托单可以删除")
    db.delete(commission)
    db.commit()
