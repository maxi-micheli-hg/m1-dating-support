"""
metrics.py

Objetivo: Registrar métricas de cada ejecución (tokens, latencia, costo estimado)
en metrics/metrics.json para observabilidad y análisis posterior.

Release Date: 2026-03-29

Copyright 2026 Henry Academy.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from .logger_config import get_logger

logger = get_logger(__name__)

# gpt-4o-mini pricing (USD por 1K tokens)
_COST_INPUT_PER_1K = 0.000150
_COST_OUTPUT_PER_1K = 0.000600

_METRICS_PATH = Path(__file__).parent.parent / "metrics" / "metrics.json"


def log_metrics(
    categoria: str,
    tokens_prompt: int,
    tokens_completion: int,
    latency_ms: float,
    safety_flag: bool = False,
) -> None:
    """Agrega una entrada al log de métricas."""
    cost = (tokens_prompt / 1000 * _COST_INPUT_PER_1K) + (
        tokens_completion / 1000 * _COST_OUTPUT_PER_1K
    )

    entry = {
        "timestamp": datetime.now().isoformat(),
        "categoria": categoria,
        "tokens_prompt": tokens_prompt,
        "tokens_completion": tokens_completion,
        "total_tokens": tokens_prompt + tokens_completion,
        "latency_ms": round(latency_ms, 2),
        "estimated_cost_usd": round(cost, 6),
        "safety_flag": safety_flag,
    }

    entries: list[dict] = []
    if _METRICS_PATH.exists():
        try:
            with open(_METRICS_PATH, encoding="utf-8") as f:
                entries = json.load(f)
        except (json.JSONDecodeError, OSError):
            entries = []

    entries.append(entry)
    _METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(_METRICS_PATH, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)

    logger.info(
        f"[METRICS] categoria={entry['categoria']} "
        f"tokens={entry['total_tokens']} "
        f"latencia={entry['latency_ms']}ms "
        f"costo=${entry['estimated_cost_usd']}"
    )
