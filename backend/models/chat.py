"""
ChatSession model for storing chat conversations
"""
import enum

from sqlalchemy import JSON, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from .base import BaseModel


class ChatStatus(enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"


class ChatSession(BaseModel):
    __tablename__ = "chat_sessions"

    plan_id = Column(String(36), ForeignKey("plans.id", ondelete="CASCADE"), nullable=False)
    messages = Column(JSON, nullable=False, default=list)
    status = Column(String(20), nullable=False, default=ChatStatus.ACTIVE.value)

    # Relationships
    plan = relationship("Plan", back_populates="chat_sessions")

    def __repr__(self) -> str:
        message_count = len(self.messages) if self.messages else 0
        return f"<ChatSession(plan_id='{self.plan_id}', status='{self.status}', messages_count={message_count})>"
