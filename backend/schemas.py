"""
Pydantic schemas for API request/response models
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


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


# Plan Version schemas
class PlanVersionBase(BaseModel):
    content: Dict[str, Any]
    version: int = 1


class PlanVersionCreate(PlanVersionBase):
    plan_id: str


class PlanVersion(PlanVersionBase):
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
