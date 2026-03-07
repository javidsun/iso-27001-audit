import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from iso_27001_audit.models.model import Model


class AppUser(Model):
    __tablename__ = "app_users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    external_subject: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        unique=True,
    )

    username: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
    )

    email: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        unique=True,
    )

    first_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    memberships = relationship(
        "Membership",
        back_populates="user",
        cascade="all, delete-orphan",
    )