import json
import logging
from typing import Any

import anthropic

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an SRE incident analysis assistant. Analyze the incident and return a JSON response with:

{
  "root_cause": "string - the most likely root cause",
  "confidence": 0.0-1.0,
  "evidence_citations": ["list of specific evidence supporting the conclusion"],
  "actions": ["list of recommended remediation actions"]
}

Rules:
- Only recommend actions that are safe and reversible
- Cite specific evidence for each conclusion
- Confidence below 0.5 means insufficient evidence
- Never recommend destructive actions without explicit approval
"""


class LLMClient:
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514") -> None:
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
        self.model = model

    async def analyze_incident(
        self,
        alert_name: str,
        namespace: str,
        evidence: dict[str, str],
    ) -> dict[str, Any]:
        evidence_text = "\n".join(f"## {k}\n{v}" for k, v in evidence.items())

        user_message = f"""Incident: {alert_name}
Namespace: {namespace}

Evidence:
{evidence_text}

Analyze this incident and provide root cause, confidence, evidence citations, and recommended actions."""

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_message}],
            )

            text = response.content[0].text
            return json.loads(text)

        except json.JSONDecodeError:
            logger.warning("LLM returned invalid JSON")
            return {"error": "invalid_json", "raw": text}

        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return {"error": str(e)}
