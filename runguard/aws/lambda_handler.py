"""Lambda handler — entry point for AWS Lambda execution."""

import json
from typing import Any

from runguard.aws.eventbridge import EventBridgeIntake


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """AWS Lambda handler for incident intake."""
    intake = EventBridgeIntake()
    incident_data = intake.parse_event(event)
    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "message": "Incident received",
                "incident": incident_data,
            }
        ),
    }
