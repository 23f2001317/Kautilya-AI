# apps/tests/test_end_to_end_flow.py
"""Comprehensive end-to-end integration test across all 5 architectural planes:
Plane 1: Ingestion & Webhooks
Plane 2: Knowledge Graph & Memory
Plane 3: Agentic Reasoning (LangGraph)
Plane 4: Ephemeral Sandboxing
Plane 5: Customer Relay Proxy & HITL Governance (WORM Audit)
"""

import pytest
from fastapi.testclient import TestClient
from apps.relay.src.relay_agent import CustomerRelayProxy
from apps.src.api.incidents import _INCIDENT_STORE
from apps.src.api.tasks import _COMPLETED_TASKS, _PENDING_TASKS
from apps.src.core.orchestrator import audit_ledger, orchestrator
from apps.src.main import app

client = TestClient(app)


@pytest.mark.asyncio
async def test_complete_five_plane_remediation_lifecycle() -> None:
    # -------------------------------------------------------------
    # PLANE 1: Ingest telemetry alert via Webhook
    # -------------------------------------------------------------
    from uuid import uuid4
    unique_suffix = uuid4().hex[:6]
    alert_payload = {
        "id": f"e2e-alert-auth-{unique_suffix}",
        "event_title": "High Latency & DB Pool Starvation on auth-service",
        "body": f"504 Gateway Timeouts detected. DB pool saturation > 98% [{unique_suffix}].",
        "priority": "high",
        "alert_type": "error",
        "service": "auth-service",
        "tags": ["env:production", "tier:backend"],
    }
    headers = {"Idempotency-Key": f"e2e-idemp-{unique_suffix}"}

    ingest_res = client.post("/webhooks/datadog", json=alert_payload, headers=headers)
    assert ingest_res.status_code == 202
    ingest_data = ingest_res.json()
    assert ingest_data["status"] == "received"
    canonical_id = ingest_data["canonical_alert_id"]

    # -------------------------------------------------------------
    # PLANE 2, 3, 4: Execute Autonomous Reasoning & Sandboxing Pipeline
    # -------------------------------------------------------------
    canonical_alert_dict = {
        "id": "e2e-incident-999",
        "source": "datadog",
        "external_id": "c0ffee123",
        "service_name": "auth-service",
        "title": alert_payload["event_title"],
        "severity": "critical",
        "description": alert_payload["body"],
        "raw_payload": alert_payload,
    }

    # Execute orchestrator pipeline
    incident = await orchestrator.process_alert(canonical_alert_dict)

    assert incident.id == "e2e-incident-999"
    assert incident.status == "patch_ready"
    assert incident.confidence_score >= 0.90
    assert "max_connections: int = 50" in incident.candidate_patch
    assert incident.verification_status == "passed"
    assert incident.test_summary.get("passed", 0) >= 1
    assert "payment-api" in incident.impacted_services

    # Verify incident is visible in API
    fetch_res = client.get(f"/incidents/{incident.id}")
    assert fetch_res.status_code == 200
    assert fetch_res.json()["status"] == "patch_ready"

    # -------------------------------------------------------------
    # PLANE 5 (Part A): Customer Relay Proxy Egress-Only Polling
    # -------------------------------------------------------------
    relay_proxy = CustomerRelayProxy(control_plane_url="", agent_id="customer-vpc-relay-test")

    # Poll task from control plane
    polled_task = await relay_proxy.poll_remote_task(client)
    assert polled_task is not None
    assert polled_task.task_type == "sandbox_verification"

    # Execute task inside Customer VPC boundary and sign result
    local_result = await relay_proxy.process_task(polled_task)
    assert local_result.status == "completed"
    assert len(local_result.signature) == 64  # Cryptographic SHA-256 signature

    # Submit signed result back to control plane
    submission_ok = await relay_proxy.submit_remote_result(local_result, client)
    assert submission_ok is True

    # -------------------------------------------------------------
    # PLANE 5 (Part B): Human-in-the-Loop Governance & PR Creation
    # -------------------------------------------------------------
    approval_payload = {
        "signer_id": "sre-lead@kautilya.ai",
        "signature": "sha256-verified-cryptographic-sig",
        "comments": "Verified patch and test report. Approved for production deployment.",
    }
    approve_res = client.post(f"/incidents/{incident.id}/approve", json=approval_payload)
    assert approve_res.status_code == 200
    resolved_incident = approve_res.json()
    assert resolved_incident["status"] == "resolved"
    assert resolved_incident["pr_url"] is not None
    assert "pull" in resolved_incident["pr_url"]
    assert resolved_incident["resolved_at"] is not None

    # -------------------------------------------------------------
    # WORM Cryptographic Audit Verification
    # -------------------------------------------------------------
    is_valid, status_msg = audit_ledger.verify_integrity()
    assert is_valid is True
    assert "cryptographically valid" in status_msg
