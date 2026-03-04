import os
from typing import Dict


def _env_bool(name: str, default: bool) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return v.strip().lower() in {"1", "true", "yes", "y", "on"}


def get_settings() -> Dict[str, object]:
    issuer = os.getenv("KEYCLOAK_ISSUER", "").strip().rstrip("/")
    jwks_url = os.getenv("KEYCLOAK_JWKS_URL", "").strip()

    if not issuer or not jwks_url:
        raise RuntimeError("Missing KEYCLOAK_ISSUER or KEYCLOAK_JWKS_URL")

    verify_aud = _env_bool("JWT_VERIFY_AUD", False)
    expected_audience = os.getenv("JWT_EXPECTED_AUDIENCE", "iso-audit-api").strip()

    return {
        "issuer": issuer,
        "jwks_url": jwks_url,
            "verify_aud": verify_aud,
        "expected_audience": expected_audience,
    }