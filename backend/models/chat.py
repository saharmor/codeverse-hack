"""
ChatSession model for storing chat conversations
"""
from sqlalchemy import Column, ForeignKey, JSON, String
from sqlalchemy.orm import relationship
import enum
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
    
    def __repr__(self):
        return f"<ChatSession(plan_id='{self.plan_id}', status='{self.status.value}', messages_count={len(self.messages) if self.messages else 0})>"