from __future__ import annotations

import base64
import json
import os
import time
import uuid
from typing import Any, Dict, Optional, Tuple

import httpx
import pytest


# ==========================================================
# Helpers / Config
# ==========================================================


def _env(name: str, default: Optional[str] = None) -> str:
    v = os.getenv(name, default)
    if v is None or not v.strip():
        raise RuntimeError(f"Missing env var: {name}")
    return v.strip()


BACKEND_BASE = _env("BACKEND_BASE")
KEYCLOAK_BASE = _env("KEYCLOAK_BASE")
REALM = _env("KEYCLOAK_REALM")
CLIENT_ID = _env("KEYCLOAK_CLIENT_ID")

KC_ADMIN_USER = _env("KEYCLOAK_ADMIN_USER", "admin_audit")
KC_ADMIN_PASS = _env("KEYCLOAK_ADMIN_PASS", "admin123")

TENANT_CLAIM = os.getenv("TENANT_CLAIM_NAME", "org_id").strip() or "org_id"


def _unique(prefix: str) -> str:
    # Avoid collisions
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def _http_client() -> httpx.Client:
    return httpx.Client(timeout=20.0)


def _jwt_payload_unverified(token: str) -> Dict[str, Any]:
    # Decode JWT payload without signature verification (tests/debug only)
    parts = token.split(".")
    if len(parts) != 3:
        return {}
    payload_b64 = parts[1]
    padding = "=" * (-len(payload_b64) % 4)
    raw = base64.urlsafe_b64decode((payload_b64 + padding).encode("utf-8"))
    data = json.loads(raw.decode("utf-8"))
    return data if isinstance(data, dict) else {}


# ==========================================================
# Keycloak - Token
# ==========================================================


def _token_password_grant(username: str, password: str) -> str:
    url = f"{KEYCLOAK_BASE}/realms/{REALM}/protocol/openid-connect/token"
    data = {
        "grant_type": "password",
        "client_id": CLIENT_ID,
        "username": username,
        "password": password,
        # CRITICAL: request OIDC scope explicitly
        "scope": "openid profile email",
    }
    with _http_client() as c:
        r = c.post(url, data=data)
        if r.status_code >= 400:
            raise RuntimeError(
                f"Password grant failed: {r.status_code} body={r.text} username={username}"
            )
        tok = r.json().get("access_token")
        if not isinstance(tok, str) or not tok:
            raise RuntimeError(f"Keycloak did not return access_token. body={r.text}")
        return tok

def _kc_admin_token() -> str:
    # Admin REST API token from master realm (admin-cli)
    url = f"{KEYCLOAK_BASE}/realms/master/protocol/openid-connect/token"
    data = {
        "grant_type": "password",
        "client_id": "admin-cli",
        "username": KC_ADMIN_USER,
        "password": KC_ADMIN_PASS,
    }
    with _http_client() as c:
        r = c.post(url, data=data)
        r.raise_for_status()
        tok = r.json().get("access_token")
        if not isinstance(tok, str) or not tok:
            raise RuntimeError(f"Cannot obtain Keycloak admin token. body={r.text}")
        return tok


# ==========================================================
# Keycloak - Admin API Helpers
# ==========================================================


def _kc_get_client_uuid(admin_token: str) -> str:
    url = f"{KEYCLOAK_BASE}/admin/realms/{REALM}/clients"
    headers = {"Authorization": f"Bearer {admin_token}"}
    with _http_client() as c:
        r = c.get(url, headers=headers, params={"clientId": CLIENT_ID})
        r.raise_for_status()
        arr = r.json()
        if not isinstance(arr, list) or not arr:
            raise RuntimeError(f"Client not found in realm '{REALM}': {CLIENT_ID}")
        cid = arr[0].get("id")
        if not isinstance(cid, str) or not cid:
            raise RuntimeError("Client UUID missing")
        return cid


