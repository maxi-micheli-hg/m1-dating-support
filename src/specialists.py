"""
specialists.py

Objetivo: Agentes especialistas por categoría. Cada uno carga su prompt,
aplica CoT de 4 pasos y devuelve respuesta estructurada + uso de tokens.

Release Date: 2026-03-29

Copyright 2026 Henry Academy.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Callable

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from .logger_config import get_logger
from .models import SpecialistOutput

load_dotenv(Path(__file__).parent.parent / ".env")
logger = get_logger(__name__)


def _load_prompt(name: str) -> str:
    path = Path(__file__).parent.parent / "prompts" / name
    return path.read_text(encoding="utf-8")


def _run_specialist_chain(
    system_prompt: str,
    ticket: str,
    subcategoria: str,
) -> tuple[SpecialistOutput, dict]:
    """
    Función base compartida por todos los especialistas.
    Usa temperatura baja (0.3) para respuestas consistentes y evaluables.
    """
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    llm = ChatOpenAI(model=model, temperature=0.3)

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        (
            "human",
            "Subcategoría identificada: {subcategoria}\n\n"
            "Ticket del usuario:\n{ticket}\n\n"
            "Razoná en 4 pasos y genera la respuesta estructurada.",
        ),
    ])

    chain = prompt | llm.with_structured_output(
        SpecialistOutput, method="function_calling", include_raw=True
    )
    result = chain.invoke({"ticket": ticket, "subcategoria": subcategoria})

    parsed: SpecialistOutput = result["parsed"]
    usage = result["raw"].usage_metadata or {"input_tokens": 0, "output_tokens": 0}

    logger.info(
        f"[SPECIALIST] prioridad={parsed.prioridad} "
        f"confianza={parsed.confianza} "
        f"acciones={parsed.acciones}"
    )
    return parsed, usage


def _specialist_seguridad(ticket: str, subcategoria: str) -> tuple[SpecialistOutput, dict]:
    logger.info("[AGENT] Especialista SEGURIDAD activado")
    return _run_specialist_chain(_load_prompt("specialists/seguridad.md"), ticket, subcategoria)


def _specialist_matches(ticket: str, subcategoria: str) -> tuple[SpecialistOutput, dict]:
    logger.info("[AGENT] Especialista MATCHES activado")
    return _run_specialist_chain(_load_prompt("specialists/matches.md"), ticket, subcategoria)


def _specialist_cuenta(ticket: str, subcategoria: str) -> tuple[SpecialistOutput, dict]:
    logger.info("[AGENT] Especialista CUENTA activado")
    return _run_specialist_chain(_load_prompt("specialists/cuenta.md"), ticket, subcategoria)


def _specialist_pagos(ticket: str, subcategoria: str) -> tuple[SpecialistOutput, dict]:
    logger.info("[AGENT] Especialista PAGOS activado")
    return _run_specialist_chain(_load_prompt("specialists/pagos.md"), ticket, subcategoria)


def _specialist_tecnico(ticket: str, subcategoria: str) -> tuple[SpecialistOutput, dict]:
    logger.info("[AGENT] Especialista TECNICO activado")
    return _run_specialist_chain(_load_prompt("specialists/tecnico.md"), ticket, subcategoria)


_DISPATCH: dict[str, Callable] = {
    "SEGURIDAD": _specialist_seguridad,
    "MATCHES":   _specialist_matches,
    "CUENTA":    _specialist_cuenta,
    "PAGOS":     _specialist_pagos,
    "TECNICO":   _specialist_tecnico,
}


def run_specialist(
    ticket: str, categoria: str, subcategoria: str
) -> tuple[SpecialistOutput, dict]:
    """Despacha al especialista correcto según la categoría del router."""
    fn = _DISPATCH.get(categoria, _specialist_tecnico)
    return fn(ticket, subcategoria)
