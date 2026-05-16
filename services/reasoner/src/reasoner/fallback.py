import logging
from typing import Any

from reasoner.llm import LLMClient

logger = logging.getLogger(__name__)


class FallbackClient:
    """Fallback chain: Claude API → Bedrock → raw evidence."""

    def __init__(
        self,
        primary_key: str,
        bedrock_key: str,
        primary_client: LLMClient | None = None,
    ):
        self.primary_client = primary_client
        self.primary_key = primary_key
        self.bedrock_key = bedrock_key

    async def analyze(
        self,
        alert_name: str,
        namespace: str,
        evidence: dict[str, str],
    ) -> dict[str, Any]:
        # Try primary Claude API
        if self.primary_client and self.primary_key:
            try:
                logger.info("Trying primary Claude API")
                result = await self.primary_client.analyze_incident(
                    alert_name=alert_name,
                    namespace=namespace,
                    evidence=evidence,
                )
                if "error" not in result:
                    result["source"] = "claude_api"
                    return result
                logger.warning(f"Primary API returned error: {result.get('error')}")
            except Exception as e:
                logger.warning(f"Primary API failed: {e}")

        # Try Bedrock (placeholder — requires AWS setup)
        if self.bedrock_key:
            try:
                logger.info("Trying Bedrock fallback")
                # TODO: Implement Bedrock client
                pass
            except Exception as e:
                logger.warning(f"Bedrock failed: {e}")

        # Fallback: return raw evidence without analysis
        logger.info("All LLM sources failed, returning raw evidence")
        return {
            "root_cause": "unknown",
            "confidence": 0.0,
            "evidence_citations": [],
            "actions": [],
            "evidence": evidence,
            "source": "raw_evidence",
        }
