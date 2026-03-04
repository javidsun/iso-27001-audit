from contextlib import asynccontextmanager

from fastapi import FastAPI

from iso_27001_audit.api.v1.router_wrapper import router as v1_router
from iso_27001_audit.config.setting import get_settings
from iso_27001_audit.logger.app import AppLogger
from iso_27001_audit.security.jwt_validator import JWTValidator
from iso_27001_audit.utils.logger.setup import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    log = AppLogger(__name__).get()

    s = get_settings()
    app.state.jwt_validator = JWTValidator(
        issuer=str(s["issuer"]),
        jwks_url=str(s["jwks_url"]),
        verify_aud=bool(s["verify_aud"]),
        expected_audience=str(s["expected_audience"]),
    )

    log.info("startup")
    yield
    log.info("shutdown")


app = FastAPI(title="iso-27001-audit", lifespan=lifespan)
app.include_router(v1_router, prefix="/api/v1")