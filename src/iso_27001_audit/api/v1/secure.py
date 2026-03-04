from typing import Any, Dict

from fastapi import APIRouter, Depends, Request

from iso_27001_audit.security.jwt_validator import JWTValidator

router = APIRouter(tags=["secure"])


def _get_validator(request: Request) -> JWTValidator:
    validator = getattr(request.app.state, "jwt_validator", None)
    if not isinstance(validator, JWTValidator):
        raise RuntimeError("JWTValidator not initialized on app.state")
    return validator


async def require_jwt_payload(
    request: Request,
    validator: JWTValidator = Depends(_get_validator),
) -> Dict[str, Any]:
    return await validator.verify(request)


@router.get("/secure/ping")
async def secure_ping(payload: Dict[str, Any] = Depends(require_jwt_payload)) -> Dict[str, Any]:
    return {"ok": True, "sub": payload.get("sub")}