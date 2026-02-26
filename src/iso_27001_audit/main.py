from fastapi import FastAPI

from iso_27001_audit.utils.logger.setup import setup_logging
from src.iso_27001_audit.logger.app import AppLogger

setup_logging()

log = AppLogger(__name__).get()

app = FastAPI(title="iso-27001-audit")


@app.on_event("startup")
def startup():
    log.info("Application startup complete")


@app.get("/health")
def health():
    log.info("Health check")
    return {"status": "ok"}