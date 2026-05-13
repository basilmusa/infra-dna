"""Consumer interfaces for validated graph records."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


class GraphConsumer:
    """Base consumer for validated graph records."""

    def on_entity(self, entity: object) -> None:
        """Handle a validated entity."""

    def on_relation(self, relation: object) -> None:
        """Handle a validated relation."""


@dataclass(slots=True)
class CallbackConsumer(GraphConsumer):
    """Adapts plain callbacks into the consumer interface."""

    on_entity_callback: Callable[[object], None] | None = None
    on_relation_callback: Callable[[object], None] | None = None

    def on_entity(self, entity: object) -> None:
        if self.on_entity_callback is not None:
            self.on_entity_callback(entity)

    def on_relation(self, relation: object) -> None:
        if self.on_relation_callback is not None:
            self.on_relation_callback(relation)


class PrintToConsole(GraphConsumer):
    """Simple consumer that prints validated records to stdout."""

    def on_entity(self, entity: object) -> None:
        print(entity)

    def on_relation(self, relation: object) -> None:
        print(relation)
