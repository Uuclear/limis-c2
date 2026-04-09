from datetime import datetime

from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestError, NotFoundError
from app.models.commission import Commission
from app.models.sample import Sample
from app.services.numbering_service import generate_number

VALID_TRANSITIONS = {
    "pending": "received",
    "received": "testing",
    "testing": "tested",
    "tested": "retained",
    "retained": "disposed",
}


def create_sample(db: Session, data: dict) -> Sample:
    commission = (
        db.query(Commission)
        .filter(Commission.id == data["commission_id"])
        .first()
    )
    if not commission:
        raise NotFoundError("委托单不存在")
    if commission.status != "approved":
        raise BadRequestError("只能为已审核通过的委托单登记样品")

    sample_no = generate_number(db, "sample")
    sample = Sample(sample_no=sample_no, **data)
    db.add(sample)
    db.commit()
    db.refresh(sample)
    return sample


def receive_sample(
    db: Session, sample_id: int, user_id: int, storage_location: str
) -> Sample:
    sample = db.query(Sample).filter(Sample.id == sample_id).first()
    if not sample:
        raise NotFoundError("样品不存在")
    if sample.status != "pending":
        raise BadRequestError("只有待接收的样品可以接收")
    sample.status = "received"
    sample.received_by = user_id
    sample.received_at = datetime.now()
    sample.storage_location = storage_location
    db.commit()
    db.refresh(sample)
    return sample


def update_status(db: Session, sample_id: int, new_status: str) -> Sample:
    sample = db.query(Sample).filter(Sample.id == sample_id).first()
    if not sample:
        raise NotFoundError("样品不存在")
    expected_next = VALID_TRANSITIONS.get(sample.status)
    if expected_next != new_status:
        raise BadRequestError(
            f"非法状态转换: {sample.status} → {new_status}，"
            f"只允许: {sample.status} → {expected_next}"
        )
    sample.status = new_status
    if new_status == "disposed":
        sample.disposed_at = datetime.now()
    db.commit()
    db.refresh(sample)
    return sample
