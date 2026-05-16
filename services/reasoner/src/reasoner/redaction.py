import re

# Patterns to redact
PATTERNS = [
    # Anthropic API keys
    (re.compile(r"sk-ant-[a-zA-Z0-9\-_]{10,}"), "[REDACTED_API_KEY]"),
    # Bearer tokens
    (re.compile(r"Bearer\s+[a-zA-Z0-9\-_.]{20,}"), "Bearer [REDACTED_TOKEN]"),
    # AWS Access Keys
    (re.compile(r"AKIA[0-9A-Z]{16}"), "[REDACTED_AWS_KEY]"),
    # Generic passwords in key=value
    (re.compile(r"(?i)password\s*[=:]\s*\S+"), "password=[REDACTED]"),
    # Generic secrets in key=value
    (re.compile(r"(?i)secret\s*[=:]\s*\S+"), "secret=[REDACTED]"),
    # Generic tokens in key=value
    (re.compile(r"(?i)token\s*[=:]\s*\S+"), "token=[REDACTED]"),
    # Private keys
    (
        re.compile(
            r"-----BEGIN[A-Z ]*PRIVATE KEY-----[\s\S]*?-----END[A-Z ]*PRIVATE KEY-----"
        ),
        "[REDACTED_PRIVATE_KEY]",
    ),
]


def redact_sensitive(text: str) -> str:
    """Redact sensitive data from text."""
    for pattern, replacement in PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def redact_sensitive_dict(evidence: dict[str, str]) -> dict[str, str]:
    """Redact sensitive data from all values in a dictionary."""
    return {key: redact_sensitive(value) for key, value in evidence.items()}
