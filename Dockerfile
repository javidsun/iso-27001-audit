# ==========================================================
# ISO-27001-AUDIT - Backend container (Python 3.13)
# - Installs dependencies from pyproject.toml ONLY
# - Runs FastAPI via uvicorn
# ==========================================================

FROM python:3.13-slim

# ------------------------------
# Metadata
# ------------------------------
LABEL maintainer="javidshams"
LABEL project="iso-27001-audit"

# ------------------------------
# Python runtime behavior
# - no .pyc files
# - unbuffered logs (better for Docker logs)
# ------------------------------
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# ------------------------------
# Workdir inside container
# ------------------------------
WORKDIR /app

# ------------------------------
# System deps (keep minimal)
# build-essential: needed only if some deps compile native code
# curl: useful for debugging/health checks
# ------------------------------
RUN apt-get update \
  && apt-get install -y --no-install-recommends build-essential curl \
  && rm -rf /var/lib/apt/lists/*

# ------------------------------
# Copy project files
# We copy everything because `pip install .` needs:
# - pyproject.toml
# - src/ package
# ------------------------------
COPY . /app

# ------------------------------
# Install dependencies declared in pyproject.toml
# This is the key: you do NOT list fastapi/uvicorn here.
# ------------------------------
RUN pip install --upgrade pip \
  && pip install .

# ------------------------------
# Expose internal port
# ------------------------------
EXPOSE 8003

# ------------------------------
# Start FastAPI
# IMPORTANT:
# - Requires: src/iso_27001_audit/main.py
# - Requires: variable `app = FastAPI(...)` inside that file
# ------------------------------

CMD ["uvicorn", "iso_27001_audit.main:app", "--host", "0.0.0.0", "--port", "8003"]