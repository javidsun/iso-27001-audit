from __future__ import annotations

import base64
import json
import os
import uuid
from typing import Any, Dict, Optional

import httpx
import pytest


def _env(name: str, default: Optional[str] = None) -> str:
    value = os.getenv(name, default)
    if value is None or not value.strip():
        raise RuntimeError(f"Missing env var: {name}")
    return value.strip()


BACKEND_BASE = _env("BACKEND_BASE")
KEYCLOAK_BASE = _env("KEYCLOAK_BASE")
REALM = _env("KEYCLOAK_REALM")
CLIENT_ID = _env("KEYCLOAK_CLIENT_ID")
ADMIN_USER = _env("KEYCLOAK_ADMIN_USER", "admin_audit")
ADMIN_PASS = _env("KEYCLOAK_ADMIN_PASS", "admin123")


def _http() -> httpx.Client:
    return httpx.Client(timeout=20.0)


def _unique(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def _jwt_payload_unverified(token: str) -> Dict[str, Any]:
    parts = token.split(".")
    if len(parts) != 3:
        return {}

    payload_b64 = parts[1]
    padding = "=" * (-len(payload_b64) % 4)
    raw = base64.urlsafe_b64decode((payload_b64 + padding).encode("utf-8"))
    data = json.loads(raw.decode("utf-8"))

    if not isinstance(data, dict):
        return {}

    return data


def _password_grant(username: str, password: str) -> str:
    url = f"{KEYCLOAK_BASE}/realms/{REALM}/protocol/openid-connect/token"
    payload = {
        "grant_type": "password",
        "client_id": CLIENT_ID,
        "username": username,
        "password": password,
    }

    with _http() as client:
        response = client.post(url, data=payload)
        response.raise_for_status()
        token = response.json().get("access_token")
        if not isinstance(token, str) or not token:
            raise RuntimeError("Missing access_token")
        return token


def _admin_token() -> str:
    url = f"{KEYCLOAK_BASE}/realms/master/protocol/openid-connect/token"
    payload = {
        "grant_type": "password",
        "client_id": "admin-cli",
        "username": ADMIN_USER,
        "password": ADMIN_PASS,
    }

    with _http() as client:
        response = client.post(url, data=payload)
        response.raise_for_status()
        token = response.json().get("access_token")
        if not isinstance(token, str) or not token:
            raise RuntimeError("Missing admin access_token")
        return token


def _client_uuid(admin_token: str) -> str:
    url = f"{KEYCLOAK_BASE}/admin/realms/{REALM}/clients"
    headers = {"Authorization": f"Bearer {admin_token}"}

    with _http() as client:
        response = client.get(url, headers=headers, params={"clientId": CLIENT_ID})
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, list) or not data:
            raise RuntimeError("Client not found")
        client_id = data[0].get("id")
        if not isinstance(client_id, str) or not client_id:
            raise RuntimeError("Client UUID missing")
        return client_id


