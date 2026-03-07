from typing import Any, Dict, FrozenSet, Optional, Set, Callable, List

from fastapi import Depends, HTTPException, Request
from starlette import status

from iso_27001_audit.security.jwt_validator import JWTValidator
from iso_27001_audit.security.principal import Principal


class AccessControl:
    """
    Access control برای:
    - JWT auth
    - role-based authz
    - tenant resolution از روی groups claim

    قانون:
    - system می‌تواند tenant نداشته باشد
    - non-system باید حداقل یک group با prefix مشخص داشته باشد
    """

    def __init__(
        self,
        jwt_validator: JWTValidator,
        keycloak_client_id: str,
        tenant_groups_claim: str,
        tenant_group_prefix: str,
    ) -> None:
        self._jwt_validator = jwt_validator
        self._client_id = keycloak_client_id
        self._tenant_groups_claim = tenant_groups_claim
        self._tenant_group_prefix = tenant_group_prefix

    def _extract_roles(self, payload: Dict[str, Any]) -> Set[str]:
        resource_access = payload.get("resource_access")
        if not isinstance(resource_access, dict):
            return set()

        client_access = resource_access.get(self._client_id)
        if not isinstance(client_access, dict):
            return set()

        roles = client_access.get("roles")
        if not isinstance(roles, list):
            return set()

        out: Set[str] = set()
        for role in roles:
            if isinstance(role, str) and role.strip():
                out.add(role.strip())

        return out

    def _extract_groups(self, payload: Dict[str, Any]) -> List[str]:
        raw = payload.get(self._tenant_groups_claim)
        if not isinstance(raw, list):
            return []

        out: List[str] = []
        for item in raw:
            if isinstance(item, str) and item.strip():
                out.append(item.strip())

        return out

    def _resolve_tenant_group(self, payload: Dict[str, Any]) -> Optional[str]:
        groups = self._extract_groups(payload)

        for group_path in groups:
            if group_path.startswith(self._tenant_group_prefix):
                return group_path

        return None

    def _resolve_subject(self, payload: Dict[str, Any]) -> str:
        """
        ترجیح:
        1) sub
        2) preferred_username
        3) email
        4) jti

        در بعضی setupها ممکنه access token فاقد sub باشد.
        برای همین اینجا بی‌خودی 401 نمی‌دهیم.
        """
        candidates = [
            payload.get("sub"),
            payload.get("preferred_username"),
            payload.get("email"),
            payload.get("jti"),
        ]

        for candidate in candidates:
            if isinstance(candidate, str) and candidate.strip():
                return candidate.strip()

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing subject identifier in token",
        )

    def _resolve_username(self, payload: Dict[str, Any]) -> str:
        candidates = [
            payload.get("preferred_username"),
            payload.get("email"),
            payload.get("sub"),
            payload.get("jti"),
        ]

        for candidate in candidates:
            if isinstance(candidate, str) and candidate.strip():
                return candidate.strip()

        return ""

    async def authenticate(self, request: Request) -> Principal:
        payload = await self._jwt_validator.verify(request)

        subject = self._resolve_subject(payload)
        username = self._resolve_username(payload)
        roles = frozenset(self._extract_roles(payload))
        tenant_group = self._resolve_tenant_group(payload)

        principal = Principal(
            sub=subject,
            username=username,
            roles=roles,
            tenant_group=tenant_group,
        )

        if (not principal.is_system) and (not principal.tenant_group):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Missing tenant group for non-system user",
            )

        request.state.principal = principal
        return principal
