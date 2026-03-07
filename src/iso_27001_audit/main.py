from contextlib import asynccontextmanager

from fastapi import FastAPI

from iso_27001_audit.api.v1.router_wrapper import router as v1_router
from iso_27001_audit.config.setting import SettingsProvider
from iso_27001_audit.db.gateway import SqlAlchemyDatabaseGateway
from iso_27001_audit.logger.app import AppLogger
from iso_27001_audit.security.access_control import AccessControl
from iso_27001_audit.security.jwt_validator import JWTValidator
from iso_27001_audit.utils.logger.setup import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    log = AppLogger(__name__).get()

    settings_provider = SettingsProvider()
    settings = settings_provider.get_settings()

    jwt_validator = JWTValidator(
        issuer=str(settings["issuer"]),
        jwks_url=str(settings["jwks_url"]),
        verify_aud=bool(settings["verify_aud"]),
        expected_audience=str(settings["expected_audience"]),
    )

    access_control = AccessControl(
        jwt_validator=jwt_validator,
        keycloak_client_id=str(settings["keycloak_client_id"]),
        tenant_groups_claim=str(settings["tenant_groups_claim"]),
        tenant_group_prefix=str(settings["tenant_group_prefix"]),
    )

    db_gateway = SqlAlchemyDatabaseGateway(
        database_url=str(settings["database_url"]),
        echo=False,
    )
    db_gateway.create_schema()

    app.state.jwt_validator = jwt_validator
    app.state.access_control = access_control
    app.state.db_gateway = db_gateway

    log.info("startup")
    yield
    log.info("shutdown")

    db_gateway.dispose()


app = FastAPI(
    title="iso-27001-audit",
    lifespan=lifespan,
)

app.include_router(v1_router, prefix="/api/v1")