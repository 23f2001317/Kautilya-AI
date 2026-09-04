# apps/tests/test_phase5.py
"""Test verification for Phase 5: Enterprise Hardening & Security Compliance."""

import pytest
from apps.relay.src.relay_agent import CustomerRelayProxy, RelayTask
from packages.security.src.kms import KMSEnvelopeEncryption
from packages.security.src.scrubber import LogScrubber
from packages.security.src.worm_logger import WORMAuditLedger


def test_log_scrubber_redacts_credentials_and_tokens() -> None:
    raw_log = (
        "Connecting to postgres://admin:supersecretpwd@db.internal:5432/main. "
        "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.e30.t-ID brackets. "
        "AWS Key: AKIAIOSFODNN7EXAMPLE."
    )
    scrubbed = LogScrubber.scrub_text(raw_log)

    assert "supersecretpwd" not in scrubbed
    assert "[REDACTED]" in scrubbed
    assert "AKIAIOSFODNN7EXAMPLE" not in scrubbed

    payload = {
        "user": "sre-agent",
        "api_key": "sk-proj-secret12345",
        "db_password": "pass-very-secret",
        "nested": {"token": "secret-token-val", "status": "active"},
    }
    clean_dict = LogScrubber.scrub_dict(payload)
    assert clean_dict["api_key"] == "[REDACTED]"
    assert clean_dict["db_password"] == "[REDACTED]"
    assert clean_dict["nested"]["token"] == "[REDACTED]"
    assert clean_dict["nested"]["status"] == "active"


def test_worm_audit_ledger_integrity_and_tamper_detection() -> None:
    ledger = WORMAuditLedger()

    # Append sequential audit events
    ledger.append_audit_event("INGEST", "system", {"alert_id": "a-1"})
    ledger.append_audit_event("TRIAGE", "agent", {"hypothesis": "db exhaustion"})
    ledger.append_audit_event("APPROVAL", "human:sre-lead", {"action": "approved"})

    # Verify unbroken valid chain
    is_valid, msg = ledger.verify_integrity()
    assert is_valid is True
    assert "cryptographically valid" in msg

    # Tamper simulation: Alter an earlier entry's payload
    ledger.entries[1].payload["hypothesis"] = "tampered malicious edit"
    tampered_valid, tamper_msg = ledger.verify_integrity()
    assert tampered_valid is False
    assert "Tamper detected" in tamper_msg


def test_kms_envelope_encryption_roundtrip() -> None:
    kms = KMSEnvelopeEncryption(master_key_arn="arn:aws:kms:us-east-1:112233445566:key/kautilya-sre")
    secret_text = "kautilya_db_super_secure_vault_token_#992!"

    bundle = kms.encrypt_secret(secret_text)
    assert "ciphertext" in bundle
    assert "encrypted_dek" in bundle
    assert bundle["ciphertext"] != secret_text

    decrypted = kms.decrypt_secret(bundle)
    assert decrypted == secret_text


@pytest.mark.asyncio
async def test_egress_only_customer_relay_polling() -> None:
    relay = CustomerRelayProxy(agent_id="test-relay-vpc")
    queue = [
        RelayTask(
            task_id="task-01",
            task_type="sandbox_verification",
            payload={"repo": "auth-service", "patch_id": "p-1"},
            assigned_at="2026-09-03T19:54:00Z",
        )
    ]

    results = await relay.run_poll_cycle(queue, max_iterations=1)
    assert len(results) == 1
    assert results[0].task_id == "task-01"
    assert results[0].status == "completed"
    assert results[0].output["sandbox_status"] == "passed"
    assert len(results[0].signature) == 64  # Valid SHA-256 signature
