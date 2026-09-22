"""Unit tests for guardian.monitoring.base module."""

import asyncio
import pytest
from typing import List

from guardian.events.models import RawEvent
from guardian.monitoring.base import CollectorState, EventCollector
from guardian.monitoring.exceptions import CollectorError


class DummyCollector(EventCollector):
    """Dummy collector implementation for testing base class semantics."""

    def __init__(self, name: str = "DummyCollector", fail_collect: bool = False) -> None:
        super().__init__(name)
        self.fail_collect = fail_collect
        self.started = False
        self.stopped = False

    async def _on_start(self) -> None:
        self.started = True

    async def _on_stop(self) -> None:
        self.stopped = True

    async def _collect_impl(self) -> List[RawEvent]:
        if self.fail_collect:
            raise RuntimeError("Simulated collection failure.")
        return []


def test_collector_initial_state():
    """Verify collector initial state and properties."""
    c = DummyCollector("TestCollector")
    assert c.name == "TestCollector"
    assert c.state == CollectorState.STOPPED
    assert c.is_running is False
    assert c.error_count == 0
    assert c.last_error is None


def test_collector_lifecycle_transitions():
    """Verify collector start, pause, resume, stop lifecycle transitions."""
    async def run():
        c = DummyCollector("TestCollector")
        assert c.state == CollectorState.STOPPED

        await c.start()
        assert c.state == CollectorState.RUNNING
        assert c.is_running is True
        assert c.started is True

        c.pause()
        assert c.state == CollectorState.PAUSED
        assert c.is_running is False

        c.resume()
        assert c.state == CollectorState.RUNNING
        assert c.is_running is True

        await c.stop()
        assert c.state == CollectorState.STOPPED
        assert c.is_running is False
        assert c.stopped is True

    asyncio.run(run())


def test_collector_idempotency():
    """Verify repeated lifecycle method calls are idempotent and safe."""
    async def run():
        c = DummyCollector("IdempotentCollector")

        # Repeated start
        await c.start()
        await c.start()
        assert c.state == CollectorState.RUNNING

        # Repeated pause
        c.pause()
        c.pause()
        assert c.state == CollectorState.PAUSED

        # Repeated resume
        c.resume()
        c.resume()
        assert c.state == CollectorState.RUNNING

        # Repeated stop
        await c.stop()
        await c.stop()
        assert c.state == CollectorState.STOPPED

    asyncio.run(run())


def test_collector_error_isolation():
    """Verify collect_safe catches exceptions, increments error count, sets ERROR state, and returns []."""
    async def run():
        c = DummyCollector("FailingCollector", fail_collect=True)
        await c.start()
        assert c.state == CollectorState.RUNNING

        # Collect safe should handle error without raising exception
        events = await c.collect_safe()
        assert events == []
        assert c.state == CollectorState.ERROR
        assert c.error_count == 1
        assert "Simulated collection failure" in str(c.last_error)

    asyncio.run(run())
