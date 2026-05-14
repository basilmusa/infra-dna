from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from infra_dna.neo4j_service import Neo4jService


class FakeRecord:
    def __init__(self, payload: dict[str, object]) -> None:
        self._payload = payload

    def data(self) -> dict[str, object]:
        return self._payload


class Neo4jServiceTests(unittest.TestCase):
    @patch("infra_dna.neo4j_service.GraphDatabase.driver")
    def test_service_uses_constructor_parameters_and_executes_queries(
        self, driver_factory: MagicMock
    ) -> None:
        """
        GIVEN constructor-injected Neo4j connection parameters and a mocked driver
        WHEN the service executes read/write operations, clears the graph, and ensures schema
        THEN we expect the configured driver and sessions to be used consistently and the connection to close
        """
        driver = MagicMock()
        session_cm = MagicMock()
        session = MagicMock()
        session.run.return_value = [FakeRecord({"value": 1})]
        session_cm.__enter__.return_value = session
        session_cm.__exit__.return_value = False
        driver.session.return_value = session_cm
        driver_factory.return_value = driver

        service = Neo4jService(
            uri="bolt://localhost:7687",
            username="neo4j",
            password="secret",
            database="infra",
        )
        result = service.execute_read("RETURN 1 AS value")
        service.execute_write("RETURN 1 AS value")
        service.clear_graph()
        service.ensure_schema()
        service.close()

        driver_factory.assert_called_once_with("bolt://localhost:7687", auth=("neo4j", "secret"))
        self.assertEqual(4, driver.session.call_count)
        driver.session.assert_any_call(database="infra")
        session.run.assert_any_call("RETURN 1 AS value", {})
        self.assertEqual([{"value": 1}], result)
        driver.close.assert_called_once_with()
