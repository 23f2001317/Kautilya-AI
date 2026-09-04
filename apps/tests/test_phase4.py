# apps/tests/test_phase4.py
"""Test verification for Phase 4: Human-in-the-Loop Governance & UI Integration."""

from fastapi.testclient import TestClient
from src.api.incidents import _INCIDENT_STORE, Incident
from src.main import app

client = TestClient(app)


def _reset_test_incident() -> None:
    _INCIDENT_STORE["inc-test-01"] = Incident(
        id="inc-test-01",
        service_name="auth-service",
        title="High Latency Alert",
        severity="critical",
        status="patch_ready",
        hypothesis="DB connection pool saturation",
        confidence_score=0.95,
        candidate_patch="--- a/pool.py\n+++ b/pool.py\n@@ -1 +1 @@\n-max=2\n+max=50\n",
        verification_status="passed",
        test_summary={"passed": 24, "failed": 0},
        impacted_services=["payment-api"],
    )


def test_list_incidents() -> None:
    _reset_test_incident()
    response = client.get("/incidents")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any(inc["id"] == "inc-test-01" for inc in data)


def test_get_incident_detail() -> None:
    _reset_test_incident()
    response = client.get("/incidents/inc-test-01")
    assert response.status_code == 200
    data = response.json()
    assert data["service_name"] == "auth-service"
    assert "max=50" in data["candidate_patch"]
    assert data["confidence_score"] == 0.95


def test_approve_incident_generates_pr_and_resolves() -> None:
    _reset_test_incident()
    payload = {
        "signer_id": "sre-lead@kautilya.ai",
        "signature": "sha256-cryptographic-sig-val",
        "comments": "Verified patch and verified test report. Approved.",
    }
    response = client.post("/incidents/inc-test-01/approve", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "resolved"
    assert data["pr_url"] is not None
    assert "pull" in data["pr_url"]
    assert data["resolved_at"] is not None


def test_reject_incident() -> None:
    _reset_test_incident()
    payload = {
        "signer_id": "sre-dev@kautilya.ai",
        "reason": "Patch needs larger backoff parameter.",
    }
    response = client.post("/incidents/inc-test-01/reject", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "rejected"


def test_slack_interactive_approval_callback() -> None:
    _reset_test_incident()
    payload = {
        "incident_id": "inc-test-01",
        "user_id": "U123456",
        "action": "approve",
        "notes": "Approved from Slack channel #sre-alerts",
    }
    response = client.post("/api/integrations/slack/actions", json=payload)
    assert response.status_code == 200
    res_data = response.json()
    assert "white_check_mark" in res_data["text"]
    assert "Pull Request created" in res_data["text"]

    # Verify incident state is now resolved
    inc_res = client.get("/incidents/inc-test-01")
    assert inc_res.json()["status"] == "resolved"
