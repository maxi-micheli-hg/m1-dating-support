"""
models.py

Pydantic schemas shared across all modules.
Release Date: 2026-03-29

Copyright 2026 Henry Academy.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class RouterOutput(BaseModel):
    categoria: Literal["SEGURIDAD", "MATCHES", "CUENTA", "PAGOS", "TECNICO"]
    subcategoria: str = Field(description="Subcategoría específica dentro de la categoría")
    razonamiento: str = Field(description="Explicación breve de por qué se eligió esta categoría")


class SpecialistOutput(BaseModel):
    chain_of_thought: list[str] = Field(description="Exactamente 4 pasos de razonamiento")
    respuesta: str = Field(description="Respuesta empática y accionable para el usuario")
    confianza: float = Field(ge=0.0, le=1.0, description="Confianza del agente en su respuesta (0-1)")
    prioridad: Literal["ALTA", "MEDIA", "BAJA"]
    acciones: list[str] = Field(description="Acciones recomendadas para el equipo de soporte")


class TicketResult(BaseModel):
    """Output final completo devuelto al caller."""
    categoria: str
    subcategoria: str
    chain_of_thought: list[str]
    respuesta: str
    confianza: float
    prioridad: str
    acciones: list[str]
    pii_detectado: bool
    input_sanitizado: bool
