# packages/security/src/worm_logger.py
"""WORM (Write Once, Read Many) tamper-evident cryptographic audit ledger."""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any
from pydantic import BaseModel, Field
import structlog

logger = structlog.get_logger(__name__)


class AuditEntry(BaseModel):
    """Immutable audit log record locked in cryptographic hash chain."""

    entry_id: int
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    event_name: str
    actor: str
    payload: dict[str, Any]
    previous_hash: str
    entry_hash: str


class WORMAuditLedger:
    """Tamper-evident audit engine satisfying SOC2 WORM compliance specifications."""

    GENESIS_HASH: str = "0000000000000000000000000000000000000000000000000000000000000000"

    def __init__(self, persistence_path: Path | str | None = None) -> None:
        self.persistence_path = Path(persistence_path) if persistence_path else None
        self.entries: list[AuditEntry] = []
        self._load_ledger()

    def _load_ledger(self) -> None:
        """Load persisted audit chain if present on disk."""
        if self.persistence_path and self.persistence_path.exists():
            lines = self.persistence_path.read_text(encoding="utf-8").splitlines()
            for line in lines:
                if line.strip():
                    self.entries.append(AuditEntry.model_validate_json(line))

    @staticmethod
    def _compute_hash(
        entry_id: int, timestamp: str, event_name: str, actor: str, payload: dict[str, Any], previous_hash: str
    ) -> str:
        """Calculate SHA-256 cryptographic digest of entry data bound to previous block hash."""
        canonical_str = (
            f"{entry_id}|{timestamp}|{event_name}|{actor}|"
            f"{json.dumps(payload, sort_keys=True)}|{previous_hash}"
        )
        return hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()

    def append_audit_event(self, event_name: str, actor: str, payload: dict[str, Any]) -> AuditEntry:
        """Append an unalterable audit log entry chained to the preceding entry hash."""
        entry_id = len(self.entries)
        previous_hash = self.entries[-1].entry_hash if self.entries else self.GENESIS_HASH
        timestamp = datetime.now(timezone.utc).isoformat()

        entry_hash = self._compute_hash(
            entry_id, timestamp, event_name, actor, payload, previous_hash
        )

        entry = AuditEntry(
            entry_id=entry_id,
            timestamp=timestamp,
            event_name=event_name,
            actor=actor,
            payload=payload,
            previous_hash=previous_hash,
            entry_hash=entry_hash,
        )

        self.entries.append(entry)

        # Write to append-only WORM persistence target if configured
        if self.persistence_path:
            with open(self.persistence_path, "a", encoding="utf-8") as f:
                f.write(entry.model_dump_json() + "\n")

        logger.info(
            "worm_audit_event_logged",
            entry_id=entry_id,
            event_type=event_name,
            hash=entry_hash[:16],
        )
        return entry

    def verify_integrity(self) -> tuple[bool, str]:
        """Verify unbroken cryptographic consistency across the entire audit ledger.

        Returns:
            Tuple of (is_valid: bool, status_message: str).
        """
        if not self.entries:
            return True, "Ledger is empty (valid)."

        expected_prev = self.GENESIS_HASH
        for idx, entry in enumerate(self.entries):
            if entry.previous_hash != expected_prev:
                return (
                    False,
                    f"Tamper detected at entry {idx}: previous_hash mismatch! "
                    f"Expected {expected_prev}, got {entry.previous_hash}",
                )

            recomputed = self._compute_hash(
                entry.entry_id,
                entry.timestamp,
                entry.event_name,
                entry.actor,
                entry.payload,
                entry.previous_hash,
            )

            if entry.entry_hash != recomputed:
                return (
                    False,
                    f"Tamper detected at entry {idx}: payload or hash altered! "
                    f"Recorded {entry.entry_hash}, calculated {recomputed}",
                )

            expected_prev = entry.entry_hash

        return True, f"All {len(self.entries)} audit entries cryptographically valid."
