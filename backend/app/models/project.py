from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.database import Base


class Project(Base):
    """工程（顶层）"""
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    code = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(Text)
    location = Column(String(200))
    client_name = Column(String(100))
    contact_person = Column(String(50))
    contact_phone = Column(String(20))
    status = Column(String(20), default="active")  # active, completed, archived
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    unit_projects = relationship("UnitProject", back_populates="project", cascade="all, delete-orphan")


class UnitProject(Base):
    """单位工程"""
    __tablename__ = "unit_projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    code = Column(String(50), nullable=False, index=True)
    description = Column(Text)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    project = relationship("Project", back_populates="unit_projects")
    divisions = relationship("Division", back_populates="unit_project", cascade="all, delete-orphan")


class Division(Base):
    """分部工程"""
    __tablename__ = "divisions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    code = Column(String(50), nullable=False, index=True)
    description = Column(Text)
    unit_project_id = Column(Integer, ForeignKey("unit_projects.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    unit_project = relationship("UnitProject", back_populates="divisions")
    sub_items = relationship("SubItem", back_populates="division", cascade="all, delete-orphan")


class SubItem(Base):
    """分项工程"""
    __tablename__ = "sub_items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    code = Column(String(50), nullable=False, index=True)
    description = Column(Text)
    division_id = Column(Integer, ForeignKey("divisions.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    division = relationship("Division", back_populates="sub_items")
