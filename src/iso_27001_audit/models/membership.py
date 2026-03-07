import uuid

from sqlalchemy import Enum, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from iso_27001_audit.models.model import Model
from iso_27001_audit.enums.membership_role import MembershipRole


class Membership(Model):
    __tablename__ = "memberships"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "organization_id",
            name="uq_membership_user_org",
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("app_users.id", ondelete="CASCADE"),
        nullable=False,
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )

    role: Mapped[MembershipRole] = mapped_column(
        Enum(MembershipRole, name="membership_role_enum"),
        nullable=False,
    )

    user = relationship(
        "AppUser",
        back_populates="memberships",
    )

    organization = relationship(
        "Organization",
        back_populates="memberships",
    )