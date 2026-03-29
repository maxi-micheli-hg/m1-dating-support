"""
api/main.py

Objetivo: Exponer el sistema de soporte al cliente como una API REST con FastAPI.
Endpoints:
    POST /ticket   → procesa un ticket y devuelve el JSON estructurado
    GET  /health   → liveness check
    GET  /metrics  → devuelve el historial de métricas registradas

Uso:
    uv run uvicorn api.main:app --reload --port 8000

Release Date: 2026-03-29

Copyright 2026 Henry Academy.
"""

from __future__ import annotations

import json
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

load_dotenv(Path(__file__).parent.parent / ".env")

# Importar después del load_dotenv para que las variables ya estén disponibles
from src.run_query import process_ticket  # noqa: E402

app = FastAPI(
    title="Dating App — Customer Support API",
    description=(
        "Asistente de soporte al cliente para una app de citas. "
        "Clasifica tickets con Chain-of-Thought y devuelve respuestas estructuradas."
    ),
    version="1.0.0",
)

_METRICS_PATH = Path(__file__).parent.parent / "metrics" / "metrics.json"


# ── Schemas de la API ──────────────────────────────────────────────────────────

class TicketRequest(BaseModel):
    ticket: str

    model_config = {
        "json_schema_extra": {
            "example": {"ticket": "No puedo iniciar sesión en mi cuenta"}
        }
    }


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health", tags=["Sistema"])
def health() -> dict:
    """Liveness check — responde 200 si el servicio está activo."""
    return {"status": "ok", "service": "dating-support-api"}


@app.post("/ticket", tags=["Soporte"])
def submit_ticket(body: TicketRequest) -> JSONResponse:
    """
    Procesa un ticket de soporte al cliente.

    Flujo interno:
    1. PII hashing   — anonimiza datos personales
    2. Safety check  — bloquea prompt injection / jailbreak
    3. Router        — clasifica con few-shot CoT
    4. Especialista  — genera respuesta con CoT de 4 pasos
    5. Métricas      — registra tokens / latencia / costo

    Returns el JSON estructurado con categoría, chain_of_thought, respuesta,
    confianza, prioridad y acciones recomendadas.
    """
    if not body.ticket.strip():
        raise HTTPException(status_code=422, detail="El campo 'ticket' no puede estar vacío.")

    result = process_ticket(body.ticket)
    return JSONResponse(content=result)


@app.get("/metrics", tags=["Observabilidad"])
def get_metrics() -> JSONResponse:
    """
    Devuelve el historial completo de métricas registradas en metrics.json.
    Incluye tokens, latencia, costo y safety_flag por cada ejecución.
    """
    if not _METRICS_PATH.exists():
        return JSONResponse(content=[])

    try:
        data = json.loads(_METRICS_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise HTTPException(status_code=500, detail=f"Error leyendo métricas: {exc}") from exc

    return JSONResponse(content=data)
