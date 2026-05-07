"""Tests for configuration management."""


def test_settings_defaults():
    """Settings should have correct default values."""
    from runguard.backend.config import Settings

    s = Settings()
    assert s.runguard_env == "local"
    assert s.log_level == "INFO"
    assert s.api_url == "http://localhost:8000"
    assert s.api_key == ""
    assert s.webhook_secret == ""
    assert s.anthropic_api_key == ""
    assert s.claude_model == "claude-sonnet-4-20250514"
    assert s.k8s_namespace == "runguard"
    assert s.audit_store_path == "./data/audit"
    assert s.llm_max_input_tokens == 10000
    assert s.llm_max_output_tokens == 2000
    assert s.slack_webhook_url == ""


def test_settings_from_env_vars(monkeypatch):
    """Settings should load from environment variables with RUNGUARD_ prefix."""
    from runguard.backend.config import Settings

    # pydantic-settings with env_prefix="RUNGUARD_" means:
    # field "runguard_env" -> env var "RUNGUARD_RUNGUARD_ENV" (double prefix)
    # field "log_level" -> env var "RUNGUARD_LOG_LEVEL"
    monkeypatch.setenv("RUNGUARD_LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("RUNGUARD_K8S_NAMESPACE", "prod-ns")
    monkeypatch.setenv("RUNGUARD_LLM_MAX_INPUT_TOKENS", "20000")

    s = Settings()
    assert s.log_level == "DEBUG"
    assert s.k8s_namespace == "prod-ns"
    assert s.llm_max_input_tokens == 20000


def test_settings_model_config():
    """Settings model_config should use RUNGUARD_ prefix."""
    from runguard.backend.config import Settings

    assert Settings.model_config["env_prefix"] == "RUNGUARD_"


def test_settings_claude_model_from_env(monkeypatch):
    """Settings should load claude_model from env var."""
    from runguard.backend.config import Settings

    monkeypatch.setenv("RUNGUARD_CLAUDE_MODEL", "claude-opus-4-20250514")
    s = Settings()
    assert s.claude_model == "claude-opus-4-20250514"


def test_settings_slack_webhook_from_env(monkeypatch):
    """Settings should load slack_webhook_url from env var."""
    from runguard.backend.config import Settings

    monkeypatch.setenv("RUNGUARD_SLACK_WEBHOOK_URL", "https://hooks.slack.com/test")
    s = Settings()
    assert s.slack_webhook_url == "https://hooks.slack.com/test"


def test_settings_webhook_secret_from_env(monkeypatch):
    """Settings should load webhook_secret from env var."""
    from runguard.backend.config import Settings

    monkeypatch.setenv("RUNGUARD_WEBHOOK_SECRET", "my-bearer-token")
    s = Settings()
    assert s.webhook_secret == "my-bearer-token"
