from datetime import datetime

from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class Sample(Base):
    """样品"""
    __tablename__ = "samples"

    id = Column(Integer, primary_key=True, index=True)
    sample_no = Column(String(50), unique=True, nullable=False, index=True)
    commission_id = Column(Integer, ForeignKey("commissions.id"), nullable=False)
    name = Column(String(200), nullable=False)
    material_type = Column(String(50))
    specification = Column(String(100))
    quantity = Column(Integer, default=1)
    quantity_unit = Column(String(20), default="组")
    sampling_date = Column(Date)
    sampling_location = Column(String(200))
    sampler = Column(String(50))
    status = Column(String(20), default="pending")
    received_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    received_at = Column(DateTime, nullable=True)
    storage_location = Column(String(100), nullable=True)
    retention_deadline = Column(Date, nullable=True)
    disposed_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    commission = relationship("Commission", back_populates="samples")
    receiver = relationship("User", foreign_keys=[received_by])
