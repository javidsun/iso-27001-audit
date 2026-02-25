from fastapi import FastAPI

app = FastAPI(title="iso-27001-audit")

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}