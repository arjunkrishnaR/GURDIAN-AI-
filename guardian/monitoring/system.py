"""System level telemetry collector for system startup, shutdown, and status observation."""

import asyncio
from datetime import datetime, timezone
from typing import List, Optional

from guardian.events.models import EventSource, RawEvent
from guardian.monitoring.base import EventCollector


class SystemCollector(EventCollector):
    """
    Strictly read-only system telemetry collector.
    
    Observes system startup, shutdown, and critical service state telemetry.
    Never modifies, starts, stops, or configures Windows services.
    """

    def __init__(self) -> None:
        super().__init__("SystemCollector")
        self._startup_emitted = False

    async def _on_start(self) -> None:
        self._startup_emitted = False

    async def _on_stop(self) -> None:
        self._startup_emitted = False

    async def _collect_impl(self) -> List[RawEvent]:
        events: List[RawEvent] = []

        if not self._startup_emitted:
            events.append(
                RawEvent(
                    source=EventSource.SYSTEM,
                    timestamp=datetime.now(timezone.utc),
                    raw_payload=None,
                    source_metadata={
                        "event_type": "SYSTEM_MONITOR_ACTIVE",
                        "category": "INFORMATION",
                        "severity": "INFO",
                        "title": "System Monitoring Active",
                        "description": "GuardianAI system observer initialized and monitoring environment.",
                    },
                    event_type="SYSTEM_MONITOR_ACTIVE"
                )
            )
            self._startup_emitted = True

        return events
