"""RunGuard FastAPI application."""

from fastapi import FastAPI

from runguard.backend.api.incidents import router as incidents_router
from runguard.backend.api.runbooks import router as runbooks_router

app = FastAPI(
    title="RunGuard",
    description="AI-powered incident remediation platform",
    version="0.1.0",
)

app.include_router(incidents_router)
app.include_router(runbooks_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
