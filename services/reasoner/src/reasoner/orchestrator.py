import asyncio
import logging
from dataclasses import dataclass

from reasoner.llm import LLMClient
from reasoner.redaction import redact_sensitive_dict
from reasoner.token_budget import TokenBudget
from reasoner.cache import PromptCache

logger = logging.getLogger(__name__)

ANALYSIS_TIMEOUT_SECONDS = 30


@dataclass
class AnalysisResult:
    root_cause: str
    confidence: float
    evidence_citations: list[str]
    actions: list[str]
    unmatched_runbook: bool = False
    source: str = "llm"
    partial: bool = False


class ReasonerOrchestrator:
    def __init__(
        self,
        llm: LLMClient,
        runbooks: list[dict] | None = None,
        budget: TokenBudget | None = None,
        cache: PromptCache | None = None,
    ):
        self.llm = llm
        self.runbooks = runbooks or []
        self.budget = budget or TokenBudget()
        self.cache = cache or PromptCache()

    async def analyze(
        self,
        alert_name: str,
        namespace: str,
        evidence: dict[str, str],
    ) -> AnalysisResult:
        # Check if runbook matches
        matched = self._match_runbook(alert_name)

        # Redact sensitive data from evidence
        redacted_evidence = redact_sensitive_dict(evidence)

        # Check cache
        cached = self.cache.get(alert_name, redacted_evidence)
        if cached:
            logger.info(f"Cache hit for {alert_name}")
            return AnalysisResult(**cached)

        # Truncate evidence to fit token budget
        truncated = {}
        for key, value in redacted_evidence.items():
            truncated[key] = self.budget.truncate_input(value)

        # Call LLM with timeout
        try:
            result = await asyncio.wait_for(
                self.llm.analyze_incident(
                    alert_name=alert_name,
                    namespace=namespace,
                    evidence=truncated,
                ),
                timeout=ANALYSIS_TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError:
            logger.warning(f"LLM analysis timed out after {ANALYSIS_TIMEOUT_SECONDS}s")
            return AnalysisResult(
                root_cause="timeout",
                confidence=0.0,
                evidence_citations=[],
                actions=[],
                partial=True,
                source="timeout",
            )

        if "error" in result:
            logger.error(f"LLM analysis failed: {result['error']}")
            return AnalysisResult(
                root_cause="error",
                confidence=0.0,
                evidence_citations=[],
                actions=[],
                source=result.get("source", "error"),
            )

        analysis = AnalysisResult(
            root_cause=result.get("root_cause", "unknown"),
            confidence=result.get("confidence", 0.0),
            evidence_citations=result.get("evidence_citations", []),
            actions=result.get("actions", []),
            unmatched_runbook=matched is None,
            source="llm",
        )

        # Cache the result
        self.cache.set(alert_name, redacted_evidence, analysis.__dict__)

        return analysis

    def _match_runbook(self, alert_name: str) -> dict | None:
        for rb in self.runbooks:
            if rb.get("alertName") == alert_name:
                return rb
        return None
