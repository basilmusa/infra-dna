"""Consumer interfaces for validated graph records."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .models import EntityRecord, RelationRecord


class GraphConsumer:
    """Base consumer for validated graph records."""

    def on_start(self) -> None:
        """Prepare to receive validated records."""

    def on_entity(self, entity: EntityRecord) -> None:
        """Handle a validated entity."""

    def on_relation(self, relation: RelationRecord) -> None:
        """Handle a validated relation."""

    def on_finish(self) -> None:
        """Finalize record handling."""


@dataclass(slots=True)
class CallbackConsumer(GraphConsumer):
    """Adapts plain callbacks into the consumer interface."""

    on_entity_callback: Callable[[EntityRecord], None] | None = None
    on_relation_callback: Callable[[RelationRecord], None] | None = None

    def on_entity(self, entity: EntityRecord) -> None:
        if self.on_entity_callback is not None:
            self.on_entity_callback(entity)

    def on_relation(self, relation: RelationRecord) -> None:
        if self.on_relation_callback is not None:
            self.on_relation_callback(relation)


class PrintToConsole(GraphConsumer):
    """Simple consumer that prints validated records to stdout."""

    def on_entity(self, entity: EntityRecord) -> None:
        print(entity)

    def on_relation(self, relation: RelationRecord) -> None:
        print(relation)
