import os
from typing import Dict


class SettingsProvider:
    def __init__(self) -> None:
        pass

    def _read_bool(self, name: str, default: bool) -> bool:
        value = os.getenv(name)
        if value is None:
            return default

        normalized = value.strip().lower()
        return normalized in {"1", "true", "yes", "y", "on"}

    def _read_required_string(self, name: str) -> str:
        value = os.getenv(name, "").strip()
        if not value:
            raise RuntimeError(f"Missing required environment variable: {name}")
        return value

    def _read_optional_string(self, name: str, default: str) -> str:
        value = os.getenv(name, default).strip()
        if not value:
            return default
        return value

    def _build_database_url(
        self,
        host: str,
        port: str,
        database: str,
        username: str,
        password: str,
    ) -> str:
        if password.strip():
            return f"postgresql+psycopg://{username}:{password}@{host}:{port}/{database}"

        return f"postgresql+psycopg://{username}@{host}:{port}/{database}"

    def get_settings(self) -> Dict[str, object]:
        issuer = self._read_required_string("KEYCLOAK_ISSUER").rstrip("/")
        jwks_url = self._read_required_string("KEYCLOAK_JWKS_URL")

        verify_aud = self._read_bool("JWT_VERIFY_AUD", False)
        expected_audience = self._read_optional_string("JWT_EXPECTED_AUDIENCE", "iso-audit-api")
        keycloak_client_id = self._read_optional_string("KEYCLOAK_CLIENT_ID", "iso-audit-api")

        tenant_groups_claim = self._read_optional_string("TENANT_GROUPS_CLAIM", "groups")
        tenant_group_prefix = self._read_optional_string("TENANT_GROUP_PREFIX", "/org-")

        db_host = self._read_optional_string("DB_HOST", "127.0.0.1")
        db_port = self._read_optional_string("DB_PORT", "5432")
        db_name = self._read_optional_string("DB_NAME", "iso_audit")
        db_user = self._read_optional_string("DB_USER", "iso_user")
        db_password = self._read_optional_string("DB_PASSWORD", "")

        database_url = self._build_database_url(
            host=db_host,
            port=db_port,
            database=db_name,
            username=db_user,
            password=db_password,
        )

        return {
            "issuer": issuer,
            "jwks_url": jwks_url,
            "verify_aud": verify_aud,
            "expected_audience": expected_audience,
            "keycloak_client_id": keycloak_client_id,
            "tenant_groups_claim": tenant_groups_claim,
            "tenant_group_prefix": tenant_group_prefix,
            "db_host": db_host,
            "db_port": db_port,
            "db_name": db_name,
            "db_user": db_user,
            "db_password": db_password,
            "database_url": database_url,
        }