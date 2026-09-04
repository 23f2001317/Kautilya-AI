# apps/src/api/audit.py
"""Audit ledger verification and compliance endpoint."""

from typing import Any
from fastapi import APIRouter
import structlog

from packages.security.src.worm_logger import WORMAuditLedger

logger = structlog.get_logger(__name__)

router = APIRouter(tags=["Audit & Compliance"])

from ..core.orchestrator import audit_ledger as ledger_instance


@router.get("/audit/verify", response_model=dict[str, Any])
@router.get("/api/audit/verify", response_model=dict[str, Any])
async def verify_audit_ledger() -> dict[str, Any]:
    """Verify cryptographic SHA-256 hash chain of the WORM audit ledger.

    Returns:
        Status object containing valid/tampered state, total entries, and recent blocks.
    """
    is_valid, message = ledger_instance.verify_integrity()
    blocks = [
        {
            "entry_id": e.entry_id,
            "timestamp": e.timestamp,
            "event_name": e.event_name,
            "actor": e.actor,
            "hash": e.entry_hash[:16] + "...",
            "prev_hash": e.previous_hash[:16] + "...",
        }
        for e in ledger_instance.entries[-10:]
    ]
    chain_head = ledger_instance.entries[-1].entry_hash if ledger_instance.entries else "0" * 64

    return {
        "status": "valid" if is_valid else "tampered",
        "is_tampered": not is_valid,
        "message": message,
        "total_entries": len(ledger_instance.entries),
        "chain_head": chain_head,
        "recent_blocks": blocks,
    }


@router.post("/api/audit/tamper_test", response_model=dict[str, Any])
async def simulate_ledger_tampering() -> dict[str, Any]:
    """Deliberately corrupt an audit record in the ledger to test tamper detection."""
    if not ledger_instance.entries:
        ledger_instance.append_audit_event("INITIAL_AUDIT_SEED", "system", {"status": "seeded"})

    # Corrupt the payload of the first entry
    first_entry = ledger_instance.entries[0]
    first_entry.payload["tampered_key"] = "unauthorized_modification"
    logger.warning("deliberately_tampered_audit_ledger_for_testing", entry_id=first_entry.entry_id)

    is_valid, message = ledger_instance.verify_integrity()
    return {
        "status": "tampered",
        "is_valid": is_valid,
        "message": message,
    }
