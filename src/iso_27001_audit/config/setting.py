import os
from typing import Dict


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def get_settings() -> Dict[str, object]:
    issuer = os.getenv("KEYCLOAK_ISSUER", "").strip().rstrip("/")
    jwks_url = os.getenv("KEYCLOAK_JWKS_URL", "").strip()

    if not issuer or not jwks_url:
        raise RuntimeError("Missing KEYCLOAK_ISSUER or KEYCLOAK_JWKS_URL")

    verify_aud = _env_bool("JWT_VERIFY_AUD", False)
    expected_audience = os.getenv("JWT_EXPECTED_AUDIENCE", "iso-audit-api").strip()
    keycloak_client_id = os.getenv("KEYCLOAK_CLIENT_ID", "iso-audit-api").strip()

    tenant_groups_claim = os.getenv("TENANT_GROUPS_CLAIM", "groups").strip() or "groups"
    tenant_group_prefix = os.getenv("TENANT_GROUP_PREFIX", "/org-").strip() or "/org-"

    return {
        "issuer": issuer,
        "jwks_url": jwks_url,
        "verify_aud": verify_aud,
        "expected_audience": expected_audience,
        "keycloak_client_id": keycloak_client_id,
        "tenant_groups_claim": tenant_groups_claim,
        "tenant_group_prefix": tenant_group_prefix,
    }