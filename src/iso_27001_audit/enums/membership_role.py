from enum import Enum


class MembershipRole(str, Enum):
    SYSTEM = "system"
    ORG_ADMIN = "org_admin"
    EDITOR = "editor"
    VIEWER = "viewer"