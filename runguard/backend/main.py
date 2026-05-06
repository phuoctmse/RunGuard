"""RunGuard FastAPI application."""

from fastapi import FastAPI

from runguard.backend.api.audit import router as audit_router
from runguard.backend.api import workflow as workflow_module
from runguard.backend.api.incidents import router as incidents_router
from runguard.backend.api.runbooks import router as runbooks_router
from runguard.backend.api.workflow import router as workflow_router
from runguard.backend.workflow.approval import ApprovalWorkflow

app = FastAPI(
    title="RunGuard",
    description="AI-powered incident remediation platform",
    version="0.1.0",
)

app.include_router(incidents_router)
app.include_router(runbooks_router)
app.include_router(workflow_router)
app.include_router(audit_router)

workflow_module._workflow = ApprovalWorkflow()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
