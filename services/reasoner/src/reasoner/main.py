import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from reasoner.config import load_settings
from reasoner.llm import LLMClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = load_settings()
    app.state.settings = settings
    app.state.llm = LLMClient(
        api_key=settings.anthropic_api_key,
        model=settings.llm_model,
        max_tokens=settings.max_tokens,
    )
    logger.info("reasoner starting on port %d", settings.port)
    yield


app = FastAPI(title="RunGuard Reasoner", lifespan=lifespan)


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


@app.get("/readyz")
async def readyz():
    return {"status": "ready"}


@app.post("/analyze")
async def analyze(alert_name: str, namespace: str, evidence: dict):
    """Analyze an incident using LLM."""
    llm: LLMClient = app.state.llm
    result = await llm.analyze_incident(
        alert_name=alert_name,
        namespace=namespace,
        evidence=evidence,
    )
    return result


if __name__ == "__main__":
    import uvicorn

    settings = load_settings()
    uvicorn.run("reasoner.main:app", host="0.0.0.0", port=settings.port, reload=True)
