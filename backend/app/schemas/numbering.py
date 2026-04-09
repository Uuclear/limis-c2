from datetime import date, datetime

from pydantic import BaseModel


class NumberingRuleResponse(BaseModel):
    id: int
    entity_type: str
    name: str
    prefix: str
    date_format: str
    separator: str
    sequence_digits: int
    sequence_reset: str
    current_sequence: int
    last_reset_date: date | None = None
    is_active: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None
    model_config = {"from_attributes": True}


class NumberingRuleUpdate(BaseModel):
    name: str | None = None
    prefix: str | None = None
    date_format: str | None = None
    separator: str | None = None
    sequence_digits: int | None = None
    sequence_reset: str | None = None
    is_active: bool | None = None
