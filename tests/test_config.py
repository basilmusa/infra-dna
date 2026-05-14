from __future__ import annotations

import tempfile
import textwrap
import unittest
from pathlib import Path

from infra_dna.config import AppConfigLoader, ConfigError


class AppConfigLoaderTests(unittest.TestCase):
    def make_tempdir(self) -> tuple[tempfile.TemporaryDirectory[str], Path]:
        tempdir = tempfile.TemporaryDirectory()
        return tempdir, Path(tempdir.name)

    def write_toml(self, path: Path, content: str) -> None:
        path.write_text(textwrap.dedent(content).strip() + "\n", encoding="utf-8")

    def test_loader_reads_typed_neo4j_config(self) -> None:
        """
        GIVEN a valid infra-dna TOML config file
        WHEN the app config loader reads it
        THEN we expect typed application and Neo4j config values to be returned
        """
        tempdir, temp_path = self.make_tempdir()
        self.addCleanup(tempdir.cleanup)
        config_path = temp_path / "infra-dna.toml"
        self.write_toml(
            config_path,
            """
            [neo4j]
            uri = "bolt://localhost:7687"
            username = "neo4j"
            password = "secret"
            database = "infra"
            """,
        )

        config = AppConfigLoader(config_path).load()

        self.assertEqual("bolt://localhost:7687", config.neo4j.uri)
        self.assertEqual("neo4j", config.neo4j.username)
        self.assertEqual("secret", config.neo4j.password)
        self.assertEqual("infra", config.neo4j.database)

    def test_loader_rejects_missing_required_setting(self) -> None:
        """
        GIVEN a config file missing a required Neo4j setting
        WHEN the app config loader validates it
        THEN we expect a configuration error describing the missing field
        """
        tempdir, temp_path = self.make_tempdir()
        self.addCleanup(tempdir.cleanup)
        config_path = temp_path / "infra-dna.toml"
        self.write_toml(
            config_path,
            """
            [neo4j]
            uri = "bolt://localhost:7687"
            username = "neo4j"
            """,
        )

        with self.assertRaises(ConfigError) as raised:
            AppConfigLoader(config_path).load()

        self.assertIn("Missing required neo4j setting: password", str(raised.exception))

    def test_loader_rejects_invalid_optional_setting_type(self) -> None:
        """
        GIVEN a config file with a non-string optional Neo4j setting
        WHEN the app config loader validates it
        THEN we expect a configuration error describing the invalid type
        """
        tempdir, temp_path = self.make_tempdir()
        self.addCleanup(tempdir.cleanup)
        config_path = temp_path / "alt.toml"
        self.write_toml(
            config_path,
            """
            [neo4j]
            uri = "bolt://localhost:7687"
            username = "neo4j"
            password = "secret"
            database = 42
            """,
        )

        with self.assertRaises(ConfigError) as raised:
            AppConfigLoader(config_path).load()

        self.assertIn("Invalid neo4j setting 'database': expected string", str(raised.exception))
