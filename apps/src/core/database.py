# apps/src/core/database.py
"""Persistent SQLite storage for Incidents and Topology using SQLAlchemy 2.0 and aiosqlite."""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import structlog
from sqlalchemy import (
    DateTime,
    Float,
    String,
    Text,
    select,
)
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from apps.src.services.scanner_service import generate_topology_data

logger = structlog.get_logger(__name__)

# Database file location (defaults to repo root kautilya.db)
DB_PATH = os.getenv("KAUTILYA_DB_PATH", str(Path(__file__).resolve().parents[3] / "kautilya.db"))
DATABASE_URL = f"sqlite+aiosqlite:///{DB_PATH}"

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    global _engine, _session_factory
    if _engine is None:
        _engine = create_async_engine(DATABASE_URL, echo=False)
        _session_factory = async_sessionmaker(_engine, expire_on_commit=False, class_=AsyncSession)
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    get_engine()
    assert _session_factory is not None
    return _session_factory


class Base(DeclarativeBase):
    pass


class IncidentRecord(Base):
    __tablename__ = "incidents"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    service_name: Mapped[str] = mapped_column(String(128), index=True)
    title: Mapped[str] = mapped_column(String(256))
    severity: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(32), default="triaging")
    hypothesis: Mapped[str] = mapped_column(Text, default="")
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    candidate_patch: Mapped[str] = mapped_column(Text, default="")
    verification_status: Mapped[str] = mapped_column(String(32), default="pending")
    test_summary_json: Mapped[str] = mapped_column(Text, default="{}")
    impacted_services_json: Mapped[str] = mapped_column(Text, default="[]")
    pr_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    @property
    def test_summary(self) -> dict[str, Any]:
        try:
            return json.loads(self.test_summary_json)
        except Exception:
            return {}

    @property
    def impacted_services(self) -> list[str]:
        try:
            return json.loads(self.impacted_services_json)
        except Exception:
            return []


class TopologyNodeRecord(Base):
    __tablename__ = "topology_nodes"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True)
    node_type: Mapped[str] = mapped_column(String(32))  # service, database, cache, frontend
    tier: Mapped[str] = mapped_column(String(32), default="backend")
    criticality: Mapped[str] = mapped_column(String(32), default="medium")


class TopologyEdgeRecord(Base):
    __tablename__ = "topology_edges"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    source: Mapped[str] = mapped_column(String(128), index=True)
    target: Mapped[str] = mapped_column(String(128), index=True)
    relationship: Mapped[str] = mapped_column(String(64), default="CALLS")


async def init_db() -> None:
    """Initialize database tables and seed baseline topology if empty."""
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Seed baseline microservice topology if empty
    session_factory = get_session_factory()
    async with session_factory() as session:
        result = await session.execute(select(TopologyNodeRecord))
        nodes = result.scalars().all()
        if not nodes:
            repo_url = os.environ.get("TARGET_REPO_URL", "")
            repo_name = repo_url.split("/")[-1].replace(".git", "") if "/" in repo_url else "unknown-repo"
            
            default_nodes = [
                TopologyNodeRecord(
                    id=f"node-{repo_name.lower()}",
                    name=repo_name,
                    node_type="service",
                    tier="backend",
                    criticality="critical"
                )
            ]
            session.add_all(default_nodes)
            await session.commit()
            logger.info("seeded_dynamic_topology", nodes=len(default_nodes))


async def reset_database(repo_url: str) -> None:
    """Purge all data and seed a dynamic node for the given repo."""
    from sqlalchemy import delete
    
    session_factory = get_session_factory()
    async with session_factory() as session:
        # Purge all old data
        await session.execute(delete(IncidentRecord))
        await session.execute(delete(TopologyEdgeRecord))
        await session.execute(delete(TopologyNodeRecord))
        
        # Step 3: Run autonomous repository scanner to build perfect topology map
        logger.info("running_autonomous_topology_scanner", target=repo_url)
        nodes_data, edges_data = generate_topology_data(repo_url)
        
        db_nodes = [
            TopologyNodeRecord(
                id=n["id"],
                name=n["name"],
                node_type=n["node_type"],
                tier=n["tier"],
                criticality="critical"
            ) for n in nodes_data
        ]
        
        db_edges = [
            TopologyEdgeRecord(
                id=f"{e['source']}-{e['target']}",
                source=e["source"],
                target=e["target"],
                relationship=e["relationship"]
            ) for e in edges_data
        ]
        
        session.add_all(db_nodes)
        session.add_all(db_edges)
        
        await session.commit()
        logger.info("database_reset_complete", seeded_repo=repo_url)


# --- Data Access Helpers ---

async def db_list_incidents() -> list[IncidentRecord]:
    session_factory = get_session_factory()
    async with session_factory() as session:
        result = await session.execute(select(IncidentRecord).order_by(IncidentRecord.created_at.desc()))
        return list(result.scalars().all())


async def db_get_incident(incident_id: str) -> IncidentRecord | None:
    session_factory = get_session_factory()
    async with session_factory() as session:
        result = await session.execute(select(IncidentRecord).where(IncidentRecord.id == incident_id))
        return result.scalar_one_or_none()


async def db_save_incident(incident_data: dict[str, Any]) -> IncidentRecord:
    session_factory = get_session_factory()
    async with session_factory() as session:
        inc_id = incident_data["id"]
        result = await session.execute(select(IncidentRecord).where(IncidentRecord.id == inc_id))
        record = result.scalar_one_or_none()

        test_summary_str = json.dumps(incident_data.get("test_summary", {}))
        impacted_str = json.dumps(incident_data.get("impacted_services", []))

        if record is None:
            record = IncidentRecord(
                id=inc_id,
                service_name=incident_data.get("service_name", "unknown"),
                title=incident_data.get("title", "Untitled Incident"),
                severity=incident_data.get("severity", "critical"),
                status=incident_data.get("status", "triaging"),
                hypothesis=incident_data.get("hypothesis", ""),
                confidence_score=float(incident_data.get("confidence_score", 0.0)),
                candidate_patch=incident_data.get("candidate_patch", ""),
                verification_status=incident_data.get("verification_status", "pending"),
                test_summary_json=test_summary_str,
                impacted_services_json=impacted_str,
                pr_url=incident_data.get("pr_url"),
            )
            session.add(record)
        else:
            record.status = incident_data.get("status", record.status)
            record.hypothesis = incident_data.get("hypothesis", record.hypothesis)
            record.confidence_score = float(incident_data.get("confidence_score", record.confidence_score))
            record.candidate_patch = incident_data.get("candidate_patch", record.candidate_patch)
            record.verification_status = incident_data.get("verification_status", record.verification_status)
            record.test_summary_json = test_summary_str
            record.impacted_services_json = impacted_str
            if incident_data.get("pr_url"):
                record.pr_url = incident_data["pr_url"]
            if incident_data.get("resolved_at"):
                record.resolved_at = incident_data["resolved_at"]

        await session.commit()
        await session.refresh(record)
        return record


async def db_get_topology() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    session_factory = get_session_factory()
    async with session_factory() as session:
        node_res = await session.execute(select(TopologyNodeRecord))
        nodes = [
            {
                "id": n.id,
                "name": n.name,
                "type": n.node_type,
                "tier": n.tier,
                "criticality": n.criticality,
            }
            for n in node_res.scalars().all()
        ]
        edge_res = await session.execute(select(TopologyEdgeRecord))
        edges = [
            {
                "id": e.id,
                "source": e.source,
                "target": e.target,
                "relationship": e.relationship,
            }
            for e in edge_res.scalars().all()
        ]
        return nodes, edges
