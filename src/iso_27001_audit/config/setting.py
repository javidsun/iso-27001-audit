import os


def env_bool(name: str, default: bool) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return v.strip().lower() in {"1", "true", "yes", "y", "on"}


def get_settings() -> dict:
    issuer = os.getenv("KEYCLOAK_ISSUER", "").strip().rstrip("/")
    jwks_url = os.getenv("KEYCLOAK_JWKS_URL", "").strip()

    if not issuer or not jwks_url:
        raise RuntimeError("Missing KEYCLOAK_ISSUER or KEYCLOAK_JWKS_URL env vars")

    return {
        "issuer": issuer,
        "jwks_url": jwks_url,
        "verify_aud": env_bool("JWT_VERIFY_AUD", False),
        "expected_audience": os.getenv("JWT_EXPECTED_AUDIENCE", "iso-audit-api").strip(),
    }