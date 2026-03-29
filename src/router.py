"""
router.py

Objetivo: Clasificar el ticket del usuario en categoría + subcategoría usando
few-shot CoT. Devuelve también el uso de tokens para acumulación en métricas.

Release Date: 2026-03-29

Copyright 2026 Henry Academy.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from .models import RouterOutput

load_dotenv(Path(__file__).parent.parent / ".env")
logger = logging.getLogger(__name__)


def _load_prompt(name: str) -> str:
    path = Path(__file__).parent.parent / "prompts" / name
    return path.read_text(encoding="utf-8")


def classify(ticket: str) -> tuple[RouterOutput, dict]:
    """
    Clasifica el ticket y devuelve (RouterOutput, usage_dict).
    usage_dict = {"input_tokens": int, "output_tokens": int}
    """
    system_prompt = _load_prompt("router_prompt.md")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    llm = ChatOpenAI(model=model, temperature=0.1)
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "Ticket a clasificar:\n{ticket}"),
    ])

    chain = prompt | llm.with_structured_output(
        RouterOutput, method="function_calling", include_raw=True
    )
    result = chain.invoke({"ticket": ticket})

    parsed: RouterOutput = result["parsed"]
    raw_msg = result["raw"]
    usage = raw_msg.usage_metadata or {"input_tokens": 0, "output_tokens": 0}

    logger.info(f"[ROUTER] {parsed.categoria} / {parsed.subcategoria} — {parsed.razonamiento}")
    return parsed, usage
