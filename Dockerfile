# ── Imagen base ───────────────────────────────────────────────────────────────
FROM python:3.11-slim

# Variables de entorno para Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# ── Dependencias del sistema ───────────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# ── Dependencias Python ────────────────────────────────────────────────────────
COPY pyproject.toml .
RUN pip install --no-cache-dir ".[dev]"

# ── Código fuente ─────────────────────────────────────────────────────────────
COPY src/ src/
COPY api/ api/
COPY prompts/ prompts/
COPY metrics/ metrics/

# Directorio de métricas (puede estar vacío al iniciar)
RUN mkdir -p metrics

# ── Puerto y arranque ──────────────────────────────────────────────────────────
EXPOSE 8000

# Las variables sensibles (OPENAI_API_KEY) se pasan en runtime con --env-file o -e
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
