"""Parser and validator for infrastructure graph YAML."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re
from typing import Any, Iterable

import yaml

from .consumers import GraphConsumer
from .models import EntityRecord, ParseResult, RelationRecord, SourceLocation, ValidationError

ALLOWED_TOP_LEVEL_KEYS = frozenset({"entities", "relations"})
RELATION_TYPE_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")

@dataclass(slots=True)
class _ParserState:
    """Mutable state used during parsing."""

    errors: list[ValidationError] = field(default_factory=list)
    discovered_entities: dict[tuple[str, str], list[EntityRecord]] = field(default_factory=dict)
    discovered_relations: dict[
        tuple[str, str, str, str, str], list[RelationRecord]
    ] = field(default_factory=dict)
    valid_entity_records: list[EntityRecord] = field(default_factory=list)
    valid_relation_records: list[RelationRecord] = field(default_factory=list)
    known_entity_identities: set[tuple[str, str]] = field(default_factory=set)
    top_level_checked: set[Path] = field(default_factory=set)


class GraphParser:
    """Parses and validates graph YAML under an arch directory."""

    def __init__(self, arch_path: str | Path, consumers: Iterable[GraphConsumer] | None = None):
        self.arch_path = Path(arch_path)
        self._consumers = list(consumers or [])

    def discover_files(self) -> list[Path]:
        if not self.arch_path.exists():
            return []

        files = [
            path
            for path in self.arch_path.rglob("*")
            if path.is_file() and path.suffix.lower() in {".yml", ".yaml"}
        ]
        return sorted(files)

    def parse(self, dispatch: bool = True) -> ParseResult:
        """
        This parser is intentionally not fully streaming: it validates the full
        dataset first, aggregates all errors, and only dispatches records to
        consumers after the entire run is known-valid. Callers may defer
        dispatch so they can make post-validation decisions before any
        consumer side effects begin.
        """
        state = _ParserState()
        files = self.discover_files()

        for path in files:
            document = self._load_document(path, state)
            self._parse_entities_from_document(path, document, state)

        self._collect_duplicate_entity_errors(state)

        for path in files:
            document = self._load_document(path, state)
            self._parse_relations_from_document(path, document, state)

        self._collect_duplicate_relation_errors(state)

        result = ParseResult(
            entities=tuple(self._unique_entity_records(state)),
            relations=tuple(self._unique_relation_records(state)),
            errors=tuple(state.errors),
        )

        if dispatch:
            self.dispatch(result)

        return result

    def dispatch(
        self,
        result: ParseResult,
        consumers: Iterable[GraphConsumer] | None = None,
    ) -> None:
        if not result.is_valid:
            return

        active_consumers = list(self._consumers if consumers is None else consumers)
        started_consumers: list[GraphConsumer] = []
        try:
            for consumer in active_consumers:
                started_consumers.append(consumer)
                consumer.on_start()

            for entity in result.entities:
                for consumer in active_consumers:
                    consumer.on_entity(entity)
            for relation in result.relations:
                for consumer in active_consumers:
                    consumer.on_relation(relation)
        finally:
            for consumer in reversed(started_consumers):
                consumer.on_finish()

    def _load_document(self, path: Path, state: _ParserState) -> Any:
        try:
            with path.open("r", encoding="utf-8") as handle:
                document = yaml.safe_load(handle)
        except yaml.YAMLError as exc:
            self._add_error(state, f"Invalid YAML syntax: {exc}", path=path)
            return None

        if path not in state.top_level_checked:
            state.top_level_checked.add(path)
            self._validate_document_shape(path, document, state)

        return document

    def _validate_document_shape(self, path: Path, document: Any, state: _ParserState) -> None:
        if not isinstance(document, dict):
            self._add_error(
                state,
                "YAML document must be a mapping with top-level 'entities' and/or 'relations' keys",
                path=path,
            )
            return

        keys = set(document)
        unknown_keys = sorted(keys - ALLOWED_TOP_LEVEL_KEYS)
        if unknown_keys:
            self._add_error(
                state,
                f"Unknown top-level keys: {', '.join(unknown_keys)}",
                path=path,
            )

        if not keys.intersection(ALLOWED_TOP_LEVEL_KEYS):
            self._add_error(
                state,
                "YAML document must contain at least one of the top-level keys 'entities' or 'relations'",
                path=path,
            )

    def _parse_entities_from_document(self, path: Path, document: Any, state: _ParserState) -> None:
        if not isinstance(document, dict) or "entities" not in document:
            return

        entities = document["entities"]
        if not isinstance(entities, list):
            self._add_error(state, "Top-level 'entities' value must be a list", path=path)
            return

        for index, item in enumerate(entities):
            location = SourceLocation(path=path, section="entities", index=index)
            entity = self._build_entity(item, location, state)
            if entity is None:
                continue
            state.valid_entity_records.append(entity)
            state.discovered_entities.setdefault(entity.identity, []).append(entity)
            state.known_entity_identities.add(entity.identity)

    def _parse_relations_from_document(self, path: Path, document: Any, state: _ParserState) -> None:
        if not isinstance(document, dict) or "relations" not in document:
            return

        relations = document["relations"]
        if not isinstance(relations, list):
            self._add_error(state, "Top-level 'relations' value must be a list", path=path)
            return

        for index, item in enumerate(relations):
            location = SourceLocation(path=path, section="relations", index=index)
            relation = self._build_relation(item, location, state)
            if relation is None:
                continue
            state.valid_relation_records.append(relation)
            state.discovered_relations.setdefault(relation.identity, []).append(relation)

    def _build_entity(
        self,
        raw_entity: Any,
        location: SourceLocation,
        state: _ParserState,
    ) -> EntityRecord | None:
        if not isinstance(raw_entity, dict):
            self._add_error(state, "Entity record must be a mapping", location=location)
            return None

        kind = self._require_non_empty_string(raw_entity, "kind", location, state, "Entity")
        key = self._require_non_empty_string(raw_entity, "key", location, state, "Entity")
        props = self._extract_props(raw_entity, location, state, "Entity")
        if kind is None or key is None or props is None:
            return None

        return EntityRecord(kind=kind, key=key, props=props, source=location)

    def _build_relation(
        self,
        raw_relation: Any,
        location: SourceLocation,
        state: _ParserState,
    ) -> RelationRecord | None:
        if not isinstance(raw_relation, dict):
            self._add_error(state, "Relation record must be a mapping", location=location)
            return None

        relation_type = self._require_non_empty_string(
            raw_relation, "type", location, state, "Relation"
        )
        from_endpoint = self._extract_endpoint(raw_relation, "from", location, state)
        to_endpoint = self._extract_endpoint(raw_relation, "to", location, state)
        props = self._extract_props(raw_relation, location, state, "Relation")

        if relation_type is None or from_endpoint is None or to_endpoint is None or props is None:
            return None
        if not RELATION_TYPE_PATTERN.fullmatch(relation_type):
            self._add_error(
                state,
                "Relation field 'type' must start with a lowercase letter and contain only lowercase letters, digits, and underscores",
                location=location,
            )
            return None

        relation = RelationRecord(
            from_kind=from_endpoint[0],
            from_key=from_endpoint[1],
            relation_type=relation_type,
            to_kind=to_endpoint[0],
            to_key=to_endpoint[1],
            props=props,
            source=location,
        )
        self._validate_relation_endpoint(relation, state)
        return relation

    def _extract_endpoint(
        self,
        raw_relation: dict[str, Any],
        field_name: str,
        location: SourceLocation,
        state: _ParserState,
    ) -> tuple[str, str] | None:
        endpoint = raw_relation.get(field_name)
        if not isinstance(endpoint, dict):
            self._add_error(state, f"Relation field '{field_name}' must be a mapping", location=location)
            return None

        kind = self._require_non_empty_string(endpoint, "kind", location, state, f"Relation {field_name}")
        key = self._require_non_empty_string(endpoint, "key", location, state, f"Relation {field_name}")
        if kind is None or key is None:
            return None
        return (kind, key)

    def _extract_props(
        self,
        payload: dict[str, Any],
        location: SourceLocation,
        state: _ParserState,
        label: str,
    ) -> dict[str, Any] | None:
        props = payload.get("props", {})
        if not isinstance(props, dict):
            self._add_error(state, f"{label} field 'props' must be a mapping", location=location)
            return None
        return dict(props)

    def _require_non_empty_string(
        self,
        payload: dict[str, Any],
        field_name: str,
        location: SourceLocation,
        state: _ParserState,
        label: str,
    ) -> str | None:
        value = payload.get(field_name)
        if not isinstance(value, str) or not value.strip():
            self._add_error(
                state,
                f"{label} field '{field_name}' must be a non-empty string",
                location=location,
            )
            return None
        return value

    def _validate_relation_endpoint(self, relation: RelationRecord, state: _ParserState) -> None:
        missing = []
        if (relation.from_kind, relation.from_key) not in state.known_entity_identities:
            missing.append(f"from=({relation.from_kind}, {relation.from_key})")
        if (relation.to_kind, relation.to_key) not in state.known_entity_identities:
            missing.append(f"to=({relation.to_kind}, {relation.to_key})")
        if missing:
            self._add_error(
                state,
                "Relation references unknown entities: " + ", ".join(missing),
                location=relation.source,
            )

    def _collect_duplicate_entity_errors(self, state: _ParserState) -> None:
        for identity, records in state.discovered_entities.items():
            if len(records) < 2:
                continue
            self._add_error(
                state,
                f"Duplicate entity identity {identity!r}",
                locations=[record.source for record in records],
            )

    def _collect_duplicate_relation_errors(self, state: _ParserState) -> None:
        for identity, records in state.discovered_relations.items():
            if len(records) < 2:
                continue
            self._add_error(
                state,
                f"Duplicate relation identity {identity!r}",
                locations=[record.source for record in records],
            )

    def _unique_entity_records(self, state: _ParserState) -> list[EntityRecord]:
        unique_records: list[EntityRecord] = []
        for records in state.discovered_entities.values():
            if len(records) == 1:
                unique_records.append(records[0])
        return sorted(unique_records, key=lambda record: record.source.display())

    def _unique_relation_records(self, state: _ParserState) -> list[RelationRecord]:
        unique_records: list[RelationRecord] = []
        for records in state.discovered_relations.values():
            if len(records) == 1:
                unique_records.append(records[0])
        return sorted(unique_records, key=lambda record: record.source.display())

    def _add_error(
        self,
        state: _ParserState,
        message: str,
        *,
        path: Path | None = None,
        location: SourceLocation | None = None,
        locations: Iterable[SourceLocation] | None = None,
    ) -> None:
        if locations is not None:
            error_locations = tuple(locations)
        elif location is not None:
            error_locations = (location,)
        elif path is not None:
            error_locations = (SourceLocation(path=path, section="document", index=0),)
        else:
            error_locations = ()
        state.errors.append(ValidationError(message=message, locations=error_locations))
