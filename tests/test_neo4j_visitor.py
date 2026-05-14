from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import MagicMock

from infra_dna.models import EntityRecord, RelationRecord, SourceLocation
from infra_dna.neo4j_visitor import Neo4jVisitorHandler


class Neo4jVisitorHandlerTests(unittest.TestCase):
    def make_location(self) -> SourceLocation:
        return SourceLocation(path=Path("arch/example.yml"), section="entities", index=0)

    def test_visitor_start_entity_relation_finish_order(self) -> None:
        """
        GIVEN a Neo4j visitor backed by a mocked service and validated graph records
        WHEN the visitor runs through start, entity load, relation load, and finish
        THEN we expect graph clearing, schema setup, MERGE-oriented writes, and final connection cleanup in order
        """
        service = MagicMock()
        visitor = Neo4jVisitorHandler(service)
        location = self.make_location()
        entity = EntityRecord(
            kind="vendor",
            key="edgecorp",
            props={"description": "Edge provider"},
            source=location,
        )
        relation = RelationRecord(
            from_kind="vendor",
            from_key="edgecorp",
            relation_type="provides",
            to_kind="domain",
            to_key="example-app.test",
            props={"role": "cdn"},
            source=location,
        )

        visitor.on_start()
        visitor.on_entity(entity)
        visitor.on_relation(relation)
        visitor.on_finish()

        service.clear_graph.assert_called_once_with()
        service.ensure_schema.assert_called_once_with()
        self.assertEqual(2, service.execute_write.call_count)
        entity_query, entity_params = service.execute_write.call_args_list[0].args
        self.assertIn("MERGE (n:Entity {kind: $kind, key: $key})", entity_query)
        self.assertEqual(
            {"kind": "vendor", "key": "edgecorp", "props": {"description": "Edge provider"}},
            entity_params,
        )
        relation_query, relation_params = service.execute_write.call_args_list[1].args
        self.assertIn("MERGE (a)-[r:provides]->(b)", relation_query)
        self.assertEqual(
            {
                "from_kind": "vendor",
                "from_key": "edgecorp",
                "to_kind": "domain",
                "to_key": "example-app.test",
                "props": {"role": "cdn"},
            },
            relation_params,
        )
        service.close.assert_called_once_with()
