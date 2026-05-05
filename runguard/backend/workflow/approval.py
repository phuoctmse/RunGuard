"""Human approval workflow."""

import time
import uuid


class ApprovalWorkflow:
    """Manages approval requests for medium/high-risk actions."""

    def __init__(self, expiry_seconds: int = 1800):
        self.expiry_seconds = expiry_seconds
        self._requests: dict = {}

    def create_request(
        self, incident_id: str, action_name: str, approver: str, reason: str
    ) -> str:
        request_id = f"apr-{uuid.uuid4().hex[:8]}"
        self._requests[request_id] = {
            "id": request_id,
            "incident_id": incident_id,
            "action_name": action_name,
            "approver": approver,
            "reason": reason,
            "status": "pending",
            "created_at": time.time(),
            "approved_by": None,
            "rejected_by": None,
            "rejection_reason": None,
        }
        return request_id

    def approve(self, request_id: str, approver: str) -> bool:
        if request_id not in self._requests:
            return False
        req = self._requests[request_id]
        if req["status"] != "pending":
            return False
        if self._is_expired(req):
            req["status"] = "expired"
            return False
        req["status"] = "approved"
        req["approved_by"] = approver
        return True

    def reject(self, request_id: str, rejector: str, reason: str = "") -> bool:
        if request_id not in self._requests:
            return False
        req = self._requests[request_id]
        if req["status"] != "pending":
            return False
        req["status"] = "rejected"
        req["rejected_by"] = rejector
        req["rejection_reason"] = reason
        return True

    def get_status(self, request_id: str) -> dict:
        if request_id not in self._requests:
            return {"status": "not_found"}
        req = self._requests[request_id]
        if req["status"] == "pending" and self._is_expired(req):
            req["status"] = "expired"
        return req

    def _is_expired(self, req: dict) -> bool:
        return (time.time() - req["created_at"]) > self.expiry_seconds
