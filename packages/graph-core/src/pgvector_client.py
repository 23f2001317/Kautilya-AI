# packages/graph-core/src/pgvector_client.py
"""PostgreSQL + pgvector vector storage client for runbooks and documentation."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from pgvector.sqlalchemy import Vector
from sqlalchemy import Integer, String, Text, select, text
from sqlalchemy.ext.asyncio import (
    AsyncAttrs,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
import structlog

logger = structlog.get_logger(__name__)


class Base(AsyncAttrs, DeclarativeBase):
    """Base class for SQLAlchemy declarative models."""


class RunbookEmbedding(Base):
    """Database model for storing service runbooks and their dense vector embeddings."""

    __tablename__ = "runbook_embeddings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    service_name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(Vector(1536), nullable=False)


async def init_vector_db(engine: AsyncEngine) -> None:
    """Ensure the pgvector extension is created and tables are synchronized.

    Args:
        engine: Active SQLAlchemy AsyncEngine instance.
    """
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)
        logger.info("pgvector_database_initialized")


async def upsert_runbook_embedding(
    session: AsyncSession,
    service_name: str,
    content: str,
    vector_data: list[float],
    embedding_id: int | None = None,
) -> RunbookEmbedding:
    """Insert or update a runbook and its associated 1536-dimensional vector embedding.

    Args:
        session: Active SQLAlchemy AsyncSession.
        service_name: Microservice associated with the runbook.
        content: Text content of the runbook/SOP.
        vector_data: Dense vector embedding (1536 floats).
        embedding_id: Optional ID for updating an existing record.

    Returns:
        The created or updated RunbookEmbedding entity.
    """
    record: RunbookEmbedding | None = None

    if embedding_id is not None:
        stmt = select(RunbookEmbedding).where(RunbookEmbedding.id == embedding_id)
        result = await session.execute(stmt)
        record = result.scalar_one_or_none()

    if record is None:
        # Check if identical service_name and content already exists to avoid duplication
        stmt = select(RunbookEmbedding).where(
            RunbookEmbedding.service_name == service_name,
            RunbookEmbedding.content == content,
        )
        result = await session.execute(stmt)
        record = result.scalar_one_or_none()

    if record is not None:
        record.service_name = service_name
        record.content = content
        record.embedding = vector_data
        logger.info(
            "updated_runbook_embedding",
            record_id=record.id,
            service_name=service_name,
        )
    else:
        record = RunbookEmbedding(
            service_name=service_name,
            content=content,
            embedding=vector_data,
        )
        session.add(record)
        logger.info(
            "inserted_runbook_embedding",
            service_name=service_name,
        )

    await session.commit()
    await session.refresh(record)
    return record


@asynccontextmanager
async def get_async_session(
    database_url: str = "postgresql+asyncpg://kautilya_user:kautilya_password@localhost:5432/kautilya_db",
) -> AsyncIterator[AsyncSession]:
    """Provide an asynchronous database session context.

    Args:
        database_url: Connection string for PostgreSQL via asyncpg.

    Yields:
        AsyncSession: Active database session.
    """
    engine = create_async_engine(database_url, echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with session_factory() as session:
        try:
            yield session
        finally:
            await engine.dispose()
