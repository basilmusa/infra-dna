from __future__ import annotations

import tempfile
import textwrap
import unittest
from pathlib import Path

from infra_dna.consumers import CallbackConsumer
from infra_dna.parser import GraphParser


class RecordingConsumer:
    def __init__(self) -> None:
        self.entities = []
        self.relations = []

    def on_entity(self, entity: object) -> None:
        self.entities.append(entity)

    def on_relation(self, relation: object) -> None:
        self.relations.append(relation)


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
                type: PROVIDES
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
                type: PROVIDES
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
                type: PROVIDES
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
                type: PROVIDES
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
                type: PROVIDES
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
                type: PROVIDES
                to:
                  kind: domain
                  key: somedomain.com
            """,
        )

        recording_consumer = RecordingConsumer()
        callback_entities = []
        callback_relations = []
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

        self.write_yaml(
            arch_path / "bad-relation.yml",
            """
            relations:
              - from:
                  kind: vendor
                  key: cloudflare
                type: PROVIDES
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
        self.assertTrue(
            any(
                "Relation references unknown entities" in error.message
                for error in invalid_result.errors
            )
        )


if __name__ == "__main__":
    unittest.main()
