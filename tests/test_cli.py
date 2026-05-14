from __future__ import annotations

import io
import tempfile
import textwrap
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import MagicMock, patch

from infra_dna.cli import main


class CliTests(unittest.TestCase):
    def make_arch(self) -> tuple[tempfile.TemporaryDirectory[str], Path]:
        tempdir = tempfile.TemporaryDirectory()
        arch_path = Path(tempdir.name) / "arch"
        arch_path.mkdir(parents=True)
        return tempdir, arch_path

    def write_file(self, path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(content).strip() + "\n", encoding="utf-8")

    def write_valid_graph(self, arch_path: Path) -> None:
        self.write_file(
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

    def write_config(self, path: Path) -> None:
        self.write_file(
            path,
            """
            [neo4j]
            uri = "bolt://localhost:7687"
            username = "neo4j"
            password = "secret"
            database = "infra"
            """,
        )

    def test_validate_only_skips_neo4j_config_and_loading(self) -> None:
        """
        GIVEN valid YAML and no runtime config file
        WHEN the CLI runs with --validate-only
        THEN we expect validation to succeed without requiring Neo4j config or loading
        """
        tempdir, arch_path = self.make_arch()
        self.addCleanup(tempdir.cleanup)
        self.write_valid_graph(arch_path)
        stdout = io.StringIO()
        stderr = io.StringIO()

        with redirect_stdout(stdout), redirect_stderr(stderr):
            exit_code = main([str(arch_path), "--validate-only"])

        self.assertEqual(0, exit_code)
        self.assertEqual("", stderr.getvalue())
        self.assertIn("Validated 2 entities and 1 relations.", stdout.getvalue())
        self.assertIn("Neo4j load skipped (--validate-only).", stdout.getvalue())

    def test_non_interactive_load_requires_force(self) -> None:
        """
        GIVEN valid YAML, a valid config file, and a non-interactive terminal
        WHEN the CLI runs without --force
        THEN we expect Neo4j loading to be refused before any service construction
        """
        tempdir, arch_path = self.make_arch()
        self.addCleanup(tempdir.cleanup)
        self.write_valid_graph(arch_path)
        config_path = Path(tempdir.name) / "infra-dna.toml"
        self.write_config(config_path)
        stdout = io.StringIO()
        stderr = io.StringIO()

        with (
            patch("infra_dna.cli.sys.stdin.isatty", return_value=False),
            patch("infra_dna.cli.Neo4jService") as service_factory,
            redirect_stdout(stdout),
            redirect_stderr(stderr),
        ):
            exit_code = main([str(arch_path), "--config", str(config_path)])

        self.assertEqual(1, exit_code)
        self.assertIn("Refusing to clear and reload Neo4j", stderr.getvalue())
        service_factory.assert_not_called()

    def test_force_load_uses_override_config_and_dispatches_neo4j(self) -> None:
        """
        GIVEN valid YAML, a valid override config file, and --force
        WHEN the CLI runs in Neo4j load mode
        THEN we expect the configured Neo4j service and visitor to be constructed and dispatched
        """
        tempdir, arch_path = self.make_arch()
        self.addCleanup(tempdir.cleanup)
        self.write_valid_graph(arch_path)
        config_path = Path(tempdir.name) / "custom.toml"
        self.write_config(config_path)
        visitor = MagicMock()
        visitor.on_start = MagicMock()
        visitor.on_entity = MagicMock()
        visitor.on_relation = MagicMock()
        visitor.on_finish = MagicMock()
        stdout = io.StringIO()
        stderr = io.StringIO()

        with (
            patch("infra_dna.cli.Neo4jService") as service_factory,
            patch("infra_dna.cli.Neo4jVisitorHandler", return_value=visitor) as visitor_factory,
            redirect_stdout(stdout),
            redirect_stderr(stderr),
        ):
            exit_code = main([str(arch_path), "--config", str(config_path), "--force"])

        self.assertEqual(0, exit_code)
        self.assertEqual("", stderr.getvalue())
        service_factory.assert_called_once_with(
            uri="bolt://localhost:7687",
            username="neo4j",
            password="secret",
            database="infra",
        )
        visitor_factory.assert_called_once_with(service_factory.return_value)
        visitor.on_start.assert_called_once_with()
        visitor.on_finish.assert_called_once_with()
        self.assertEqual(2, visitor.on_entity.call_count)
        self.assertEqual(1, visitor.on_relation.call_count)
        self.assertIn("Loaded graph into Neo4j database 'infra'", stdout.getvalue())

    def test_interactive_cancel_stops_before_loading(self) -> None:
        """
        GIVEN valid YAML, a valid config file, and an interactive terminal
        WHEN the user declines the destructive Neo4j reload prompt
        THEN we expect the load to be cancelled without constructing Neo4j services
        """
        tempdir, arch_path = self.make_arch()
        self.addCleanup(tempdir.cleanup)
        self.write_valid_graph(arch_path)
        config_path = Path(tempdir.name) / "infra-dna.toml"
        self.write_config(config_path)
        stdout = io.StringIO()
        stderr = io.StringIO()

        with (
            patch("infra_dna.cli.sys.stdin.isatty", return_value=True),
            patch("builtins.input", return_value="n"),
            patch("infra_dna.cli.Neo4jService") as service_factory,
            redirect_stdout(stdout),
            redirect_stderr(stderr),
        ):
            exit_code = main([str(arch_path), "--config", str(config_path)])

        self.assertEqual(1, exit_code)
        self.assertIn("Neo4j load cancelled by user.", stderr.getvalue())
        service_factory.assert_not_called()
