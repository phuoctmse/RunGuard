"""AI reasoner that uses Claude API to analyze incidents."""

import json
import logging
import re
from typing import Any

import anthropic

from runguard.backend.ai.prompts import SYSTEM_PROMPT, build_analysis_prompt
from runguard.backend.config import settings

logger = logging.getLogger(__name__)


def _strip_markdown_fences(text: str) -> str:
    """Strip markdown code fences from text to extract raw JSON."""
    stripped = re.sub(r"^```(?:json)?\s*\n?", "", text.strip())
    stripped = re.sub(r"\n?```\s*$", "", stripped)
    return stripped.strip()


class AIReasoner:
    """Analyzes incidents using Claude API to generate remediation plans."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
    ):
        kwargs: dict[str, Any] = {
            "api_key": api_key or settings.anthropic_api_key,
        }
        url = base_url or settings.anthropic_base_url
        if url:
            kwargs["base_url"] = url
        self.client = anthropic.AsyncAnthropic(**kwargs)
        self.model = model or settings.claude_model

    async def analyze(
        self,
        incident_id: str,
        namespace: str,
        workload: str,
        severity: str,
        raw_alert: str,
        evidence: dict[str, Any],
        runbook_title: str = "",
    ) -> dict[str, Any]:
        """Analyze incident and return structured remediation plan.

        Returns dict with keys: summary, root_causes, actions.
        Returns empty structure on error.
        """
        prompt = build_analysis_prompt(
            incident_id=incident_id,
            namespace=namespace,
            workload=workload,
            severity=severity,
            raw_alert=raw_alert,
            evidence=evidence,
            runbook_title=runbook_title,
        )

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=settings.llm_max_output_tokens,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )
            text_blocks = [b.text for b in response.content if hasattr(b, "text")]
            content = text_blocks[0] if text_blocks else ""
            content = _strip_markdown_fences(content)
            result: dict[str, Any] = json.loads(content)
            return result
        except Exception as e:
            logger.error("AI analysis failed for %s: %s", incident_id, e)
            return {
                "summary": "",
                "root_causes": [],
                "actions": [],
            }