def _ensure_client_role(admin_token: str, client_uuid: str, role_name: str) -> None:
    headers = {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
    role_url = f"{KEYCLOAK_BASE}/admin/realms/{REALM}/clients/{client_uuid}/roles/{role_name}"
    create_url = f"{KEYCLOAK_BASE}/admin/realms/{REALM}/clients/{client_uuid}/roles"

    with _http() as client:
        response = client.get(role_url, headers=headers)
        if response.status_code == 200:
            return
        if response.status_code != 404:
            raise RuntimeError(f"Unexpected GET role status: {response.status_code} {response.text}")

        created = client.post(
            create_url,
            headers=headers,
            json={"name": role_name, "description": f"role {role_name}"},
        )
        if created.status_code not in (201, 409):
            raise RuntimeError(f"Cannot create role: {created.status_code} {created.text}")


def _ensure_group(admin_token: str, group_name: str) -> str:
    headers = {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
    list_url = f"{KEYCLOAK_BASE}/admin/realms/{REALM}/groups"
    path = f"/{group_name}"

    with _http() as client:
        response = client.get(list_url, headers=headers)
        response.raise_for_status()
        groups = response.json()

        if isinstance(groups, list):
            for group in groups:
                if isinstance(group, dict) and group.get("path") == path:
                    group_id = group.get("id")
                    if isinstance(group_id, str) and group_id:
                        return group_id

        created = client.post(list_url, headers=headers, json={"name": group_name})
        if created.status_code not in (201, 204, 409):
            raise RuntimeError(f"Cannot create group: {created.status_code} {created.text}")

        response2 = client.get(list_url, headers=headers)
        response2.raise_for_status()
        groups2 = response2.json()
        if isinstance(groups2, list):
            for group in groups2:
                if isinstance(group, dict) and group.get("path") == path:
                    group_id = group.get("id")
                    if isinstance(group_id, str) and group_id:
                        return group_id

        raise RuntimeError("Group created but not found")


def _create_user(admin_token: str, username: str, password: str) -> str:
    headers = {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
    users_url = f"{KEYCLOAK_BASE}/admin/realms/{REALM}/users"

    with _http() as client:
        created = client.post(
            users_url,
            headers=headers,
            json={
                "username": username,
                "enabled": True,
                "emailVerified": True,
                "email": f"{username}@example.com",
                "firstName": username,
                "lastName": "Test",
                "requiredActions": [],
                "credentials": [{"type": "password", "value": password, "temporary": False}],
            },
        )
        if created.status_code not in (201, 409):
            raise RuntimeError(f"Cannot create user: {created.status_code} {created.text}")

        response = client.get(users_url, headers=headers, params={"username": username})
        response.raise_for_status()
        users = response.json()
        if not isinstance(users, list) or not users:
            raise RuntimeError("User not found after create")

        user_id = users[0].get("id")
        if not isinstance(user_id, str) or not user_id:
            raise RuntimeError("User id missing")

        return user_id


def _join_group(admin_token: str, user_id: str, group_id: str) -> None:
    headers = {"Authorization": f"Bearer {admin_token}"}
    url = f"{KEYCLOAK_BASE}/admin/realms/{REALM}/users/{user_id}/groups/{group_id}"

    with _http() as client:
        response = client.put(url, headers=headers)
        if response.status_code not in (204, 409):
            raise RuntimeError(f"Cannot join group: {response.status_code} {response.text}")


def _assign_client_role(admin_token: str, client_uuid: str, user_id: str, role_name: str) -> None:
    headers = {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
    role_url = f"{KEYCLOAK_BASE}/admin/realms/{REALM}/clients/{client_uuid}/roles/{role_name}"
    map_url = f"{KEYCLOAK_BASE}/admin/realms/{REALM}/users/{user_id}/role-mappings/clients/{client_uuid}"

    with _http() as client:
        role_response = client.get(role_url, headers=headers)
        role_response.raise_for_status()
        role_rep = role_response.json()

        mapped = client.post(map_url, headers=headers, json=[role_rep])
        if mapped.status_code not in (204, 409):
            raise RuntimeError(f"Cannot map role: {mapped.status_code} {mapped.text}")


def _backend_get(path: str, token: str, params: Optional[Dict[str, str]] = None) -> httpx.Response:
    url = f"{BACKEND_BASE}{path}"
    headers = {"Authorization": f"Bearer {token}"}

    with _http() as client:
        return client.get(url, headers=headers, params=params)


@pytest.mark.integration
def test_system_user_can_access_cross_tenant() -> None:
    token = _password_grant(_env("KEYCLOAK_USERNAME"), _env("KEYCLOAK_PASSWORD"))

    payload = _jwt_payload_unverified(token)
    assert "groups" in payload
    assert "/org-javid" in payload["groups"]

    response = _backend_get("/api/v1/secure/me", token)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["is_system"] is True
    assert body["tenant_group"] == "/org-javid"

    response2 = _backend_get("/api/v1/secure/audits", token, params={"tenant_group": "/org-hack"})
    assert response2.status_code == 200, response2.text
    body2 = response2.json()
    assert body2["effective_tenant_group"] == "/org-hack"


@pytest.mark.integration
def test_editor_user_gets_tenant_from_group_claim() -> None:
    admin = _admin_token()
    client_uuid = _client_uuid(admin)

    _ensure_client_role(admin, client_uuid, "editor")
    group_id = _ensure_group(admin, "org-aurora")

    username = _unique("editor")
    password = "Editor@@00000"

    user_id = _create_user(admin, username, password)
    _join_group(admin, user_id, group_id)
    _assign_client_role(admin, client_uuid, user_id, "editor")

    token = _password_grant(username, password)
    payload = _jwt_payload_unverified(token)

    groups = payload.get("groups")
    assert isinstance(groups, list), payload
    assert "/org-aurora" in groups, payload

    response = _backend_get("/api/v1/secure/me", token)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["is_system"] is False
    assert body["tenant_group"] == "/org-aurora"

    response2 = _backend_get("/api/v1/secure/audits", token, params={"tenant_group": "/org-hack"})
    assert response2.status_code == 200, response2.text
    body2 = response2.json()
    assert body2["effective_tenant_group"] == "/org-aurora"


@pytest.mark.integration
def test_viewer_without_tenant_group_is_forbidden() -> None:
    admin = _admin_token()
    client_uuid = _client_uuid(admin)

    _ensure_client_role(admin, client_uuid, "viewer")

    username = _unique("viewer")
    password = "Viewer@@00000"

    user_id = _create_user(admin, username, password)
    _assign_client_role(admin, client_uuid, user_id, "viewer")

    token = _password_grant(username, password)

    response = _backend_get("/api/v1/secure/me", token)
    assert response.status_code == 403, response.text