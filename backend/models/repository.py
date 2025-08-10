"""
Repository model for storing git repository information
"""
from sqlalchemy import Column, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from .base import BaseModel


class Repository(BaseModel):
    __tablename__ = "repositories"

    name = Column(String(255), nullable=False)
    path = Column(Text, nullable=False)
    git_url = Column(Text, nullable=True)
    default_branch = Column(String(100), nullable=False, default="main")

    # Relationships
    plans = relationship("Plan", back_populates="repository", cascade="all, delete-orphan")

    __table_args__ = (UniqueConstraint("path", name="uq_repositories_path"),)

    def __repr__(self) -> str:
        return f"<Repository(name='{self.name}', path='{self.path}')>"
