"""
Base model class with common fields and utilities
"""
import uuid

from sqlalchemy import Column, DateTime, String, func
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class BaseModel(Base):  # type: ignore
    """Base model class with common fields"""

    __abstract__ = True

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
