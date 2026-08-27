# packages/graph-core/src/neo4j_client.py
"""Asynchronous Neo4j client and topological graph schema manager."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from neo4j import AsyncDriver, AsyncGraphDatabase, AsyncSession
import structlog

logger = structlog.get_logger(__name__)


class Neo4jManager:
    """Manages async Neo4j driver connections, schema bootstrapping, and graph mutations."""

    def __init__(
        self,
        uri: str = "bolt://localhost:7687",
        auth: tuple[str, str] = ("neo4j", "kautilya_password"),
        database: str = "neo4j",
    ) -> None:
        """Initialize the Neo4j connection parameters.

        Args:
            uri: Bolt connection URI for the Neo4j instance.
            auth: Tuple of (username, password).
            database: Target database name.
        """
        self._uri = uri
        self._auth = auth
        self._database = database
        self._driver: AsyncDriver | None = None

    async def connect(self) -> None:
        """Establish the async Neo4j driver instance."""
        if self._driver is None:
            self._driver = AsyncGraphDatabase.driver(self._uri, auth=self._auth)
            # Verify connectivity
            await self._driver.verify_connectivity()
            logger.info("neo4j_connected", uri=self._uri, database=self._database)

    async def close(self) -> None:
        """Gracefully close the Neo4j driver connection pool."""
        if self._driver is not None:
            await self._driver.close()
            self._driver = None
            logger.info("neo4j_connection_closed")

    @asynccontextmanager
    async def get_session(self) -> AsyncIterator[AsyncSession]:
        """Context manager providing an active async Neo4j session.

        Yields:
            AsyncSession: Active Neo4j session.

        Raises:
            RuntimeError: If connect() has not been called prior to acquiring a session.
        """
        if self._driver is None:
            raise RuntimeError("Neo4j driver is not connected. Call connect() first.")
        session: AsyncSession = self._driver.session(database=self._database)
        try:
            yield session
        finally:
            await session.close()

    async def bootstrap_constraints(self) -> None:
        """Create uniqueness constraints for Service, Commit, and Alert nodes if they do not exist."""
        constraints: list[str] = [
            "CREATE CONSTRAINT constraint_service_name IF NOT EXISTS FOR (s:Service) REQUIRE s.name IS UNIQUE",
            "CREATE CONSTRAINT constraint_commit_hash IF NOT EXISTS FOR (c:Commit) REQUIRE c.hash IS UNIQUE",
            "CREATE CONSTRAINT constraint_alert_id IF NOT EXISTS FOR (a:Alert) REQUIRE a.id IS UNIQUE",
        ]

        async with self.get_session() as session:
            for query in constraints:
                await session.run(query)
                logger.info("neo4j_constraint_ensured", query=query)

    async def merge_alert_impact(
        self,
        service_name: str,
        alert_id: str,
        alert_severity: str,
    ) -> dict[str, Any]:
        """Merge an Alert node, Service node, and the IMPACTS relationship between them.

        Uses strict parameterized Cypher query parameters to avoid injection.

        Args:
            service_name: Name of the impacted microservice.
            alert_id: Unique identifier for the alert.
            alert_severity: Severity level of the alert.

        Returns:
            Dictionary containing merged alert ID, service name, and severity.
        """
        cypher: str = """
        MERGE (a:Alert {id: $alert_id})
        ON CREATE SET a.severity = $alert_severity, a.created_at = datetime()
        ON MATCH SET a.severity = $alert_severity, a.updated_at = datetime()
        MERGE (s:Service {name: $service_name})
        MERGE (a)-[r:IMPACTS]->(s)
        RETURN a.id AS alert_id, s.name AS service_name, a.severity AS severity
        """
        parameters: dict[str, Any] = {
            "alert_id": alert_id,
            "service_name": service_name,
            "alert_severity": alert_severity,
        }

        async with self.get_session() as session:
            result = await session.run(cypher, parameters)
            record = await result.single()
            logger.info(
                "merged_alert_impact",
                alert_id=alert_id,
                service_name=service_name,
                severity=alert_severity,
            )
            if record:
                return dict(record.items())
            return parameters
