"""
Plan and PlanArtifact models for storing planning information
"""
import enum

from sqlalchemy import JSON, Column, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from .base import BaseModel


class PlanStatus(enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class Plan(BaseModel):
    __tablename__ = "plans"

    repository_id = Column(String(36), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    target_branch = Column(String(100), nullable=False)
    status = Column(String(20), nullable=False, default=PlanStatus.DRAFT.value)

    # Relationships
    repository = relationship("Repository", back_populates="plans")
    plan_versions = relationship("PlanVersion", back_populates="plan", cascade="all, delete-orphan")
    chat_sessions = relationship("ChatSession", back_populates="plan", cascade="all, delete-orphan")

    __table_args__ = (UniqueConstraint("repository_id", "name", name="uq_plans_repo_name"),)

    def __repr__(self) -> str:
        return f"<Plan(name='{self.name}', status='{self.status}')>"


class PlanVersion(BaseModel):
    __tablename__ = "plan_artifacts"

    plan_id = Column(String(36), ForeignKey("plans.id", ondelete="CASCADE"), nullable=False)
    content = Column(JSON, nullable=False)
    version = Column(Integer, nullable=False, default=1)

    # Relationships
    plan = relationship("Plan", back_populates="plan_versions")

    def __repr__(self) -> str:
        return f"<PlanVersion(plan_id='{self.plan_id}', version={self.version})>"
