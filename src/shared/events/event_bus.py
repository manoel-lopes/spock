import logging
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable

logger = logging.getLogger(__name__)


@dataclass
class DomainEvent:
    name: str
    payload: dict[str, Any]


EventHandler = Callable[[DomainEvent], None]


class EventBus:
    def __init__(self) -> None:
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)

    def subscribe(self, event_name: str, handler: EventHandler) -> None:
        self._handlers[event_name].append(handler)
        logger.info("Subscribed handler to event '%s'", event_name)

    def publish(self, event: DomainEvent) -> None:
        handlers = self._handlers.get(event.name, [])
        logger.info("Publishing event '%s' to %d handler(s)", event.name, len(handlers))
        for handler in handlers:
            try:
                handler(event)
            except Exception:
                logger.exception("Handler failed for event '%s'", event.name)
