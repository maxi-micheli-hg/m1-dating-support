"""
safety.py

Objetivo: Detectar y bloquear inputs adversariales (prompt injection, jailbreak,
contenido extremo) antes de que lleguen al LLM.
Los intentos bloqueados se registran en logs para auditoría.

Release Date: 2026-03-29

Copyright 2026 Henry Academy.
"""

from __future__ import annotations

import re

from .logger_config import get_logger

logger = get_logger(__name__)

# ── Patrones de inyección / jailbreak ─────────────────────────────────────────
_INJECTION_PATTERNS: list[tuple[str, str]] = [
    ("prompt_injection",  r"ignora\s+(tus\s+)?(instrucciones|reglas|sistema|todo)"),
    ("prompt_injection",  r"olvida\s+(todo|tus|las\s+instrucciones)"),
    ("role_override",     r"eres\s+ahora\s+un"),
    ("role_override",     r"actúa\s+como\s+(si\s+fueras|un\s+)"),
    ("role_override",     r"pretende\s+que\s+(eres|no\s+tienes)"),
    ("jailbreak",         r"\bDAN\b"),
    ("jailbreak",         r"jailbreak"),
    ("system_override",   r"(system|SYSTEM)\s*:"),
    ("system_override",   r"<\s*system\s*>"),
    ("system_override",   r"\[INST\]"),
    ("data_extraction",   r"(muestra|revela|dame|lista)\s+(todos\s+)?(los\s+)?(datos|usuarios|registros|contraseñas)"),
]

# ── Respuesta de fallback ──────────────────────────────────────────────────────
def _fallback_response() -> dict:
    return {
        "categoria": "BLOQUEADO",
        "subcategoria": "input_adversarial",
        "chain_of_thought": [
            "Input analizado como potencial ataque adversarial.",
            "Patrón de inyección o jailbreak detectado.",
            "Política de seguridad: bloqueo automático sin procesar.",
            "Respuesta de fallback activada.",
        ],
        "respuesta": (
            "No pudimos procesar tu mensaje. "
            "Por favor escribí tu consulta de forma directa y sin instrucciones al sistema. "
            "Si necesitás ayuda, contanos cuál es tu problema con la app."
        ),
        "confianza": 1.0,
        "prioridad": "ALTA",
        "acciones": ["log_adversarial_input", "escalar_a_humano"],
        "pii_detectado": False,
        "input_sanitizado": False,
    }


def check_safety(text: str) -> tuple[bool, str, dict | None]:
    """
    Evalúa si el texto es seguro para procesar.

    Returns:
        is_safe:           True si el input puede continuar al LLM
        reason:            'ok' o descripción del problema detectado
        fallback_response: None si es seguro, dict de respuesta si fue bloqueado
    """
    normalized = text.lower().strip()

    for attack_type, pattern in _INJECTION_PATTERNS:
        if re.search(pattern, normalized, re.IGNORECASE):
            logger.warning(f"[SAFETY] BLOQUEADO — tipo={attack_type} patrón='{pattern}'")
            logger.warning(f"[SAFETY] Input recibido: {text[:120]}...")
            return False, f"{attack_type}: {pattern}", _fallback_response()

    return True, "ok", None
