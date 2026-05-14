"""Runtime configuration loading for infra-dna."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tomllib


@dataclass(frozen=True, slots=True)
class Neo4jConfig:
    """Neo4j runtime settings."""

    uri: str
    username: str
    password: str
    database: str | None = None


@dataclass(frozen=True, slots=True)
class AppConfig:
    """Top-level runtime configuration."""

    neo4j: Neo4jConfig


class ConfigError(ValueError):
    """Raised when runtime configuration cannot be loaded."""


class AppConfigLoader:
    """Loads typed runtime configuration from TOML."""

    DEFAULT_FILENAME = "infra-dna.toml"

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path is not None else Path(self.DEFAULT_FILENAME)

    def load(self) -> AppConfig:
        try:
            with self.path.open("rb") as handle:
                document = tomllib.load(handle)
        except FileNotFoundError as exc:
            raise ConfigError(f"Configuration file not found: {self.path}") from exc
        except tomllib.TOMLDecodeError as exc:
            raise ConfigError(f"Invalid configuration file '{self.path}': {exc}") from exc

        if not isinstance(document, dict):
            raise ConfigError(f"Configuration file must contain a top-level mapping: {self.path}")

        neo4j_section = document.get("neo4j")
        if not isinstance(neo4j_section, dict):
            raise ConfigError(f"Missing required [neo4j] section in {self.path}")

        uri = self._require_string(neo4j_section, "uri")
        username = self._require_string(neo4j_section, "username")
        password = self._require_string(neo4j_section, "password")
        database = self._optional_string(neo4j_section, "database")

        return AppConfig(
            neo4j=Neo4jConfig(
                uri=uri,
                username=username,
                password=password,
                database=database,
            )
        )

    def _require_string(self, payload: dict[str, object], field_name: str) -> str:
        value = payload.get(field_name)
        if not isinstance(value, str) or not value.strip():
            raise ConfigError(f"Missing required neo4j setting: {field_name}")
        return value

    def _optional_string(self, payload: dict[str, object], field_name: str) -> str | None:
        value = payload.get(field_name)
        if value is None:
            return None
        if not isinstance(value, str) or not value.strip():
            raise ConfigError(f"Invalid neo4j setting '{field_name}': expected string")
        return value
