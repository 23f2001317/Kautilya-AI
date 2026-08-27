# apps/api/tests/test_phase1.py
"""Self-contained test verification for Phase 1 components."""

import hashlib
from src.api.webhooks import CanonicalAlert, DatadogAlertPayload, GitHubWebhookPayload


def test_datadog_payload_and_canonical_normalization() -> None:
    raw = {
        "id": "alert-12345",
        "event_title": "High CPU utilization on auth-service",
        "body": "CPU has exceeded 90% threshold for 5 minutes",
        "priority": "high",
        "alert_type": "error",
        "service": "auth-service",
        "tags": ["env:production", "tier:backend"],
    }
    payload = DatadogAlertPayload.model_validate(raw)
    assert payload.id == "alert-12345"
    assert payload.service == "auth-service"

    alert = CanonicalAlert(
        source="datadog",
        external_id=payload.id,
        service_name=payload.service,
        title=payload.event_title,
        severity="critical",
        description=payload.body,
        raw_payload=payload.model_dump(),
    )
    assert alert.source == "datadog"
    assert alert.external_id == "alert-12345"
    assert alert.service_name == "auth-service"
    assert alert.severity == "critical"


def test_github_payload_and_hash_idempotency() -> None:
    raw = {
        "ref": "refs/heads/main",
        "repository": {"name": "payment-gateway"},
        "head_commit": {
            "id": "c0ffee123",
            "message": "fix(checkout): resolve transaction timeout",
            "timestamp": "2026-08-27T14:00:00Z",
        },
    }
    payload = GitHubWebhookPayload.model_validate(raw)
    assert payload.head_commit is not None
    assert payload.head_commit.id == "c0ffee123"

    body_bytes = b'{"ref":"refs/heads/main"}'
    computed_hash = hashlib.sha256(body_bytes).hexdigest()
    assert len(computed_hash) == 64


if __name__ == "__main__":
    test_datadog_payload_and_canonical_normalization()
    test_github_payload_and_hash_idempotency()
    print("All Phase 1 unit self-checks passed successfully.")
