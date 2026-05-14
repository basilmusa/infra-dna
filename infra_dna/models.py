"""Shared data models for validated graph records."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class SourceLocation:
    """Describes where a record came from."""

    path: Path
    section: str
    index: int

    def display(self) -> str:
        return f"{self.path}:{self.section}[{self.index}]"


@dataclass(frozen=True, slots=True)
class EntityRecord:
    """Canonical validated entity record."""

    kind: str
    key: str
    props: dict[str, Any]
    source: SourceLocation

    @property
    def identity(self) -> tuple[str, str]:
        return (self.kind, self.key)


@dataclass(frozen=True, slots=True)
class RelationRecord:
    """Canonical validated relation record."""

    from_kind: str
    from_key: str
    relation_type: str
    to_kind: str
    to_key: str
    props: dict[str, Any]
    source: SourceLocation

    @property
    def identity(self) -> tuple[str, str, str, str, str]:
        return (
            self.from_kind,
            self.from_key,
            self.relation_type,
            self.to_kind,
            self.to_key,
        )


@dataclass(frozen=True, slots=True)
class ValidationError:
    """Aggregated validation error."""

    message: str
    locations: tuple[SourceLocation, ...] = ()

    def format(self) -> str:
        if not self.locations:
            return self.message
        lines = [self.message]
        for location in self.locations:
            lines.append(f"  - {location.display()}")
        return "\n".join(lines)


@dataclass(frozen=True, slots=True)
class ParseResult:
    """Result of a parser run."""

    entities: tuple[EntityRecord, ...]
    relations: tuple[RelationRecord, ...]
    errors: tuple[ValidationError, ...]

    @property
    def is_valid(self) -> bool:
        return not self.errors