def _kc_ensure_client_role(admin_token: str, client_uuid: str, role_name: str) -> None:
    # Create client role if missing (idempotent)
    headers = {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
    get_url = f"{KEYCLOAK_BASE}/admin/realms/{REALM}/clients/{client_uuid}/roles/{role_name}"

    with _http_client() as c:
        r = c.get(get_url, headers=headers)
        if r.status_code == 200:
            return
        if r.status_code != 404:
            raise RuntimeError(f"Unexpected role GET status: {r.status_code} {r.text}")

        create_url = f"{KEYCLOAK_BASE}/admin/realms/{REALM}/clients/{client_uuid}/roles"
        payload = {"name": role_name, "description": f"Auto-created role {role_name}"}
        rc = c.post(create_url, headers=headers, json=payload)
        if rc.status_code not in (201, 409):
            raise RuntimeError(f"Failed to create role '{role_name}': {rc.status_code} {rc.text}")


def _kc_ensure_user_attr_mapper(admin_token: str, client_uuid: str) -> None:
    """
    HARD reset protocol mapper (delete + create):
    maps user attribute (org_id) -> token claim (org_id)
    """
    headers = {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
    list_url = f"{KEYCLOAK_BASE}/admin/realms/{REALM}/clients/{client_uuid}/protocol-mappers/models"

    desired_config: Dict[str, str] = {
        "user.attribute": TENANT_CLAIM,
        "claim.name": TENANT_CLAIM,
        "jsonType.label": "String",
        "id.token.claim": "true",
        "access.token.claim": "true",
        "userinfo.token.claim": "true",
        "multivalued": "false",
    }

    desired_payload: Dict[str, Any] = {
        "name": "org-id",
        "protocol": "openid-connect",
        "protocolMapper": "oidc-usermodel-attribute-mapper",
        "config": desired_config,
    }

    with _http_client() as c:
        r = c.get(list_url, headers=headers)
        r.raise_for_status()
        mappers = r.json()

        # Delete any existing mapper with same name
        if isinstance(mappers, list):
            for m in mappers:
                if isinstance(m, dict) and m.get("name") == "org-id":
                    mid = m.get("id")
                    if isinstance(mid, str) and mid:
                        del_url = f"{list_url}/{mid}"
                        rd = c.delete(del_url, headers=headers)
                        if rd.status_code != 204:
                            raise RuntimeError(
                                f"Failed to delete existing mapper: {rd.status_code} {rd.text}"
                            )
                    break

        # Create mapper
        rc = c.post(list_url, headers=headers, json=desired_payload)
        if rc.status_code not in (201, 409):
            raise RuntimeError(f"Failed to create mapper: {rc.status_code} {rc.text}")


def _kc_upsert_user(admin_token: str, username: str, password: str, org_id: Optional[str]) -> str:
    """
    Create user if missing; otherwise update user to be LOGIN-READY for password grant:
    - enabled=True
    - emailVerified=True
    - requiredActions=[]
    - password set (reset-password) with temporary=False
    - attributes set/removed (TENANT_CLAIM)
    """
    headers = {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
    users_url = f"{KEYCLOAK_BASE}/admin/realms/{REALM}/users"

    with _http_client() as c:
        # 1) Search user by username
        r = c.get(users_url, headers=headers, params={"username": username})
        r.raise_for_status()
        arr = r.json()

        user_id: Optional[str] = None
        if isinstance(arr, list) and arr:
            uid = arr[0].get("id")
            if isinstance(uid, str) and uid:
                user_id = uid

        # 2) Create if missing
        if user_id is None:
            create_payload: Dict[str, Any] = {
                "username": username,
                "enabled": True,
                "emailVerified": True,
                "email": f"{username}@example.com",
                "firstName": username,
                "lastName": "Test",
                "requiredActions": [],  # IMPORTANT: avoid "Account is not fully set up"
            }
            rc = c.post(users_url, headers=headers, json=create_payload)
            if rc.status_code not in (201, 409):
                raise RuntimeError(f"Failed to create user: {rc.status_code} {rc.text}")

            # Re-fetch to get id
            r2 = c.get(users_url, headers=headers, params={"username": username})
            r2.raise_for_status()
            arr2 = r2.json()
            if not isinstance(arr2, list) or not arr2:
                raise RuntimeError("User created but cannot be found")
            uid2 = arr2[0].get("id")
            if not isinstance(uid2, str) or not uid2:
                raise RuntimeError("User id missing after creation")
            user_id = uid2

        assert user_id is not None

        # 3) GET full representation (safer than PUT minimal)
        get_url = f"{users_url}/{user_id}"
        rep_r = c.get(get_url, headers={"Authorization": f"Bearer {admin_token}"})
        rep_r.raise_for_status()
        rep = rep_r.json()
        if not isinstance(rep, dict):
            raise RuntimeError("Invalid user representation")

        # 4) Force LOGIN-READY flags
        rep["username"] = username
        rep["enabled"] = True
        rep["emailVerified"] = True
        rep["requiredActions"] = []  # CRITICAL

        # 5) Merge attributes
        attrs = rep.get("attributes")
        if not isinstance(attrs, dict):
            attrs = {}

        if org_id is not None:
            attrs[TENANT_CLAIM] = [org_id]
        else:
            attrs.pop(TENANT_CLAIM, None)

        rep["attributes"] = attrs

        # 6) PUT back full representation
        upd = c.put(get_url, headers=headers, json=rep)
        if upd.status_code != 204:
            raise RuntimeError(f"Failed to update user rep: {upd.status_code} {upd.text}")

        # 7) Reset password (temporary=False) => loggable
        pwd_url = f"{users_url}/{user_id}/reset-password"
        pwd_payload = {"type": "password", "temporary": False, "value": password}
        pwd_r = c.put(pwd_url, headers=headers, json=pwd_payload)
        if pwd_r.status_code != 204:
            raise RuntimeError(f"reset-password failed: {pwd_r.status_code} {pwd_r.text}")

        # 8) Defensive check: requiredActions must be empty
        rep2_r = c.get(get_url, headers={"Authorization": f"Bearer {admin_token}"})
        rep2_r.raise_for_status()
        rep2 = rep2_r.json()
        ra = rep2.get("requiredActions")
        if isinstance(ra, list) and len(ra) > 0:
            raise RuntimeError(
                f"User still has requiredActions={ra} (Account not fully set up) username={username}"
            )

        return user_id


def _kc_assign_client_role(admin_token: str, client_uuid: str, user_uuid: str, role_name: str) -> None:
    headers = {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}

    role_url = f"{KEYCLOAK_BASE}/admin/realms/{REALM}/clients/{client_uuid}/roles/{role_name}"
    map_url = f"{KEYCLOAK_BASE}/admin/realms/{REALM}/users/{user_uuid}/role-mappings/clients/{client_uuid}"

    with _http_client() as c:
        rr = c.get(role_url, headers=headers)
        rr.raise_for_status()
        role_rep = rr.json()
        if not isinstance(role_rep, dict):
            raise RuntimeError("Invalid role representation")

        rp = c.post(map_url, headers=headers, json=[role_rep])
        if rp.status_code not in (204, 409):
            raise RuntimeError(f"Failed to map role: {rp.status_code} {rp.text}")


# ==========================================================
# Backend helpers
# ==========================================================


def _backend_get(path: str, token: str, params: Optional[Dict[str, str]] = None) -> httpx.Response:
    url = f"{BACKEND_BASE}{path}"
    headers = {"Authorization": f"Bearer {token}"}
    with _http_client() as c:
        return c.get(url, headers=headers, params=params)


def _get_token_until_claim(username: str, password: str, org_id: str) -> Tuple[str, Dict[str, Any]]:
    """
    Some setups may take a moment to reflect new mappers/attributes in issued tokens.
    We retry a few times and fail with full last payload for debugging.
    """
    last_payload: Dict[str, Any] = {}
    for _ in range(10):
        tok = _token_password_grant(username, password)
        payload = _jwt_payload_unverified(tok)
        last_payload = payload
        if payload.get(TENANT_CLAIM) == org_id:
            return tok, payload
        time.sleep(0.5)
    raise AssertionError(f"Token missing '{TENANT_CLAIM}' or mismatch. Payload={last_payload}")


# ==========================================================
# Tests
# ==========================================================


@pytest.mark.integration
def test_system_user_me_and_audits_ok() -> None:
    """
    System user can:
      - /secure/me
      - /secure/audits even with org_id query (system bypass)
    """
    username = _env("KEYCLOAK_USERNAME")
    password = _env("KEYCLOAK_PASSWORD")
    token = _token_password_grant(username, password)

    r1 = _backend_get("/api/v1/secure/me", token)
    assert r1.status_code == 200, r1.text
    data1 = r1.json()
    assert data1.get("is_system") is True
    roles = data1.get("roles")
    assert isinstance(roles, list)
    assert "system" in roles

    r2 = _backend_get("/api/v1/secure/audits", token, params={"org_id": "some-org"})
    assert r2.status_code == 200, r2.text


@pytest.mark.integration
def test_non_system_org_id_claim_and_spoofing_protection() -> None:
    """
    Non-system user:
      - MUST have org_id claim in token
      - /secure/me returns org_id
      - /secure/audits ignores spoof query and uses token org_id
    """
    admin_token = _kc_admin_token()
    client_uuid = _kc_get_client_uuid(admin_token)

    _kc_ensure_client_role(admin_token, client_uuid, "editor")
    _kc_ensure_client_role(admin_token, client_uuid, "viewer")

    # CRITICAL: hard reset mapper before issuing tokens
    _kc_ensure_user_attr_mapper(admin_token, client_uuid)

    editor_username = _unique("editor")
    editor_password = "Editor@@00000"
    org_id = "11111111-1111-1111-1111-111111111111"

    user_uuid = _kc_upsert_user(admin_token, editor_username, editor_password, org_id=org_id)
    _kc_assign_client_role(admin_token, client_uuid, user_uuid, "editor")

    # Validate token claim (what matters to backend)
    token, payload_dbg = _get_token_until_claim(editor_username, editor_password, org_id=org_id)
    assert payload_dbg.get(TENANT_CLAIM) == org_id

    r1 = _backend_get("/api/v1/secure/me", token)
    assert r1.status_code == 200, r1.text
    data1 = r1.json()
    assert data1.get("is_system") is False
    assert data1.get("org_id") == org_id

    r2 = _backend_get("/api/v1/secure/audits", token, params={"org_id": "HACK"})
    assert r2.status_code == 200, r2.text
    data2 = r2.json()
    assert data2.get("effective_org_id") == org_id


@pytest.mark.integration
def test_non_system_without_org_id_is_forbidden() -> None:
    """
    Non-system user WITHOUT org_id:
      - can login (password grant)
      - but /secure/me must return 403 (backend enforces tenant claim)
    """
    admin_token = _kc_admin_token()
    client_uuid = _kc_get_client_uuid(admin_token)

    _kc_ensure_client_role(admin_token, client_uuid, "viewer")
    _kc_ensure_user_attr_mapper(admin_token, client_uuid)

    viewer_username = _unique("viewer_no_org")
    viewer_password = "Viewer@@00000"

    user_uuid = _kc_upsert_user(admin_token, viewer_username, viewer_password, org_id=None)
    _kc_assign_client_role(admin_token, client_uuid, user_uuid, "viewer")

    token = _token_password_grant(viewer_username, viewer_password)

    r = _backend_get("/api/v1/secure/me", token)
    assert r.status_code == 403, r.text