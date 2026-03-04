import os
import time
from typing import Dict

import httpx


def _env(name: str, default: str) -> str:
    v = os.getenv(name, default).strip()
    if not v:
        raise RuntimeError(f"Missing env var: {name}")
    return v


def _wait_http_ok(url: str, timeout_seconds: int = 60) -> None:
    deadline = time.time() + timeout_seconds
    last_err: str = ""
    while time.time() < deadline:
        try:
            r = httpx.get(url, timeout=3.0)
            if 200 <= r.status_code < 500:
                return
            last_err = f"status={r.status_code}"
        except Exception as e:
            last_err = str(e)
        time.sleep(1)
    raise RuntimeError(f"Service not ready: {url} (last_err={last_err})")


def _get_access_token(
    keycloak_base: str,
    realm: str,
    client_id: str,
    username: str,
    password: str,
) -> str:
    token_url = f"{keycloak_base}/realms/{realm}/protocol/openid-connect/token"

    data: Dict[str, str] = {
        "client_id": client_id,
        "grant_type": "password",
        "username": username,
        "password": password,
        "scope": "openid profile email",
    }

    r = httpx.post(
        token_url,
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=10.0,
    )
    r.raise_for_status()

    body: Dict[str, object] = r.json()
    token_obj = body.get("access_token")
    if not isinstance(token_obj, str) or len(token_obj) < 200:
        raise RuntimeError("access_token missing/invalid in Keycloak response")

    return token_obj


def test_task_9_4_secure_ping_returns_200_with_valid_token() -> None:
    # For running inside Docker network:
    # KEYCLOAK_BASE=http://keycloak:8080
    # BACKEND_BASE=http://iso-audit-backend:8003
    keycloak_base = _env("KEYCLOAK_BASE", "http://keycloak:8080")
    backend_base = _env("BACKEND_BASE", "http://iso-audit-backend:8003")

    realm = _env("KEYCLOAK_REALM", "iso-audit")
    client_id = _env("KEYCLOAK_CLIENT_ID", "iso-audit-api")
    username = _env("KEYCLOAK_USERNAME", "javid")
    password = _env("KEYCLOAK_PASSWORD", "Admin@@00000")

    # Wait for backend to be reachable
    _wait_http_ok(f"{backend_base}/api/v1/health", timeout_seconds=60)

    token = _get_access_token(
        keycloak_base=keycloak_base,
        realm=realm,
        client_id=client_id,
        username=username,
        password=password,
    )

    r = httpx.get(
        f"{backend_base}/api/v1/secure/ping",
        headers={"Authorization": f"Bearer {token}"},
        timeout=10.0,
    )

    assert r.status_code == 200, r.text

    body: Dict[str, object] = r.json()
    ok = body.get("ok")
    assert ok is True, body