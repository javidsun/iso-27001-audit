from iso_27001_audit.logger.app import AppLogger

from contextlib import asynccontextmanager
from fastapi import FastAPI

from iso_27001_audit.utils.logger.setup import setup_logging
from iso_27001_audit.api.v1.router_wrapper import router as v1_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    log = AppLogger(__name__).get()
    log.info("startup")
    yield
    log.info("shutdown")


app = FastAPI(title="iso-27001-audit", lifespan=lifespan)
app.include_router(v1_router, prefix="/api/v1")
