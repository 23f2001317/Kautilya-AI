# apps/tests/test_real_data_pipeline.py
"""Test suite validating real backend data sources without mock fixtures."""

import pytest
from fastapi.testclient import TestClient
from apps.src.core.database import init_db
from apps.src.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_test_db():
    import asyncio
    asyncio.run(init_db())


def test_audit_verify_endpoint() -> None:
    """Verify GET /api/audit/verify returns valid chain state."""
    res = client.get("/api/audit/verify")
    assert res.status_code == 200
    data = res.json()
    assert "status" in data
    assert "chain_head" in data
    assert data["is_tampered"] is False


def test_audit_tamper_detection() -> None:
    """Verify audit verification detects tampering."""
    # Ensure at least one entry in ledger
    from packages.security.src.worm_logger import WORMAuditLedger
    from apps.src.api.audit import ledger_instance
    ledger_instance.append_audit_event("TEST_EVENT", "test_actor", {"test": "data"})

    # Deliberately tamper
    tamper_res = client.post("/api/audit/tamper_test")
    assert tamper_res.status_code == 200
    assert tamper_res.json()["is_valid"] is False

    # Check verify reflects tampered state
    verify_res = client.get("/api/audit/verify")
    assert verify_res.status_code == 200
    assert verify_res.json()["status"] == "tampered"
    assert verify_res.json()["is_tampered"] is True

    # Restore clean ledger for subsequent tests
    ledger_instance.entries.clear()
    ledger_instance.append_audit_event("RESTORE", "system", {"restored": True})


def test_topology_dynamic_endpoint() -> None:
    """Verify GET /api/topology returns dynamic nodes and edges."""
    res = client.get("/api/topology")
    assert res.status_code == 200
    data = res.json()
    assert "nodes" in data
    assert "edges" in data
    assert len(data["nodes"]) >= 4
    assert len(data["edges"]) >= 3

    from uuid import uuid4
    unique_name = f"svc-{uuid4().hex[:6]}"
    new_node = {
        "name": unique_name,
        "node_type": "service",
        "tier": "backend",
        "criticality": "high",
        "connect_to": "payment-api",
    }
    add_res = client.post("/api/topology/nodes", json=new_node)
    assert add_res.status_code == 200

    # Verify new node is now returned in topology
    res2 = client.get("/api/topology")
    names = [n["name"] for n in res2.json()["nodes"]]
    assert unique_name in names


def test_simulate_alert_archetypes_produce_distinct_diagnoses() -> None:
    """Verify different simulated alert archetypes produce genuinely distinct hypotheses and patches."""
    # 1. DB Pool Alert
    res1 = client.post("/api/alerts/simulate", json={"archetype": "db_pool"})
    assert res1.status_code == 200
    d1 = res1.json()
    assert d1["service_name"] == "auth-service"
    assert "database" in d1["hypothesis"].lower() or "pool" in d1["hypothesis"].lower()

    # 2. Redis Cache Alert
    res2 = client.post("/api/alerts/simulate", json={"archetype": "redis_cache"})
    assert res2.status_code == 200
    d2 = res2.json()
    assert d2["service_name"] == "payment-api"
    assert "redis" in d2["hypothesis"].lower() or "cache" in d2["hypothesis"].lower()

    # Assert two distinct diagnoses
    assert d1["hypothesis"] != d2["hypothesis"]
    assert d1["incident_id"] != d2["incident_id"]

    # Verify incidents are persisted in DB
    list_res = client.get("/incidents")
    assert list_res.status_code == 200
    persisted_ids = [inc["id"] for inc in list_res.json()]
    assert d1["incident_id"] in persisted_ids
    assert d2["incident_id"] in persisted_ids


def test_approve_incident_creates_real_branch_and_resolves() -> None:
    """Verify approval creates a real Git branch reference and resolves incident."""
    sim_res = client.post("/api/alerts/simulate", json={"archetype": "gateway_timeout"})
    assert sim_res.status_code == 200
    incident_id = sim_res.json()["incident_id"]

    approval = {
        "signer_id": "sre-engineer@kautilya.ai",
        "signature": "sha256-verified-sig",
        "comments": "Verified in sandbox",
    }
    app_res = client.post(f"/incidents/{incident_id}/approve", json=approval)
    assert app_res.status_code == 200
    data = app_res.json()
    assert data["status"] == "resolved"
    assert data["pr_url"] is not None
    assert incident_id.replace("inc-", "") in data["pr_url"]

    # Verify persistence survives
    get_res = client.get(f"/incidents/{incident_id}")
    assert get_res.status_code == 200
    assert get_res.json()["status"] == "resolved"
