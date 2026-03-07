from typing import FrozenSet, Optional


class Principal:
    __slots__ = ("_sub", "_username", "_roles", "_tenant_group")

    def __init__(
        self,
        sub: str,
        username: str,
        roles: FrozenSet[str],
        tenant_group: Optional[str],
    ) -> None:
        self._sub = sub
        self._username = username
        self._roles = roles
        self._tenant_group = tenant_group

    @property
    def sub(self) -> str:
        return self._sub

    @property
    def username(self) -> str:
        return self._username

    @property
    def roles(self) -> FrozenSet[str]:
        return self._roles

    @property
    def tenant_group(self) -> Optional[str]:
        return self._tenant_group

    @property
    def is_system(self) -> bool:
        return "system" in self._roles