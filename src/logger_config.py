"""
logger_config.py

Objetivo: Logger centralizado con colores para todos los módulos del sistema.
Inspirado en el patrón del profesor (logger_configuration.py).

Release Date: 2026-03-29

Copyright 2026 Henry Academy.
"""

from __future__ import annotations

import logging

# ── Códigos ANSI ───────────────────────────────────────────────────────────────
_RESET  = "\033[0m"
_BOLD   = "\033[1m"
_COLORS = {
    "DEBUG":    "\033[36m",   # cyan
    "INFO":     "\033[32m",   # verde
    "WARNING":  "\033[33m",   # amarillo
    "ERROR":    "\033[31m",   # rojo
    "CRITICAL": "\033[35m",   # magenta
}


class _ColorFormatter(logging.Formatter):
    """Formateador con colores ANSI por nivel de log."""

    FMT = "{color}{bold}[{level}]{reset} {color}{time}{reset} {name} — {msg}"

    def format(self, record: logging.LogRecord) -> str:
        color = _COLORS.get(record.levelname, _RESET)
        time_str = self.formatTime(record, "%H:%M:%S")
        return self.FMT.format(
            color=color,
            bold=_BOLD,
            level=record.levelname[0],  # D / I / W / E / C
            reset=_RESET,
            time=time_str,
            name=record.name.split(".")[-1],
            msg=record.getMessage(),
        )


_configured: set[str] = set()


def get_logger(name: str) -> logging.Logger:
    """
    Devuelve un logger con handler coloreado. Idempotente: si ya fue
    configurado, devuelve el mismo logger sin añadir handlers duplicados.
    """
    logger = logging.getLogger(name)

    if name not in _configured:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        handler.setFormatter(_ColorFormatter())
        logger.addHandler(handler)
        logger.propagate = False
        _configured.add(name)

    return logger
