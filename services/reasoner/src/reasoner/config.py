from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Reasoner service configuration from environment variables."""

    port: int = 8082
    nats_url: str = "nats://localhost:4222"
    anthropic_api_key: str = ""
    llm_model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 2048

    model_config = {"env_prefix": "REASONER_"}


def load_settings() -> Settings:
    return Settings()