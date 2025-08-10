"""
Pydantic schemas for API request/response models
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# Repository schemas
class RepositoryBase(BaseModel):
    name: str
    path: str
    git_url: Optional[str] = None
    default_branch: str = "main"


class RepositoryCreate(RepositoryBase):
    pass


class RepositoryUpdate(BaseModel):
    name: Optional[str] = None
    path: Optional[str] = None
    git_url: Optional[str] = None
    default_branch: Optional[str] = None


class Repository(RepositoryBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Plan schemas
class PlanStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class PlanBase(BaseModel):
    name: str
    description: Optional[str] = None
    target_branch: str
    version: int = 1
    status: PlanStatus = PlanStatus.DRAFT


class PlanCreate(PlanBase):
    repository_id: str


class PlanUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    target_branch: Optional[str] = None
    status: Optional[PlanStatus] = None


class Plan(PlanBase):
    id: str
    repository_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Plan Artifact schemas
class ArtifactType(str, Enum):
    FEATURE_PLAN = "feature_plan"
    IMPLEMENTATION_STEPS = "implementation_steps"
    CODE_CHANGES = "code_changes"


class PlanArtifactBase(BaseModel):
    content: Dict[str, Any]
    artifact_type: ArtifactType


class PlanArtifactCreate(PlanArtifactBase):
    plan_id: str


class PlanArtifact(PlanArtifactBase):
    id: str
    plan_id: str
    created_at: datetime

    class Config:
        from_attributes = True


# Chat Session schemas
class ChatStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: Optional[datetime] = None


class ChatSessionBase(BaseModel):
    messages: List[ChatMessage] = []
    status: ChatStatus = ChatStatus.ACTIVE


class ChatSessionCreate(ChatSessionBase):
    plan_id: str


class ChatSessionUpdate(BaseModel):
    messages: Optional[List[ChatMessage]] = None
    status: Optional[ChatStatus] = None


class ChatSession(ChatSessionBase):
    id: str
    plan_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Transcription schemas
class TranscribeRequest(BaseModel):
    plan_id: str
    audio_wav_base64: str = Field(..., description="Base64-encoded WAV audio, <= 60 s, <= 10 MB")


class TranscribeResponse(BaseModel):
    raw_text: str
    corrected_text: str | None = None
    confidence: float | None = None
    vocab_hit_rate: float = 0.0
