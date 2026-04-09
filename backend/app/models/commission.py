from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class Commission(Base):
    """委托单"""
    __tablename__ = "commissions"

    id = Column(Integer, primary_key=True, index=True)
    commission_no = Column(String(50), unique=True, nullable=False, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    sub_item_id = Column(Integer, ForeignKey("sub_items.id"), nullable=False)
    client_name = Column(String(100), nullable=False)
    client_contact = Column(String(50))
    client_phone = Column(String(20))
    description = Column(Text)
    sample_count = Column(Integer, default=0)
    status = Column(String(20), default="draft")
    submitted_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    review_comment = Column(Text, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    project = relationship("Project")
    sub_item = relationship("SubItem")
    submitter = relationship("User", foreign_keys=[submitted_by])
    reviewer = relationship("User", foreign_keys=[reviewed_by])
