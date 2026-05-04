"""Runbook API routes."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/runbooks", tags=["runbooks"])

# In-memory store for MVP
_runbooks: dict = {}


class RunbookCreateRequest(BaseModel):
    title: str
    content: str  # Raw Markdown


@router.post("", status_code=201)
async def create_or_update_runbook(request: RunbookCreateRequest):
    """Create or update a runbook from Markdown content."""
    from runguard.backend.compiler.parser import parse_runbook_markdown
    from runguard.backend.compiler.extractor import extract_metadata

    sections = parse_runbook_markdown(request.content)
    runbook = extract_metadata(sections, raw_markdown=request.content)
    _runbooks[runbook.id] = runbook.model_dump()
    return _runbooks[runbook.id]


@router.get("")
async def list_runbooks():
    """List all runbooks."""
    return list(_runbooks.values())
