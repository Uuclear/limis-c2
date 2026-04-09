from datetime import datetime

from pydantic import BaseModel


class CommissionCreate(BaseModel):
    project_id: int
    sub_item_id: int
    client_name: str
    client_contact: str | None = None
    client_phone: str | None = None
    description: str | None = None
    sample_count: int = 0


class CommissionUpdate(BaseModel):
    client_name: str | None = None
    client_contact: str | None = None
    client_phone: str | None = None
    description: str | None = None
    sample_count: int | None = None
    sub_item_id: int | None = None


class CommissionResponse(BaseModel):
    id: int
    commission_no: str
    project_id: int
    sub_item_id: int
    client_name: str
    client_contact: str | None = None
    client_phone: str | None = None
    description: str | None = None
    sample_count: int
    status: str
    submitted_by: int
    reviewed_by: int | None = None
    review_comment: str | None = None
    reviewed_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    model_config = {"from_attributes": True}


class CommissionReview(BaseModel):
    approved: bool
    comment: str = ""
