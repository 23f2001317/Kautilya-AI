# packages/security/src/scrubber.py
"""Sensitive data, credential, and PII redaction engine for telemetry and logs."""

import re
from typing import Any
import structlog

logger = structlog.get_logger(__name__)

# Precompiled regex patterns for sensitive tokens, credentials, and secrets
REDACTION_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("BEARER_TOKEN", re.compile(r"(?i)\b(Bearer\s+)[A-Za-z0-9\-_\.=]+")),
    ("BASIC_AUTH", re.compile(r"(?i)\b(Basic\s+)[A-Za-z0-9+/=]+")),
    ("AWS_KEY", re.compile(r"\b(AKIA|ABIA|ACCA|ASIA)[0-9A-Z]{16}\b")),
    ("AWS_SECRET", re.compile(r"(?i)(aws_secret_access_key|secret_key)\s*[:=]\s*['\"]?([A-Za-z0-9/+=]{40})['\"]?")),
    ("JWT_TOKEN", re.compile(r"\beyJ[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*\b")),
    ("DB_CONN_STR", re.compile(r"(?i)(postgres|postgresql|mysql|bolt|mongodb)://[^:]+:([^@]+)@")),
    ("PASSWORD_FIELD", re.compile(r"(?i)(\"?(password|secret|api_key|token)\"?\s*:\s*\"?)([^\",\s]+)(\"?)")),
]


class LogScrubber:
    """Detects and redacts sensitive credentials from strings, dictionaries, and log messages."""

    REDACTED_MASK: str = "[REDACTED]"

    @classmethod
    def scrub_text(cls, text: str) -> str:
        """Replace all matched sensitive substrings in text with redaction masks."""
        if not text:
            return ""

        scrubbed = text
        for name, pattern in REDACTION_PATTERNS:
            if name in ("BEARER_TOKEN", "BASIC_AUTH"):
                scrubbed = pattern.sub(rf"\1{cls.REDACTED_MASK}", scrubbed)
            elif name == "DB_CONN_STR":
                scrubbed = pattern.sub(rf"\1://[USER]:{cls.REDACTED_MASK}@", scrubbed)
            elif name == "PASSWORD_FIELD":
                scrubbed = pattern.sub(rf"\1{cls.REDACTED_MASK}\4", scrubbed)
            elif name == "AWS_SECRET":
                scrubbed = pattern.sub(rf"\1: '{cls.REDACTED_MASK}'", scrubbed)
            else:
                scrubbed = pattern.sub(cls.REDACTED_MASK, scrubbed)

        return scrubbed

    @classmethod
    def scrub_dict(cls, data: dict[str, Any]) -> dict[str, Any]:
        """Recursively redact dictionary keys and string values."""
        clean: dict[str, Any] = {}
        for k, v in data.items():
            if any(term in k.lower() for term in ("password", "secret", "token", "authorization", "api_key")):
                clean[k] = cls.REDACTED_MASK
            elif isinstance(v, str):
                clean[k] = cls.scrub_text(v)
            elif isinstance(v, dict):
                clean[k] = cls.scrub_dict(v)
            elif isinstance(v, list):
                clean[k] = [
                    cls.scrub_dict(item) if isinstance(item, dict)
                    else cls.scrub_text(item) if isinstance(item, str)
                    else item
                    for item in v
                ]
            else:
                clean[k] = v
        return clean
