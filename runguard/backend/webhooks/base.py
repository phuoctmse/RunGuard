from abc import ABC, abstractmethod
from typing import Any


class BaseWebhookParser(ABC):
    @abstractmethod
    def parse(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        """Parse webhook payload into list of incident-ready dicts.

        Each dict contains: source, severity, namespace, workload, raw_alert.
        Returns empty list if no actionable alerts.
        """
