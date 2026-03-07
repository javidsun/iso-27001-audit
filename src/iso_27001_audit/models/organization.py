from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from iso_27001_audit.models.model import Model


class Organization(Model):
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    slug: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
    )

    keycloak_group_path: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
    )

    memberships = relationship(
        "Membership",
        back_populates="organization",
        cascade="all, delete-orphan",
    )