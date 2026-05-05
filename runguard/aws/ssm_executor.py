"""SSM document executor — triggers AWS Systems Manager documents."""

import boto3


class SSMExecutor:
    """Executes SSM documents on target instances."""

    def __init__(self, region_name: str = "us-east-1"):
        self.ssm = boto3.client("ssm", region_name=region_name)

    def trigger_document(
        self,
        document_name: str,
        targets: list[str],
        parameters: dict | None = None,
    ) -> dict:
        try:
            response = self.ssm.send_command(
                DocumentName=document_name,
                Targets=[{"Key": "InstanceIds", "Values": targets}],
                Parameters=parameters or {},
            )
            return {
                "status": "success",
                "execution_id": response["Command"]["CommandId"],
                "document_name": document_name,
                "targets": targets,
            }
        except Exception as e:
            return {"status": "failed", "error": str(e)}

    def get_execution_status(self, execution_id: str) -> dict:
        try:
            response = self.ssm.list_commands(CommandId=execution_id)
            commands = response.get("Commands", [])
            if commands:
                return {
                    "status": commands[0]["Status"],
                    "execution_id": execution_id,
                }
            return {"status": "not_found", "execution_id": execution_id}
        except Exception as e:
            return {"status": "error", "error": str(e)}
