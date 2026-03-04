# ==========================================================
# ISO-27001-AUDIT - Backend container (Python 3.13)
# - Installs dependencies from pyproject.toml (PEP 621)
# - Uses layer caching properly (fast rebuilds)
# - Runs FastAPI via uvicorn
# ==========================================================

FROM python:3.13-slim

LABEL maintainer="javidshams"
LABEL project="iso-27001-audit"

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Minimal system deps:
# - curl: debug / healthcheck
# - ca-certificates: TLS
RUN apt-get update \
  && apt-get install -y --no-install-recommends curl ca-certificates \
  && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --no-cache-dir -U pip

# --------------------------------
# COPY ONLY metadata first (cache)
# --------------------------------
COPY pyproject.toml /app/pyproject.toml

# If you have any packaging files, copy them too.
# (Safe even if you don't have them; but Docker will fail if missing.)
# So only include what exists in your repo:
# COPY README.md /app/README.md

# Copy src layout (needed for editable install fallback scenarios)
COPY src /app/src

# Install runtime deps (project dependencies)
# We install the project in editable mode to avoid reinstalling on code changes
RUN pip install --no-cache-dir -e .

# --------------------------------
# Now copy the rest (app code, tests excluded if you use .dockerignore)
# --------------------------------
# If you want tests inside backend container, keep this copy.
# Otherwise add tests/ to .dockerignore
COPY . /app

EXPOSE 8003

CMD ["uvicorn", "iso_27001_audit.main:app", "--host", "0.0.0.0", "--port", "8003"]