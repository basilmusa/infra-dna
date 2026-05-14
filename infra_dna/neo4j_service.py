"""Neo4j service adapter."""

from __future__ import annotations

from typing import Any

from neo4j import GraphDatabase


class Neo4jService:
    """Thin adapter around the Neo4j Python driver."""

    def __init__(
        self,
        uri: str,
        username: str,
        password: str,
        database: str | None = None,
    ) -> None:
        self._database = database
        self._driver = GraphDatabase.driver(uri, auth=(username, password))

    def execute_read(
        self,
        query: str,
        parameters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        return self._execute(query, parameters)

    def execute_write(
        self,
        query: str,
        parameters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        return self._execute(query, parameters)

    def clear_graph(self) -> None:
        self.execute_write("MATCH (n) DETACH DELETE n")

    def ensure_schema(self) -> None:
        self.execute_write(
            """
            CREATE CONSTRAINT entity_identity IF NOT EXISTS
            FOR (n:Entity)
            REQUIRE (n.kind, n.key) IS UNIQUE
            """
        )

    def close(self) -> None:
        self._driver.close()

    def _execute(
        self,
        query: str,
        parameters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        with self._driver.session(database=self._database) as session:
            result = session.run(query, parameters or {})
            return [record.data() for record in result]
