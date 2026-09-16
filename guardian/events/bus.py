"""Asynchronous event bus with concurrent dispatch, filtering, and failure isolation."""

import asyncio
from dataclasses import dataclass, field
from typing import List, Optional, Set, Tuple, Union

from guardian.events.handlers import EventHandler
from guardian.events.models import GuardianEvent, Severity
from guardian.logging.logger import get_logger


@dataclass
class Subscription:
    """Subscription rule mapping an EventHandler to optional event_type and severity filters."""
    handler: EventHandler
    event_type: Optional[str] = None
    severity: Optional[Severity] = None

    def matches(self, event: GuardianEvent) -> bool:
        """Check if subscription filters match incoming GuardianEvent."""
        if self.event_type and self.event_type != event.event_type:
            return False
        if self.severity and self.severity != event.severity:
            return False
        return True


@dataclass
class EventBusStats:
    """Statistics tracking for EventBus activity."""
    total_published: int = 0
    total_handled: int = 0
    total_failures: int = 0


class EventBus:
    """
    Asynchronous event bus for dispatching GuardianEvents to registered handlers.
    
    Provides concurrent handler dispatch, filter matching, handler failure isolation,
    and runtime statistics tracking.
    """

    def __init__(self, handler_timeout: Optional[float] = 5.0) -> None:
        self._subscriptions: List[Subscription] = []
        self._stats = EventBusStats()
        self._logger = get_logger()
        self._handler_timeout = handler_timeout

    @property
    def stats(self) -> EventBusStats:
        """Return current EventBus statistics."""
        return self._stats

    def subscribe(
        self,
        handler: EventHandler,
        event_type: Optional[str] = None,
        severity: Optional[Union[Severity, str]] = None
    ) -> None:
        """
        Subscribe an EventHandler with optional event_type and severity filters.
        
        Prevents duplicate registrations for the same handler and filter criteria.
        """
        sev_enum: Optional[Severity] = None
        if isinstance(severity, Severity):
            sev_enum = severity
        elif isinstance(severity, str):
            sev_enum = Severity[severity.strip().upper()]

        # Prevent duplicate exact subscription
        for sub in self._subscriptions:
            if sub.handler == handler and sub.event_type == event_type and sub.severity == sev_enum:
                self._logger.debug("Duplicate subscription request ignored for handler: %s", handler)
                return

        subscription = Subscription(handler=handler, event_type=event_type, severity=sev_enum)
        self._subscriptions.append(subscription)
        self._logger.info(
            "Registered event handler '%s' (Filter: event_type=%s, severity=%s)",
            getattr(handler, "name", type(handler).__name__),
            event_type,
            sev_enum.value if sev_enum else None
        )

    def unsubscribe(
        self,
        handler: EventHandler,
        event_type: Optional[str] = None,
        severity: Optional[Union[Severity, str]] = None
    ) -> bool:
        """Unsubscribe an EventHandler matching filter parameters cleanly."""
        sev_enum: Optional[Severity] = None
        if isinstance(severity, Severity):
            sev_enum = severity
        elif isinstance(severity, str):
            sev_enum = Severity[severity.strip().upper()]

        initial_len = len(self._subscriptions)
        self._subscriptions = [
            sub for sub in self._subscriptions
            if not (sub.handler == handler and (event_type is None or sub.event_type == event_type) and (severity is None or sub.severity == sev_enum))
        ]

        removed = initial_len > len(self._subscriptions)
        if removed:
            self._logger.info("Unsubscribed event handler '%s'", getattr(handler, "name", type(handler).__name__))
        return removed

    async def _execute_handler_safe(self, sub: Subscription, event: GuardianEvent) -> bool:
        """Execute a single handler safely with timeout and error isolation."""
        handler_name = getattr(sub.handler, "name", type(sub.handler).__name__)
        try:
            if self._handler_timeout and self._handler_timeout > 0:
                await asyncio.wait_for(sub.handler.handle(event), timeout=self._handler_timeout)
            else:
                await sub.handler.handle(event)
            return True
        except asyncio.TimeoutError:
            self._logger.error(
                "Handler '%s' timed out after %.2fs while processing event '%s'",
                handler_name, self._handler_timeout, event.event_id
            )
            return False
        except Exception as e:
            self._logger.error(
                "Handler '%s' failed while processing event '%s': %s",
                handler_name, event.event_id, e, exc_info=True
            )
            return False

    async def publish(self, event: GuardianEvent) -> int:
        """
        Publish a GuardianEvent to all matching subscribed handlers concurrently.
        
        Returns count of matching handlers dispatched.
        """
        self._stats.total_published += 1
        matching_subs = [sub for sub in self._subscriptions if sub.matches(event)]

        if not matching_subs:
            self._logger.debug("Published event '%s' (%s) with no matching subscribers.", event.event_id, event.event_type)
            return 0

        self._logger.debug(
            "Publishing event '%s' (%s) to %d matching handler(s)...",
            event.event_id, event.event_type, len(matching_subs)
        )

        # Dispatch handlers concurrently
        tasks = [self._execute_handler_safe(sub, event) for sub in matching_subs]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for res in results:
            if res is True:
                self._stats.total_handled += 1
            else:
                self._stats.total_failures += 1

        return len(matching_subs)
