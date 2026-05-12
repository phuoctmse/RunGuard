import json
import logging
from typing import Any

import anthropic

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an SRE incident analyzer. Given an alert and evidence,
identify the root cause and propose remediation actions.

Respond in JSON format:
{
  "root_cause": "brief description",
  "confidence": 0.0-1.0,
  "evidence_citations": ["key evidence points"],
  "actions": ["proposed remediation actions"]
}"""


class LLMClient:
    """Wrapper around Anthropic API for incident analysis."""

    def __init__(self, api_key: str, model: str, max_tokens: int = 2048) -> None:
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
        self.model = model
        self.max_tokens = max_tokens

    async def analyze_incident(
        self,
        alert_name: str,
        namespace: str,
        evidence: dict[str, Any],
    ) -> dict[str, Any]:
        """Analyze an incident using LLM and return structured result."""
        user_message = (
            f"Alert: {alert_name}\n"
            f"Namespace: {namespace}\n"
            f"Evidence:\n{json.dumps(evidence, indent=2)}"
        )

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_message}],
            )
            raw_text = response.content[0].text
            return json.loads(raw_text)
        except json.JSONDecodeError:
            logger.warning("LLM returned invalid JSON: %s", raw_text[:200])
            return {"error": "invalid_json", "raw": raw_text[:500]}
        except Exception:
            logger.exception("LLM call failed")
            return {"error": "llm_call_failed"}