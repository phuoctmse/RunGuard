from typing import Any


class Processor:
    """Handles async job processing for the reasoner service."""

    def process(self, job: dict[str, Any]) -> dict[str, str]:
        """Process a job and return the result."""
        job_type = job.get("type", "")
        payload = job.get("payload", {})

        if job_type == "collect_evidence":
            return {
                "status": "completed",
                "message": f"evidence collected for {payload.get('pod', 'unknown')}",
            }
        if job_type == "send_notification":
            return {"status": "completed", "message": "notification sent"}

        raise ValueError(f"unknown job type: {job_type!r}")
