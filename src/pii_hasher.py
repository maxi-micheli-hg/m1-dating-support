"""
pii_hasher.py

Objetivo: Detectar y reemplazar PII (información personal identificable) en el
texto del usuario antes de enviarlo al LLM. Los tokens generados son consistentes
dentro de la misma sesión: la misma PII siempre produce el mismo token.

Release Date: 2026-03-29

Copyright 2026 Henry Academy.
"""

from __future__ import annotations

import hashlib
import re

# ── Patrones de PII ────────────────────────────────────────────────────────────
_PII_PATTERNS: list[tuple[str, str]] = [
    # Orden importa: más específico primero para evitar solapamiento
    ("EMAIL",       r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"),
    ("PHONE",       r"\b(\+?[\d]{1,3}[\s\-]?)?(\(?\d{2,4}\)?[\s\-]?)(\d{3,4}[\s\-]?\d{3,4})\b"),
    ("HANDLE",      r"(?<!\w)@[A-Za-z0-9_]{3,30}\b"),
    ("ID_DOC",      r"\b(?:DNI|CUIT|CUIL|RUT|CPF|pasaporte|passport)\s*:?\s*[\d\-\.]{6,15}\b"),
    ("CREDIT_CARD", r"\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b"),
]


def _make_token(pii_type: str, value: str) -> str:
    """Genera un token corto y consistente para un valor de PII."""
    h = hashlib.md5(value.lower().encode()).hexdigest()[:4]
    return f"[{pii_type}_{h}]"


def hash_pii(text: str) -> tuple[str, dict[str, str], bool]:
    """
    Reemplaza PII en el texto con tokens anonimizados.

    Returns:
        sanitized_text: texto con PII reemplazada
        token_map:      {valor_original: token}  — para auditoría interna
        pii_detected:   True si se encontró al menos una PII
    """
    token_map: dict[str, str] = {}
    pii_detected = False

    for pii_type, pattern in _PII_PATTERNS:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            value = match.group(0)
            if value not in token_map:
                token_map[value] = _make_token(pii_type, value)
                pii_detected = True

    sanitized = text
    # Reemplazar de mayor a menor longitud para evitar reemplazos parciales
    for original, token in sorted(token_map.items(), key=lambda x: -len(x[0])):
        sanitized = sanitized.replace(original, token)

    return sanitized, token_map, pii_detected
