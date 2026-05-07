from abc import ABC, abstractmethod


class NotificationSender(ABC):
    @abstractmethod
    async def send_incident_created(self, incident_id: str, workload: str, severity: str) -> None: ...

    @abstractmethod
    async def send_approval_required(self, incident_id: str, action: str) -> None: ...

    @abstractmethod
    async def send_action_executed(self, incident_id: str, action: str) -> None: ...

    @abstractmethod
    async def send_action_failed(self, incident_id: str, action: str, error: str) -> None: ...

    @abstractmethod
    async def send_resolved(self, incident_id: str, summary: str) -> None: ...
