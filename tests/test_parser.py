from __future__ import annotations

import tempfile
import textwrap
import unittest
from pathlib import Path

from infra_dna.consumers import CallbackConsumer, GraphConsumer
from infra_dna.models import EntityRecord, RelationRecord
from infra_dna.parser import GraphParser


class RecordingConsumer(GraphConsumer):
    def __init__(self) -> None:
        self.events: list[object] = []
        self.entities: list[EntityRecord] = []
        self.relations: list[RelationRecord] = []

    def on_start(self) -> None:
        self.events.append("start")

    def on_entity(self, entity: EntityRecord) -> None:
        self.events.append(("entity", entity.identity))
        self.entities.append(entity)

    def on_relation(self, relation: RelationRecord) -> None:
        self.events.append(("relation", relation.identity))
        self.relations.append(relation)

    def on_finish(self) -> None:
        self.events.append("finish")


class GraphParserTests(unittest.TestCase):
    def make_arch(self) -> tuple[tempfile.TemporaryDirectory[str], Path]:
        tempdir = tempfile.TemporaryDirectory()
        arch_path = Path(tempdir.name) / "arch"
        arch_path.mkdir(parents=True)
        return tempdir, arch_path

    def write_yaml(self, path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(content).strip() + "\n", encoding="utf-8")

    def test_recursive_discovery_and_mixed_documents(self) -> None:
        """
        GIVEN nested YAML files where one mixed document defines entities and relations
        WHEN the parser scans the arch directory recursively
        THEN we expect all valid entities and relations to be discovered and accepted
        """
        tempdir, arch_path = self.make_arch()
        self.addCleanup(tempdir.cleanup)

        self.write_yaml(
            arch_path / "nested" / "anything.yml",
            """
            entities:
              - kind: vendor
                key: cloudflare
            relations:
              - from:
                  kind: vendor
                  key: cloudflare
                type: provides
                to:
                  kind: domain
                  key: somedomain.com
            """,
        )
        self.write_yaml(
            arch_path / "odd-name.yaml",
            """
            entities:
              - kind: domain
                key: somedomain.com
                props:
                  unique_visits: 17290000
            """,
        )

        result = GraphParser(arch_path).parse()

        self.assertTrue(result.is_valid)
        self.assertEqual(2, len(result.entities))
        self.assertEqual(1, len(result.relations))

    def test_strict_top_level_validation(self) -> None:
        """
        GIVEN a YAML document with an unknown top-level key
        WHEN the parser validates the document shape
        THEN we expect a validation error for the unexpected key
        """
        tempdir, arch_path = self.make_arch()
        self.addCleanup(tempdir.cleanup)

        self.write_yaml(
            arch_path / "bad.yml",
            """
            relation:
              - from:
                  kind: vendor
                  key: cloudflare
            """,
        )

        result = GraphParser(arch_path).parse()

        self.assertFalse(result.is_valid)
        messages = [error.message for error in result.errors]
        self.assertTrue(any("Unknown top-level keys: relation" in message for message in messages))

    def test_malformed_records_are_reported(self) -> None:
        """
        GIVEN entity and relation records with malformed fields
        WHEN the parser validates those records
        THEN we expect aggregated validation errors describing each malformed field
        """
        tempdir, arch_path = self.make_arch()
        self.addCleanup(tempdir.cleanup)

        self.write_yaml(
            arch_path / "bad-entities.yml",
            """
            entities:
              - key: missing-kind
              - kind: vendor
                key: ok
                props: wrong
            relations:
              - from: wrong
                type: provides
                to:
                  kind: domain
                  key: somedomain.com
            """,
        )

        result = GraphParser(arch_path).parse()

        self.assertFalse(result.is_valid)
        messages = [error.message for error in result.errors]
        self.assertTrue(any("Entity field 'kind' must be a non-empty string" in message for message in messages))
        self.assertTrue(any("Entity field 'props' must be a mapping" in message for message in messages))
        self.assertTrue(any("Relation field 'from' must be a mapping" in message for message in messages))

    def test_duplicate_reporting_includes_all_occurrences(self) -> None:
        """
        GIVEN duplicate entity and relation identities across multiple files
        WHEN the parser validates the full input set
        THEN we expect duplicate errors that include every conflicting occurrence
        """
        tempdir, arch_path = self.make_arch()
        self.addCleanup(tempdir.cleanup)

        self.write_yaml(
            arch_path / "one.yml",
            """
            entities:
              - kind: vendor
                key: cloudflare
              - kind: domain
                key: somedomain.com
            relations:
              - from:
                  kind: vendor
                  key: cloudflare
                type: provides
                to:
                  kind: domain
                  key: somedomain.com
            """,
        )
        self.write_yaml(
            arch_path / "two.yml",
            """
            entities:
              - kind: vendor
                key: cloudflare
            relations:
              - from:
                  kind: vendor
                  key: cloudflare
                type: provides
                to:
                  kind: domain
                  key: somedomain.com
            """,
        )
        self.write_yaml(
            arch_path / "nested" / "three.yml",
            """
            entities:
              - kind: vendor
                key: cloudflare
            relations:
              - from:
                  kind: vendor
                  key: cloudflare
                type: provides
                to:
                  kind: domain
                  key: somedomain.com
            """,
        )

        result = GraphParser(arch_path).parse()

        duplicate_entity_error = next(
            error for error in result.errors if "Duplicate entity identity" in error.message
        )
        duplicate_relation_error = next(
            error for error in result.errors if "Duplicate relation identity" in error.message
        )
        self.assertEqual(3, len(duplicate_entity_error.locations))
        self.assertEqual(3, len(duplicate_relation_error.locations))

    def test_missing_entity_references_and_consumer_dispatch(self) -> None:
        """
        GIVEN a valid graph first and then a second run with a missing relation endpoint
        WHEN the parser dispatches consumers for the valid run and validates the invalid run
        THEN we expect lifecycle-ordered consumer callbacks only for the valid run and none for the invalid one
        """
        tempdir, arch_path = self.make_arch()
        self.addCleanup(tempdir.cleanup)

        self.write_yaml(
            arch_path / "graph.yml",
            """
            entities:
              - kind: vendor
                key: cloudflare
              - kind: domain
                key: somedomain.com
            relations:
              - from:
                  kind: vendor
                  key: cloudflare
                type: provides
                to:
                  kind: domain
                  key: somedomain.com
            """,
        )

        recording_consumer = RecordingConsumer()
        callback_entities: list[EntityRecord] = []
        callback_relations: list[RelationRecord] = []
        callback_consumer = CallbackConsumer(
            on_entity_callback=callback_entities.append,
            on_relation_callback=callback_relations.append,
        )

        valid_result = GraphParser(
            arch_path,
            consumers=[recording_consumer, callback_consumer],
        ).parse()

        self.assertTrue(valid_result.is_valid)
        self.assertEqual(2, len(recording_consumer.entities))
        self.assertEqual(1, len(recording_consumer.relations))
        self.assertEqual(2, len(callback_entities))
        self.assertEqual(1, len(callback_relations))
        self.assertEqual(
            [
                "start",
                ("entity", ("vendor", "cloudflare")),
                ("entity", ("domain", "somedomain.com")),
                ("relation", ("vendor", "cloudflare", "provides", "domain", "somedomain.com")),
                "finish",
            ],
            recording_consumer.events,
        )

        self.write_yaml(
            arch_path / "bad-relation.yml",
            """
            relations:
              - from:
                  kind: vendor
                  key: cloudflare
                type: provides
                to:
                  kind: domain
                  key: missing.example
            """,
        )

        blocked_consumer = RecordingConsumer()
        invalid_result = GraphParser(arch_path, consumers=[blocked_consumer]).parse()

        self.assertFalse(invalid_result.is_valid)
        self.assertEqual([], blocked_consumer.entities)
        self.assertEqual([], blocked_consumer.relations)
        self.assertEqual([], blocked_consumer.events)
        self.assertTrue(
            any(
                "Relation references unknown entities" in error.message
                for error in invalid_result.errors
            )
        )

    def test_invalid_relation_type_is_reported(self) -> None:
        """
        GIVEN a relation type that violates the lowercase-safe naming rule
        WHEN the parser validates the relation record
        THEN we expect a validation error describing the allowed relation type format
        """
        tempdir, arch_path = self.make_arch()
        self.addCleanup(tempdir.cleanup)

        self.write_yaml(
            arch_path / "graph.yml",
            """
            entities:
              - kind: vendor
                key: edgecorp
              - kind: domain
                key: example-app.test
            relations:
              - from:
                  kind: vendor
                  key: edgecorp
                type: Provides
                to:
                  kind: domain
                  key: example-app.test
            """,
        )

        result = GraphParser(arch_path).parse()

        self.assertFalse(result.is_valid)
        self.assertTrue(
            any(
                "Relation field 'type' must start with a lowercase letter" in error.message
                for error in result.errors
            )
        )

    def test_parse_can_defer_dispatch_until_caller_decides(self) -> None:
        """
        GIVEN a valid graph and a configured consumer
        WHEN the parser runs with dispatch disabled and the caller dispatches later
        THEN we expect validation to succeed first and consumer callbacks to run only during explicit dispatch
        """
        tempdir, arch_path = self.make_arch()
        self.addCleanup(tempdir.cleanup)
        self.write_yaml(
            arch_path / "graph.yml",
            """
            entities:
              - kind: vendor
                key: edgecorp
              - kind: domain
                key: example-app.test
            relations:
              - from:
                  kind: vendor
                  key: edgecorp
                type: provides
                to:
                  kind: domain
                  key: example-app.test
            """,
        )

        consumer = RecordingConsumer()
        parser = GraphParser(arch_path, consumers=[consumer])

        result = parser.parse(dispatch=False)

        self.assertTrue(result.is_valid)
        self.assertEqual([], consumer.events)

        parser.dispatch(result)

        self.assertEqual(
            [
                "start",
                ("entity", ("vendor", "edgecorp")),
                ("entity", ("domain", "example-app.test")),
                ("relation", ("vendor", "edgecorp", "provides", "domain", "example-app.test")),
                "finish",
            ],
            consumer.events,
        )

    def test_dispatch_skips_invalid_results(self) -> None:
        """
        GIVEN an invalid parse result and a configured consumer
        WHEN the caller tries to dispatch it explicitly
        THEN we expect no lifecycle or record callbacks to be invoked
        """
        tempdir, arch_path = self.make_arch()
        self.addCleanup(tempdir.cleanup)
        self.write_yaml(
            arch_path / "graph.yml",
            """
            relations:
              - from:
                  kind: vendor
                  key: edgecorp
                type: provides
                to:
                  kind: domain
                  key: missing.example
            """,
        )

        consumer = RecordingConsumer()
        parser = GraphParser(arch_path, consumers=[consumer])
        result = parser.parse(dispatch=False)

        self.assertFalse(result.is_valid)

        parser.dispatch(result)

        self.assertEqual([], consumer.events)


if __name__ == "__main__":
    unittest.main()
