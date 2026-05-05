"""Lambda handler — entry point for AWS Lambda execution."""

import json

from runguard.aws.eventbridge import EventBridgeIntake


def handler(event, context):
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
