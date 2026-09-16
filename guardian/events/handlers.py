"""Event handler abstractions and test implementation."""

from abc import ABC, abstractmethod
from typing import List, Protocol, runtime_checkable

from guardian.events.models import GuardianEvent


@runtime_checkable
class EventHandler(Protocol):
    """Protocol defining standard asynchronous event handler interface."""

    async def handle(self, event: GuardianEvent) -> None:
        """Process incoming normalized GuardianEvent."""
        ...


class BaseEventHandler(ABC):
    """Abstract base class for all GuardianAI event handlers."""

    @abstractmethod
    async def handle(self, event: GuardianEvent) -> None:
        """Process incoming normalized GuardianEvent."""
        pass


class TestEventHandler(BaseEventHandler):
    """Deterministic test handler recording processed events and supporting artificial failures."""
    __test__ = False

    def __init__(self, name: str = "TestEventHandler", should_raise: bool = False) -> None:
        self.name = name
        self.should_raise = should_raise
        self.received_events: List[GuardianEvent] = []

    async def handle(self, event: GuardianEvent) -> None:
        """Process event by appending to received list or raising test exception."""
        if self.should_raise:
            raise RuntimeError(f"Handler '{self.name}' simulated failure for event '{event.event_id}'.")
        self.received_events.append(event)
