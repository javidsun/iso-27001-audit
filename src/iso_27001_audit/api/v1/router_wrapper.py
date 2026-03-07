from fastapi import APIRouter

from .health import router as health_router
from .secure import router as secure_router
from .secure_multi_tenant import router as secure_multi_tenant_router

router = APIRouter()
router.include_router(health_router, tags=["health"])
router.include_router(secure_router, tags=["secure"])
router.include_router(secure_multi_tenant_router, tags=["secure-multi-tenant"])