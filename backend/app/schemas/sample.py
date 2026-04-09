from datetime import date, datetime

from pydantic import BaseModel


class SampleCreate(BaseModel):
    commission_id: int
    name: str
    material_type: str | None = None
    specification: str | None = None
    quantity: int = 1
    quantity_unit: str = "组"
    sampling_date: date | None = None
    sampling_location: str | None = None
    sampler: str | None = None
    notes: str | None = None


class SampleUpdate(BaseModel):
    name: str | None = None
    material_type: str | None = None
    specification: str | None = None
    quantity: int | None = None
    quantity_unit: str | None = None
    sampling_date: date | None = None
    sampling_location: str | None = None
    sampler: str | None = None
    storage_location: str | None = None
    retention_deadline: date | None = None
    notes: str | None = None


class SampleResponse(BaseModel):
    id: int
    sample_no: str
    commission_id: int
    name: str
    material_type: str | None = None
    specification: str | None = None
    quantity: int
    quantity_unit: str
    sampling_date: date | None = None
    sampling_location: str | None = None
    sampler: str | None = None
    status: str
    received_by: int | None = None
    received_at: datetime | None = None
    storage_location: str | None = None
    retention_deadline: date | None = None
    disposed_at: datetime | None = None
    notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    model_config = {"from_attributes": True}


class SampleReceive(BaseModel):
    storage_location: str


class SampleStatusUpdate(BaseModel):
    status: str
