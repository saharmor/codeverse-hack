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


class ArtifactType(enum.Enum):
    FEATURE_PLAN = "feature_plan"
    IMPLEMENTATION_STEPS = "implementation_steps"
    CODE_CHANGES = "code_changes"


class Plan(BaseModel):
    __tablename__ = "plans"

    repository_id = Column(String(36), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    target_branch = Column(String(100), nullable=False)
    version = Column(Integer, nullable=False, default=1)
    status = Column(String(20), nullable=False, default=PlanStatus.DRAFT.value)

    # Relationships
    repository = relationship("Repository", back_populates="plans")
    artifacts = relationship("PlanArtifact", back_populates="plan", cascade="all, delete-orphan")
    chat_sessions = relationship("ChatSession", back_populates="plan", cascade="all, delete-orphan")

    __table_args__ = (UniqueConstraint("repository_id", "name", "version", name="uq_plans_repo_name_version"),)

    def __repr__(self) -> str:
        return f"<Plan(name='{self.name}', version={self.version}, status='{self.status}')>"


class PlanArtifact(BaseModel):
    __tablename__ = "plan_artifacts"

    plan_id = Column(String(36), ForeignKey("plans.id", ondelete="CASCADE"), nullable=False)
    content = Column(JSON, nullable=False)
    artifact_type = Column(String(30), nullable=False)

    # Relationships
    plan = relationship("Plan", back_populates="artifacts")

    def __repr__(self) -> str:
        return f"<PlanArtifact(type='{self.artifact_type}', plan_id='{self.plan_id}')>"
