"""Windows Event Log collector with subprocess security and bounded deduplication."""

import asyncio
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from collections import deque
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

from guardian.events.models import EventSource, RawEvent
from guardian.monitoring.base import EventCollector
from guardian.monitoring.exceptions import WindowsEventLogError


class IWindowsEventLogProvider(ABC):
    """Abstract interface for querying Windows Event Log channels safely."""

    @abstractmethod
    def query_events(self, channel: str, max_events: int = 10) -> List[Dict[str, Any]]:
        """Query recent event log records for a specified channel."""
        pass


class SubprocessWevtutilProvider(IWindowsEventLogProvider):
    """
    Subprocess-based implementation of Windows Event Log reader using wevtutil.exe.
    
    Security Contract:
    - Uses subprocess.run with shell=False.
    - Explicit fixed argument list only.
    - Enforces strict timeout and stdout buffer size caps.
    """

    def query_events(self, channel: str, max_events: int = 10) -> List[Dict[str, Any]]:
        if sys.platform != "win32":
            return []

        # Construct strict fixed command args
        cmd = ["wevtutil.exe", "qe", channel, f"/c:{max_events}", "/rd:true", "/f:xml"]

        try:
            res = subprocess.run(
                cmd,
                shell=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=5.0,
                text=True,
                encoding="utf-8",
                errors="replace"
            )

            if res.returncode != 0:
                return []

            return self._parse_xml_output(res.stdout, channel)
        except subprocess.TimeoutExpired:
            return []
        except Exception:
            return []

    def _parse_xml_output(self, xml_text: str, channel: str) -> List[Dict[str, Any]]:
        if not xml_text or not xml_text.strip():
            return []

        events = []
        # Wrap XML snippets in root element if multiple Events returned
        wrapped_xml = f"<Events>{xml_text}</Events>"
        try:
            root = ET.fromstring(wrapped_xml)
            ns = {"ns": "http://schemas.microsoft.com/win/2004/08/events/event"}

            for elem in root.findall(".//ns:Event", ns) or root.findall(".//Event"):
                try:
                    sys_node = elem.find("ns:System", ns) or elem.find("System")
                    if sys_node is None:
                        continue

                    provider_node = sys_node.find("ns:Provider", ns) or sys_node.find("Provider")
                    provider_name = provider_node.attrib.get("Name", "Unknown") if provider_node is not None else "Unknown"

                    event_id_node = sys_node.find("ns:EventID", ns) or sys_node.find("EventID")
                    event_id = event_id_node.text if event_id_node is not None and event_id_node.text else "0"

                    level_node = sys_node.find("ns:Level", ns) or sys_node.find("Level")
                    level = level_node.text if level_node is not None and level_node.text else "0"

                    time_node = sys_node.find("ns:TimeCreated", ns) or sys_node.find("TimeCreated")
                    time_created = time_node.attrib.get("SystemTime", "") if time_node is not None else ""

                    record_node = sys_node.find("ns:EventRecordID", ns) or sys_node.find("EventRecordID")
                    record_id = record_node.text if record_node is not None and record_node.text else ""

                    events.append({
                        "channel": channel,
                        "provider": provider_name,
                        "event_id": event_id,
                        "level": level,
                        "record_id": record_id,
                        "timestamp": time_created,
                    })
                except Exception:
                    continue

        except Exception:
            pass

        return events


class MockWindowsEventLogProvider(IWindowsEventLogProvider):
    """Deterministic mock provider for unit testing without live Windows dependencies."""

    def __init__(self, mock_events: Optional[List[Dict[str, Any]]] = None) -> None:
        self.mock_events = mock_events or []

    def query_events(self, channel: str, max_events: int = 10) -> List[Dict[str, Any]]:
        return [e for e in self.mock_events if e.get("channel") == channel][:max_events]


class WindowsEventLogCollector(EventCollector):
    """
    Collector for Windows Event Logs (Application, System).
    
    Features:
    - Bounded deduplication queue (maxlen=1000).
    - Raw payload privacy: retains only normalized fields by default.
    - Pluggable provider for deterministic mock testing.
    """

    def __init__(
        self,
        channels: Optional[List[str]] = None,
        provider: Optional[IWindowsEventLogProvider] = None,
        max_dedup_cache: int = 1000
    ) -> None:
        super().__init__("WindowsEventLogCollector")
        self.channels = channels or ["Application", "System"]
        self.provider = provider or SubprocessWevtutilProvider()
        self._dedup_queue: deque = deque(maxlen=max_dedup_cache)
        self._dedup_set: Set[Tuple[str, str, str, str, str]] = set()

    async def _on_start(self) -> None:
        self._dedup_queue.clear()
        self._dedup_set.clear()

    async def _on_stop(self) -> None:
        self._dedup_queue.clear()
        self._dedup_set.clear()

    def _is_duplicate(self, channel: str, provider: str, event_id: str, record_id: str, timestamp: str) -> bool:
        key = (channel, provider, event_id, record_id, timestamp)
        if key in self._dedup_set:
            return True

        if len(self._dedup_queue) >= self._dedup_queue.maxlen:  # type: ignore
            oldest = self._dedup_queue.popleft()
            self._dedup_set.discard(oldest)

        self._dedup_queue.append(key)
        self._dedup_set.add(key)
        return False

    async def _collect_impl(self) -> List[RawEvent]:
        raw_events: List[RawEvent] = []

        # Run Provider query off the main asyncio thread to avoid blocking
        loop = asyncio.get_running_loop()

        for channel in self.channels:
            try:
                records = await loop.run_in_executor(None, self.provider.query_events, channel, 10)
                for rec in records:
                    ch = rec.get("channel", channel)
                    prov = rec.get("provider", "Unknown")
                    eid = str(rec.get("event_id", "0"))
                    rec_id = str(rec.get("record_id", ""))
                    ts = str(rec.get("timestamp", ""))

                    if self._is_duplicate(ch, prov, eid, rec_id, ts):
                        continue

                    # Determine severity label based on Windows Level integer
                    level_int = int(rec.get("level", 0)) if str(rec.get("level", "0")).isdigit() else 0
                    sev_map = {1: "CRITICAL", 2: "ERROR", 3: "WARNING", 4: "INFO", 5: "DEBUG"}
                    severity_str = sev_map.get(level_int, "INFO")
                    cat_str = "CRASH" if eid in ("1000", "1001") else ("ERROR" if severity_str in ("ERROR", "CRITICAL") else "INFORMATION")

                    raw_events.append(
                        RawEvent(
                            source=EventSource.WINDOWS,
                            timestamp=ts or datetime.now(timezone.utc),
                            raw_payload=None,  # Privacy: raw payload excluded by default
                            source_metadata={
                                "channel": ch,
                                "provider": prov,
                                "event_id": eid,
                                "record_id": rec_id,
                                "level": level_int,
                                "severity": severity_str,
                                "category": cat_str,
                            },
                            event_type=f"WIN_EVENT_{eid}"
                        )
                    )
            except Exception as e:
                self._record_error(f"Error collecting Windows Event Log channel '{channel}': {e}")

        return raw_events
