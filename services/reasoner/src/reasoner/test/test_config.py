from reasoner.config import load_settings


def test_default_settings():
    settings = load_settings()
    assert settings.port == 8082
    assert settings.nats_url == "nats://localhost:4222"


def test_override_port(monkeypatch):
    monkeypatch.setenv("REASONER_PORT", "9999")
    settings = load_settings()
    assert settings.port == 9999