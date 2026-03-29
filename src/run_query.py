"""
run_query.py

Objetivo: Entry point del sistema de soporte al cliente para una app de citas.
Orquesta el flujo completo: PII hashing → Safety → Router → Especialista → Métricas.

Release Date: 2026-03-29

Copyright 2026 Henry Academy.
"""

from __future__ import annotations

import argparse
import json
import logging
import time
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from .metrics import log_metrics
from .models import TicketResult
from .pii_hasher import hash_pii
from .router import classify
from .safety import check_safety
from .specialists import run_specialist

# ── Logger ─────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


# ── Flujo principal ────────────────────────────────────────────────────────────

def process_ticket(ticket: str) -> dict:
    """
    Procesa un ticket de soporte completo y devuelve el resultado en JSON.

    Flujo:
        1. PII hashing   — anonimiza datos personales antes del LLM
        2. Safety check  — bloquea inputs adversariales
        3. Router        — clasifica categoría + subcategoría (few-shot CoT)
        4. Specialist    — genera respuesta con CoT de 4 pasos
        5. Métricas      — registra tokens, latencia y costo en metrics.json
    """
    start = time.perf_counter()
    tokens_in = 0
    tokens_out = 0
    safety_flag = False

    # ── 1. PII Hashing ─────────────────────────────────────────────────────────
    logger.info("[PIPELINE] Paso 1: PII hashing")
    sanitized, pii_map, pii_detected = hash_pii(ticket)
    if pii_detected:
        logger.info(f"[PII] {len(pii_map)} elemento(s) anonimizado(s)")

    # ── 2. Safety ──────────────────────────────────────────────────────────────
    logger.info("[PIPELINE] Paso 2: Safety check")
    is_safe, reason, fallback = check_safety(sanitized)

    if not is_safe:
        safety_flag = True
        latency_ms = (time.perf_counter() - start) * 1000
        log_metrics("BLOQUEADO", 0, 0, latency_ms, safety_flag=True)
        logger.warning(f"[PIPELINE] Input bloqueado: {reason}")
        return fallback  # type: ignore[return-value]

    # ── 3. Router ──────────────────────────────────────────────────────────────
    logger.info("[PIPELINE] Paso 3: Router")
    router_output, router_usage = classify(sanitized)
    tokens_in += router_usage.get("input_tokens", 0)
    tokens_out += router_usage.get("output_tokens", 0)

    # ── 4. Especialista ────────────────────────────────────────────────────────
    logger.info(f"[PIPELINE] Paso 4: Especialista {router_output.categoria}")
    specialist_output, spec_usage = run_specialist(
        sanitized, router_output.categoria, router_output.subcategoria
    )
    tokens_in += spec_usage.get("input_tokens", 0)
    tokens_out += spec_usage.get("output_tokens", 0)

    # ── 5. Métricas ────────────────────────────────────────────────────────────
    latency_ms = (time.perf_counter() - start) * 1000
    log_metrics(router_output.categoria, tokens_in, tokens_out, latency_ms, safety_flag)

    # ── Resultado final ────────────────────────────────────────────────────────
    result = TicketResult(
        categoria=router_output.categoria,
        subcategoria=router_output.subcategoria,
        chain_of_thought=specialist_output.chain_of_thought,
        respuesta=specialist_output.respuesta,
        confianza=specialist_output.confianza,
        prioridad=specialist_output.prioridad,
        acciones=specialist_output.acciones,
        pii_detectado=pii_detected,
        input_sanitizado=True,
    )
    return result.model_dump()


# ── CLI ────────────────────────────────────────────────────────────────────────

def _print_result(result: dict) -> None:
    print("\n" + "=" * 60)
    print("  RESULTADO DEL TICKET")
    print("=" * 60)
    print(f"  Categoría  : {result['categoria']} / {result['subcategoria']}")
    print(f"  Prioridad  : {result['prioridad']}")
    print(f"  Confianza  : {result['confianza']:.0%}")
    print(f"  PII        : {'Detectada y anonimizada' if result['pii_detectado'] else 'No detectada'}")
    print()
    print("  RAZONAMIENTO (Chain of Thought):")
    for i, step in enumerate(result["chain_of_thought"], 1):
        print(f"    {i}. {step}")
    print()
    print("  RESPUESTA AL USUARIO:")
    print(f"    {result['respuesta']}")
    print()
    print("  ACCIONES RECOMENDADAS:")
    for action in result["acciones"]:
        print(f"    • {action}")
    print("=" * 60)
    print()
    print("  JSON completo:")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Sistema de soporte al cliente para una app de citas."
    )
    parser.add_argument(
        "-t", "--ticket",
        type=str,
        required=True,
        help='Ticket del usuario (e.g., "No puedo iniciar sesión en mi cuenta")',
    )
    parser.add_argument(
        "--json-only",
        action="store_true",
        help="Imprimir solo el JSON sin formato adicional",
    )
    args = parser.parse_args()

    resultado = process_ticket(args.ticket)

    if args.json_only:
        print(json.dumps(resultado, ensure_ascii=False, indent=2))
    else:
        _print_result(resultado)

# Ejemplos de uso:
# uv run python -m src.run_query -t "No puedo iniciar sesión, me dice que mi email no existe"
# uv run python -m src.run_query -t "Me cobraron dos veces este mes" --json-only
# uv run python -m src.run_query -t "Un usuario me acosa y me manda fotos sin permiso"
