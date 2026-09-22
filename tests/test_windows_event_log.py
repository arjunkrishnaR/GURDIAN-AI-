"""Unit tests for guardian.monitoring.windows_event_log module."""

import asyncio
import pytest
from datetime import datetime, timezone

from guardian.events.models import EventSource, RawEvent
from guardian.monitoring.windows_event_log import (
    MockWindowsEventLogProvider,
    SubprocessWevtutilProvider,
    WindowsEventLogCollector,
)


def test_mock_windows_event_log_collector():
    """Verify WindowsEventLogCollector with mock provider produces normalized RawEvents."""
    async def run():
        mock_data = [
            {
                "channel": "Application",
                "provider": "TestApp",
                "event_id": "1000",
                "level": "2",
                "record_id": "501",
                "timestamp": "2026-09-16T12:00:00Z",
            },
            {
                "channel": "System",
                "provider": "ServiceControlManager",
                "event_id": "7036",
                "level": "4",
                "record_id": "902",
                "timestamp": "2026-09-16T12:01:00Z",
            }
        ]

        provider = MockWindowsEventLogProvider(mock_events=mock_data)
        collector = WindowsEventLogCollector(channels=["Application", "System"], provider=provider)

        await collector.start()
        events = await collector.collect_safe()

        assert len(events) == 2
        assert events[0].source == EventSource.WINDOWS
        assert events[0].source_metadata["channel"] == "Application"
        assert events[0].source_metadata["provider"] == "TestApp"
        assert events[0].source_metadata["event_id"] == "1000"
        # Verify privacy: raw_payload is None by default
        assert events[0].raw_payload is None

        await collector.stop()

    asyncio.run(run())


def test_bounded_deduplication():
    """Verify duplicate event records are skipped by deduplication cache."""
    async def run():
        mock_data = [
            {
                "channel": "Application",
                "provider": "TestApp",
                "event_id": "1000",
                "level": "2",
                "record_id": "501",
                "timestamp": "2026-09-16T12:00:00Z",
            }
        ]

        provider = MockWindowsEventLogProvider(mock_events=mock_data)
        collector = WindowsEventLogCollector(channels=["Application"], provider=provider, max_dedup_cache=10)

        await collector.start()

        # First collection run returns the event
        e1 = await collector.collect_safe()
        assert len(e1) == 1

        # Second collection run with identical event parameters gets deduplicated (returns empty list)
        e2 = await collector.collect_safe()
        assert len(e2) == 0

        await collector.stop()

    asyncio.run(run())


def test_subprocess_provider_xml_parsing():
    """Verify XML parsing helper in SubprocessWevtutilProvider."""
    provider = SubprocessWevtutilProvider()
    xml_data = """
    <Event xmlns="http://schemas.microsoft.com/win/2004/08/events/event">
        <System>
            <Provider Name="Application Error"/>
            <EventID>1000</EventID>
            <Level>2</Level>
            <TimeCreated SystemTime="2026-09-16T10:00:00.0000000Z"/>
            <EventRecordID>12345</EventRecordID>
        </System>
    </Event>
    """
    records = provider._parse_xml_output(xml_data, "Application")
    assert len(records) == 1
    assert records[0]["provider"] == "Application Error"
    assert records[0]["event_id"] == "1000"
    assert records[0]["record_id"] == "12345"
