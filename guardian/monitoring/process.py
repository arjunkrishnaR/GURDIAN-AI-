"""Process lifecycle monitor detecting process start and stop events with PID reuse handling."""

import asyncio
import os
import sys
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

from guardian.events.models import EventCategory, EventSource, RawEvent, Severity
from guardian.monitoring.base import EventCollector
from guardian.monitoring.exceptions import ProcessMonitoringError


class IProcessProvider(ABC):
    """Abstract interface for querying active system processes cleanly."""

    @abstractmethod
    def get_running_processes(self) -> List[Dict[str, Any]]:
        """Return list of current running processes with PID, name, and optional start_time."""
        pass


class NativeProcessProvider(IProcessProvider):
    """
    Standard library & native process list provider.
    
    Security / Privacy Contract:
    - Queries PID and executable name ONLY.
    - Never collects command line arguments, environment variables, memory contents, or user data.
    """

    def get_running_processes(self) -> List[Dict[str, Any]]:
        if sys.platform != "win32":
            return []

        processes = []
        try:
            import subprocess
            cmd = ["tasklist.exe", "/FO", "CSV", "/NH"]
            res = subprocess.run(
                cmd,
                shell=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=3.0,
                text=True,
                encoding="utf-8",
                errors="replace"
            )

            if res.returncode == 0:
                for line in res.stdout.splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    parts = [p.strip('"') for p in line.split('","')]
                    if len(parts) >= 2:
                        name = parts[0]
                        pid_str = parts[1]
                        if pid_str.isdigit():
                            processes.append({
                                "pid": int(pid_str),
                                "name": name,
                                "start_time": 0.0  # Limitation: tasklist.exe CSV does not expose start_time
                            })
        except Exception:
            pass

        return processes


class MockProcessProvider(IProcessProvider):
    """Deterministic mock process provider for unit testing without OS side effects."""

    def __init__(self, mock_processes: Optional[List[Dict[str, Any]]] = None) -> None:
        self.mock_processes = mock_processes or []

    def get_running_processes(self) -> List[Dict[str, Any]]:
        return list(self.mock_processes)


class ProcessCollector(EventCollector):
    """
    Collector for process lifecycle events (PROCESS_STARTED, PROCESS_STOPPED).
    
    Features:
    - Process snapshot diffing.
    - Composite process key (PID, name, start_time) to handle PID recycling.
    - Strict privacy (no memory/cmdline/credential scanning).
    """

    def __init__(
        self,
        poll_interval_seconds: float = 2.0,
        provider: Optional[IProcessProvider] = None
    ) -> None:
        super().__init__("ProcessCollector")
        self.poll_interval_seconds = poll_interval_seconds
        self.provider = provider or NativeProcessProvider()
        self._previous_snapshot: Dict[Tuple[int, str, float], Dict[str, Any]] = {}

    async def _on_start(self) -> None:
        self._previous_snapshot.clear()

    async def _on_stop(self) -> None:
        self._previous_snapshot.clear()

    async def _collect_impl(self) -> List[RawEvent]:
        loop = asyncio.get_running_loop()
        try:
            current_list = await loop.run_in_executor(None, self.provider.get_running_processes)
        except Exception as e:
            self._record_error(f"Error querying process snapshot: {e}")
            return []

        current_snapshot: Dict[Tuple[int, str, float], Dict[str, Any]] = {}
        for p in current_list:
            pid = int(p.get("pid", 0))
            name = str(p.get("name", "unknown"))
            start_time = float(p.get("start_time", 0.0))
            key = (pid, name, start_time)
            current_snapshot[key] = p

        raw_events: List[RawEvent] = []

        # If initial run, populate snapshot without firing flood of started events
        if not self._previous_snapshot:
            self._previous_snapshot = current_snapshot
            return []

        # Detect newly started processes
        for key, pdata in current_snapshot.items():
            if key not in self._previous_snapshot:
                pid, name, _ = key
                raw_events.append(
                    RawEvent(
                        source=EventSource.PROCESS,
                        timestamp=datetime.now(timezone.utc),
                        raw_payload=None,
                        source_metadata={
                            "process_id": pid,
                            "process_name": name,
                            "event_type": "PROCESS_STARTED",
                            "category": "INFORMATION",
                            "severity": "INFO",
                            "title": f"Process Started: {name}",
                            "description": f"Process {name} (PID {pid}) started.",
                        },
                        event_type="PROCESS_STARTED"
                    )
                )

        # Detect stopped processes
        for key, pdata in self._previous_snapshot.items():
            if key not in current_snapshot:
                pid, name, _ = key
                raw_events.append(
                    RawEvent(
                        source=EventSource.PROCESS,
                        timestamp=datetime.now(timezone.utc),
                        raw_payload=None,
                        source_metadata={
                            "process_id": pid,
                            "process_name": name,
                            "event_type": "PROCESS_STOPPED",
                            "category": "INFORMATION",
                            "severity": "INFO",
                            "title": f"Process Stopped: {name}",
                            "description": f"Process {name} (PID {pid}) stopped.",
                        },
                        event_type="PROCESS_STOPPED"
                    )
                )

        self._previous_snapshot = current_snapshot
        return raw_events
