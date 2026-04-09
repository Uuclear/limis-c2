from datetime import date, datetime

from sqlalchemy import Boolean, Column, Date, DateTime, Integer, String

from app.database import Base


class NumberingRule(Base):
    """编号规则配置"""
    __tablename__ = "numbering_rules"

    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String(30), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    prefix = Column(String(20), nullable=False)
    date_format = Column(String(20), default="YYYY")
    separator = Column(String(5), default="-")
    sequence_digits = Column(Integer, default=4)
    sequence_reset = Column(String(20), default="yearly")
    current_sequence = Column(Integer, default=0)
    last_reset_date = Column(Date, default=date.today)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
