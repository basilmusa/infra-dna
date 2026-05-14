"""Neo4j-backed graph consumer."""

from __future__ import annotations

from .consumers import GraphConsumer
from .models import EntityRecord, RelationRecord
from .neo4j_service import Neo4jService


class Neo4jVisitorHandler(GraphConsumer):
    """Graph consumer that loads validated records into Neo4j."""

    def __init__(self, neo4j_service: Neo4jService) -> None:
        self._neo4j_service = neo4j_service

    def on_start(self) -> None:
        self._neo4j_service.clear_graph()
        self._neo4j_service.ensure_schema()

    def on_entity(self, entity: EntityRecord) -> None:
        self._neo4j_service.execute_write(
            """
            MERGE (n:Entity {kind: $kind, key: $key})
            SET n += $props
            """,
            {
                "kind": entity.kind,
                "key": entity.key,
                "props": entity.props,
            },
        )

    def on_relation(self, relation: RelationRecord) -> None:
        query = f"""
            MATCH (a:Entity {{kind: $from_kind, key: $from_key}})
            MATCH (b:Entity {{kind: $to_kind, key: $to_key}})
            MERGE (a)-[r:{relation.relation_type}]->(b)
            SET r += $props
        """
        self._neo4j_service.execute_write(
            query,
            {
                "from_kind": relation.from_kind,
                "from_key": relation.from_key,
                "to_kind": relation.to_kind,
                "to_key": relation.to_key,
                "props": relation.props,
            },
        )

    def on_finish(self) -> None:
        self._neo4j_service.close()
