"""Configuration management for RunGuard."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    runguard_env: str = "local"
    log_level: str = "INFO"

    # API
    api_url: str = "http://localhost:8000"
    api_key: str = ""
    webhook_secret: str = ""

    # Claude API
    anthropic_api_key: str = ""
    anthropic_base_url: str = ""
    claude_model: str = "claude-sonnet-4-20250514"

    # Kubernetes
    kubeconfig: str = "~/.kube/config"
    k8s_namespace: str = "runguard"

    # Audit
    audit_store_path: str = "./data/audit"

    # LLM token budget
    llm_max_input_tokens: int = 10000
    llm_max_output_tokens: int = 8000

    # GitOps
    gitops_enabled: bool = False
    gitops_repo_path: str = ""

    # Cost tracking
    opencost_endpoint: str = ""

    # Notifications
    slack_webhook_url: str = ""

    model_config = {"env_prefix": "RUNGUARD_", "env_file": ".env"}


settings = Settings()
