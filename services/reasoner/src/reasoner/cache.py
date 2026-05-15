import logging
import json
import time
import hashlib
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class CacheEntry:
    value: str
    created_at: float

class PromptCache:
    def __init__(self, ttl_seconds: int = 3600):
        self.ttl_seconds = ttl_seconds
        self._cache: dict[str, CacheEntry] = {}

    def _make_key(self, alert_type: str, evidence: dict) -> str:
        evidence_str = json.dumps(evidence, sort_keys=True)
        raw = f"{alert_type}:{evidence_str}"
        return hashlib.sha256(raw.encode()).hexdigest()

    def get(self, alert_type: str, evidence: dict) -> str | None:
        key = self._make_key(alert_type, evidence)
        entry = self._cache.get(key)

        if entry is None:
            return None

        if time.time() - entry.created_at > self.ttl_seconds:
            del self._cache[key]
            logger.debug(f"Cache expired for {alert_type}")
            return None

        logger.debug(f"Cache hit for {alert_type}")
        return entry.value

    def set(self, alert_type: str, evidence: dict, value: str) -> None:
        key = self._make_key(alert_type, evidence)
        self._cache[key] = CacheEntry(value=value, created_at=time.time())
        logger.debug(f"Cache set for {alert_type}")

    def clear(self) -> None:
        self._cache.clear()  