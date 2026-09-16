"""Unit tests for guardian.events.bus module."""

import asyncio
import pytest
from datetime import datetime, timezone
import uuid

from guardian.events.bus import EventBus
from guardian.events.handlers import TestEventHandler
from guardian.events.models import GuardianEvent, EventSource, EventCategory, Severity, make_immutable


@pytest.fixture
def sample_event():
    """Fixture producing a valid GuardianEvent."""
    return GuardianEvent(
        event_id=str(uuid.uuid4()),
        timestamp=datetime.now(timezone.utc),
        source=EventSource.APPLICATION,
        category=EventCategory.ERROR,
        severity=Severity.ERROR,
        event_type="TEST_CRASH",
        title="Test Crash",
        description="Test crash description",
        metadata=make_immutable({"test": True}),
    )


def test_bus_subscribe_publish(sample_event):
    """Verify subscribing a handler and publishing an event."""
    async def run():
        bus = EventBus()
        handler = TestEventHandler("Handler1")
        bus.subscribe(handler)

        dispatched_count = await bus.publish(sample_event)
        assert dispatched_count == 1
        assert len(handler.received_events) == 1
        assert handler.received_events[0].event_id == sample_event.event_id

        assert bus.stats.total_published == 1
        assert bus.stats.total_handled == 1
        assert bus.stats.total_failures == 0

    asyncio.run(run())


def test_bus_unsubscribe(sample_event):
    """Verify unsubscribing a handler stops event delivery."""
    async def run():
        bus = EventBus()
        handler = TestEventHandler("Handler1")
        bus.subscribe(handler)
        assert bus.unsubscribe(handler) is True

        dispatched_count = await bus.publish(sample_event)
        assert dispatched_count == 0
        assert len(handler.received_events) == 0

    asyncio.run(run())


def test_bus_duplicate_subscribe_prevented(sample_event):
    """Verify duplicate exact subscription requests are ignored."""
    async def run():
        bus = EventBus()
        handler = TestEventHandler("Handler1")
        bus.subscribe(handler)
        bus.subscribe(handler)  # Duplicate

        dispatched_count = await bus.publish(sample_event)
        assert dispatched_count == 1
        assert len(handler.received_events) == 1

    asyncio.run(run())


def test_bus_filtering(sample_event):
    """Verify event bus filtering by event_type and severity."""
    async def run():
        bus = EventBus()
        h_matching_type = TestEventHandler("MatchingType")
        h_matching_sev = TestEventHandler("MatchingSev")
        h_non_matching = TestEventHandler("NonMatching")

        bus.subscribe(h_matching_type, event_type="TEST_CRASH")
        bus.subscribe(h_matching_sev, severity=Severity.ERROR)
        bus.subscribe(h_non_matching, event_type="OTHER_EVENT")

        dispatched_count = await bus.publish(sample_event)
        assert dispatched_count == 2
        assert len(h_matching_type.received_events) == 1
        assert len(h_matching_sev.received_events) == 1
        assert len(h_non_matching.received_events) == 0

    asyncio.run(run())


def test_bus_failure_isolation(sample_event):
    """Verify a failing handler does not crash the bus or prevent other handlers from executing."""
    async def run():
        bus = EventBus()
        h_good1 = TestEventHandler("Good1")
        h_failing = TestEventHandler("Failing", should_raise=True)
        h_good2 = TestEventHandler("Good2")

        bus.subscribe(h_good1)
        bus.subscribe(h_failing)
        bus.subscribe(h_good2)

        dispatched_count = await bus.publish(sample_event)
        assert dispatched_count == 3
        assert len(h_good1.received_events) == 1
        assert len(h_good2.received_events) == 1

        assert bus.stats.total_handled == 2
        assert bus.stats.total_failures == 1

    asyncio.run(run())
