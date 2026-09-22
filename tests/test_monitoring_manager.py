"""Unit tests for guardian.monitoring.manager module."""

import asyncio
import pytest
from typing import List

from guardian.events.bus import EventBus
from guardian.events.handlers import TestEventHandler
from guardian.events.models import EventSource, RawEvent
from guardian.events.normalizer import EventNormalizer
from guardian.monitoring.base import CollectorState, EventCollector
from guardian.monitoring.manager import MonitoringManager, MonitoringState
from guardian.monitoring.windows_event_log import MockWindowsEventLogProvider, WindowsEventLogCollector
from guardian.monitoring.process import MockProcessProvider, ProcessCollector
from guardian.monitoring.system import SystemCollector


class FailingCollector(EventCollector):
    """Failing collector for testing error isolation and degraded health state."""

    def __init__(self) -> None:
        super().__init__("FailingCollector")

    async def _on_start(self) -> None:
        pass

    async def _on_stop(self) -> None:
        pass

    async def _collect_impl(self) -> List[RawEvent]:
        raise RuntimeError("Collector internal error.")


def test_manager_lifecycle_and_idempotency():
    """Verify MonitoringManager full lifecycle and idempotency of pause/resume/stop."""
    async def run():
        mock_wel = MockWindowsEventLogProvider()
        mock_proc = MockProcessProvider()

        collectors = [
            WindowsEventLogCollector(provider=mock_wel),
            ProcessCollector(provider=mock_proc),
            SystemCollector(),
        ]

        mgr = MonitoringManager(collectors=collectors)
        assert mgr.state == MonitoringState.STOPPED
        assert mgr.health_condition == "STOPPED"

        # Start
        await mgr.start()
        assert mgr.state == MonitoringState.RUNNING
        assert mgr.health_condition == "HEALTHY"

        # Repeated start (idempotent)
        await mgr.start()
        assert mgr.state == MonitoringState.RUNNING

        # Pause
        await mgr.pause()
        assert mgr.state == MonitoringState.PAUSED

        # Repeated pause (idempotent)
        await mgr.pause()
        assert mgr.state == MonitoringState.PAUSED

        # Resume
        await mgr.resume()
        assert mgr.state == MonitoringState.RUNNING

        # Repeated resume (idempotent)
        await mgr.resume()
        assert mgr.state == MonitoringState.RUNNING

        # Stop & repeated stop
        await mgr.stop()
        await mgr.stop()
        await mgr.stop()
        assert mgr.state == MonitoringState.STOPPED
        assert mgr._worker_task is None

    asyncio.run(run())


def test_manager_degraded_health_state():
    """Verify manager health_condition becomes DEGRADED when one collector fails while others run."""
    async def run():
        mock_wel = MockWindowsEventLogProvider()

        good_collector = WindowsEventLogCollector(provider=mock_wel)
        failing_collector = FailingCollector()

        mgr = MonitoringManager(collectors=[good_collector, failing_collector])
        await mgr.start()

        # Execute loop iteration
        await failing_collector.collect_safe()
        assert failing_collector.state == CollectorState.ERROR
        assert good_collector.state == CollectorState.RUNNING

        assert mgr.health_condition == "DEGRADED"

        await mgr.stop()

    asyncio.run(run())


def test_end_to_end_event_pipeline():
    """Verify complete pipeline: Collector -> RawEvent -> EventNormalizer -> GuardianEvent -> EventBus -> Handler."""
    async def run():
        mock_wel = MockWindowsEventLogProvider(
            mock_events=[
                {
                    "channel": "Application",
                    "provider": "FaultingApp",
                    "event_id": "1000",
                    "level": "2",
                    "record_id": "88",
                    "timestamp": "2026-09-16T15:00:00Z",
                }
            ]
        )

        wel_collector = WindowsEventLogCollector(channels=["Application"], provider=mock_wel)
        bus = EventBus()
        handler = TestEventHandler("PipelineHandler")
        bus.subscribe(handler)

        mgr = MonitoringManager(bus=bus, collectors=[wel_collector])
        await mgr.start()

        # Allow worker loop iteration
        await asyncio.sleep(0.1)

        assert len(handler.received_events) >= 1
        received = handler.received_events[0]
        assert received.source == EventSource.WINDOWS
        assert received.event_type == "WIN_EVENT_1000"

        await mgr.stop()

    asyncio.run(run())
