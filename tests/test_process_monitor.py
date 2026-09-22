"""Unit tests for guardian.monitoring.process module."""

import asyncio
import pytest

from guardian.events.models import EventSource
from guardian.monitoring.process import MockProcessProvider, ProcessCollector


def test_process_collector_lifecycle_detection():
    """Verify ProcessCollector detects newly started and stopped processes."""
    async def run():
        provider = MockProcessProvider(
            mock_processes=[
                {"pid": 101, "name": "system.exe", "start_time": 0.0},
                {"pid": 102, "name": "svchost.exe", "start_time": 0.0},
            ]
        )
        collector = ProcessCollector(poll_interval_seconds=1.0, provider=provider)

        await collector.start()

        # First collection populates initial snapshot without emitting flood events
        e1 = await collector.collect_safe()
        assert len(e1) == 0

        # Simulate process 102 stopping and process 103 starting
        provider.mock_processes = [
            {"pid": 101, "name": "system.exe", "start_time": 0.0},
            {"pid": 103, "name": "app.exe", "start_time": 0.0},
        ]

        e2 = await collector.collect_safe()
        assert len(e2) == 2

        event_types = [e.event_type for e in e2]
        assert "PROCESS_STARTED" in event_types
        assert "PROCESS_STOPPED" in event_types

        # Verify privacy: raw_payload is None and no command line / memory collected
        for e in e2:
            assert e.source == EventSource.PROCESS
            assert e.raw_payload is None
            assert "cmdline" not in e.source_metadata
            assert "memory" not in e.source_metadata

        await collector.stop()

    asyncio.run(run())


def test_pid_reuse_handling():
    """Verify process key (PID, name, start_time) distinguishes reused PIDs with different process names/start times."""
    async def run():
        provider = MockProcessProvider(
            mock_processes=[
                {"pid": 500, "name": "old_proc.exe", "start_time": 100.0},
            ]
        )
        collector = ProcessCollector(provider=provider)

        await collector.start()
        await collector.collect_safe()  # Populate initial snapshot

        # PID 500 is reused by a new binary with start_time 200.0
        provider.mock_processes = [
            {"pid": 500, "name": "new_proc.exe", "start_time": 200.0},
        ]

        events = await collector.collect_safe()
        assert len(events) == 2
        event_types = [e.event_type for e in events]
        assert "PROCESS_STOPPED" in event_types
        assert "PROCESS_STARTED" in event_types

        await collector.stop()

    asyncio.run(run())
