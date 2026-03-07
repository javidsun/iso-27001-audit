# Project

## Requirements
- Docker
- Docker Compose

## Quick start (dev)
1. Copy env template:
   - cp .env.example .env
2. Start:
   - docker compose up --build

## Notes
- Do not commit `.env`

## example di utility of loger 
```python
from iso_27001_audit.logger.audit import AuditLogger

audit_log = AuditLogger(__name__)
audit_log.audit_event(action="USER_LOGIN", subject="user_id:123", details={"ip": "1.2.3.4"})
```
# uso auth middleware

```python
from fastapi import APIRouter, Depends
from iso_27001_audit.middleware.auth_middleware import verify_token

router = APIRouter()


@router.get("/protected")
async def protected_route(user=Depends(verify_token)):
    return {
        "message": "Access granted",
        "user": user.get("preferred_username"),
    }
```

```python
from __future__ import annotations

from fastapi import FastAPI

from iso_27001_audit.api.v1.router import router as v1_router
from iso_27001_audit.config import get_settings
from iso_27001_audit.middleware.auth import AuthMiddleware

settings = get_settings()

app = FastAPI(title="iso-27001-audit")

# middleware (global auth)
app.add_middleware(
   AuthMiddleware,
   issuer=settings.keycloak_issuer,
   jwks_url=settings.keycloak_jwks_url,
   verify_aud=settings.jwt_verify_aud,
   expected_audience=settings.jwt_expected_audience,
   bypass_paths=[
      "/api/v1/health",
      "/docs",
      "/openapi.json",
      "/redoc",
   ],
)

# routes
app.include_router(v1_router, prefix="/api/v1")
```
## keycloak db docker access 
```bash
   docker exec -it iso-audit-keycloak-db psql -U admin_audit -d keycloak
```

```bash
   docker exec -it iso-audit-db psql -U iso_user -d iso_audit           
```
