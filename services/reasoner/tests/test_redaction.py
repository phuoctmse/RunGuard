import pytest

from reasoner.redaction import redact_sensitive, redact_sensitive_dict


def test_redact_api_key():
    text = "Using API key sk-ant-1234567890abcdef for auth"
    result = redact_sensitive(text)
    assert "sk-ant-" not in result
    assert "[REDACTED_API_KEY]" in result


def test_redact_bearer_token():
    text = "Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.payload.signature"
    result = redact_sensitive(text)
    assert "eyJ" not in result


def test_redact_password():
    text = "password=mysecretpass123"
    result = redact_sensitive(text)
    assert "mysecretpass123" not in result


def test_redact_aws_key():
    text = "AKIAIOSFODNN7EXAMPLE is the access key"
    result = redact_sensitive(text)
    assert "AKIAIOSFODNN7" not in result


def test_no_redaction_needed():
    text = "Normal log output with no secrets"
    result = redact_sensitive(text)
    assert result == text


def test_redact_in_dict():
    evidence = {"logs": "API key sk-ant-1234567890abcdef found"}
    result = redact_sensitive_dict(evidence)
    assert "sk-ant-" not in result["logs"]