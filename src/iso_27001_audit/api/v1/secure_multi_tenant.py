from fastapi import APIRouter, Depends, HTTPException, Request

from iso_27001_audit.security.access_control import AccessControl

router = APIRouter(tags=["secure-multi-tenant"])


def _get_access_control(request: Request) -> AccessControl:
    access_control = getattr(request.app.state, "access_control", None)
    if not isinstance(access_control, AccessControl):
        raise HTTPException(status_code=500, detail="AccessControl not initialized on app.state")
    return access_control


def require_access_control(request: Request) -> AccessControl:
    return _get_access_control(request)


@router.get("/secure/me")
async def secure_me(
    request: Request,
    access_control: AccessControl = Depends(require_access_control),
) -> dict:
    principal = await access_control.authenticate(request)

    return {
        "ok": True,
        "sub": principal.sub,
        "username": principal.username,
        "roles": sorted(principal.roles),
        "is_system": principal.is_system,
        "tenant_group": principal.tenant_group,
    }


@router.get("/secure/audits")
async def secure_audits(
    request: Request,
    access_control: AccessControl = Depends(require_access_control),
) -> dict:
    principal = await access_control.authenticate(request)

    requested_tenant_group = request.query_params.get("tenant_group")

    if principal.is_system:
        effective_tenant_group = requested_tenant_group or "__SYSTEM__"
    else:
        assert principal.tenant_group is not None
        effective_tenant_group = principal.tenant_group

    return {
        "ok": True,
        "requested_tenant_group": requested_tenant_group,
        "effective_tenant_group": effective_tenant_group,
        "is_system": principal.is_system,
    }