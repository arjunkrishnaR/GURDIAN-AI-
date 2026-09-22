"""Unit tests for guardian.monitoring.system module."""

import asyncio
import pytest

from guardian.events.models import EventSource
from guardian.monitoring.system import SystemCollector


def test_system_collector_lifecycle():
    """Verify SystemCollector active event emission."""
    async def run():
        collector = SystemCollector()
        await collector.start()

        events = await collector.collect_safe()
        assert len(events) == 1
        assert events[0].source == EventSource.SYSTEM
        assert events[0].event_type == "SYSTEM_MONITOR_ACTIVE"

        # Subsequent collection does not duplicate active event
        e2 = await collector.collect_safe()
        assert len(e2) == 0

        await collector.stop()

    asyncio.run(run())
