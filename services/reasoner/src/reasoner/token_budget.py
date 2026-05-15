import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Pricing per 1M tokens (Claude Sonnet)
INPUT_COST_PER_1M = 3.0
OUTPUT_COST_PER_1M = 15.0

@dataclass
class UsageRecord:
    input_tokens: int = 0
    output_tokens: int = 0

class TokenBudget:
    def __init__(self, max_input: int = 10000, max_output: int = 2000):
        self.max_input = max_input
        self.max_output = max_output
        self._usage: dict[str, UsageRecord] = {}

    def truncate_input(self, text: str) -> str:
        """Truncate input text to fit within token budget."""
        # Rough estimate: 1 token ≈ 4 characters
        max_chars = self.max_input * 4
        if len(text) <= max_chars:
            return text

        logger.warning(
            f"Input truncated from {len(text)} to {max_chars} chars "
            f"(~{self.max_input} tokens)"
        )
        return text[:max_chars]

    def record_usage(
        self, incident_id: str, input_tokens: int, output_tokens: int
    ) -> None:
        """Record token usage for an incident."""
        if incident_id not in self._usage:
            self._usage[incident_id] = UsageRecord()

        record = self._usage[incident_id]
        record.input_tokens += input_tokens
        record.output_tokens += output_tokens

        logger.info(
            f"Token usage for {incident_id}: "
            f"input={input_tokens}, output={output_tokens}"
        )

    def get_usage(self, incident_id: str) -> dict[str, int]:
        """Get token usage for an incident."""
        record = self._usage.get(incident_id, UsageRecord())
        return {
            "input_tokens": record.input_tokens,
            "output_tokens": record.output_tokens,
        }

    def get_total_cost(self, incident_id: str) -> float:
        """Calculate total cost in USD for an incident."""
        usage = self.get_usage(incident_id)
        input_cost = (usage["input_tokens"] / 1_000_000) * INPUT_COST_PER_1M
        output_cost = (usage["output_tokens"] / 1_000_000) * OUTPUT_COST_PER_1M
        return input_cost + output_cost