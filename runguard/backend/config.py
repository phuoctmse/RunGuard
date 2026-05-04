"""Configuration management for RunGuard."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    runguard_env: str = "local"
    log_level: str = "INFO"

    # Claude API
    anthropic_api_key: str = ""

    # Kubernetes
    kubeconfig: str = "~/.kube/config"
    k8s_namespace: str = "runguard"

    # Audit
    audit_store_path: str = "./data/audit"

    # LLM token budget
    llm_max_input_tokens: int = 10000
    llm_max_output_tokens: int = 2000

    model_config = {"env_prefix": "RUNGUARD_", "env_file": ".env"}


settings = Settings()
