"""
models.py — SQLAlchemy models pour AUI Email Support System.
"""

from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Enum as SAEnum
from sqlalchemy.orm import DeclarativeBase
import enum


class Base(DeclarativeBase):
    pass


class RoleEnum(str, enum.Enum):
    admin  = "admin"
    user   = "user"
    viewer = "viewer"


class User(Base):
    __tablename__ = "users"

    id              = Column(String(20),  primary_key=True)
    email           = Column(String(254), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role            = Column(SAEnum(RoleEnum), nullable=False, default=RoleEnum.viewer)
    is_active       = Column(Boolean, nullable=False, default=True)
    created_at      = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_login      = Column(DateTime, nullable=True)

    def to_dict(self) -> dict:
        return {
            "id":         self.id,
            "email":      self.email,
            "role":       self.role.value,
            "is_active":  self.is_active,
            "created_at": self.created_at.isoformat() + "Z" if self.created_at else "",
            "last_login": self.last_login.isoformat() + "Z" if self.last_login else None,
        }
