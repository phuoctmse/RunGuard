"""Runbook data model."""

from typing import Any

from pydantic import BaseModel


class Runbook(BaseModel):
    """A parsed runbook with extracted metadata."""

    id: str
    title: str
    scope: dict[str, Any]  # {"namespaces": [...], "workloads": [...]}
    allowed_tools: list[str] = []
    forbidden_tools: list[str] = []
    severity: str = "medium"
    rollback_steps: list[str] = []
    raw_markdown: str = ""
    version: int = 1
