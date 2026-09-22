"""Central monitoring manager orchestrating collectors, background tasks, and event pipeline."""

import asyncio
from enum import Enum, auto
from typing import Dict, List, Optional

from guardian.core.config import GuardianConfig, load_config
from guardian.events.bus import EventBus
from guardian.events.models import GuardianEvent, RawEvent
from guardian.events.normalizer import EventNormalizer
from guardian.logging.logger import get_logger
from guardian.monitoring.base import CollectorState, EventCollector
from guardian.monitoring.exceptions import MonitoringError
from guardian.monitoring.process import ProcessCollector
from guardian.monitoring.system import SystemCollector
from guardian.monitoring.windows_event_log import WindowsEventLogCollector


class MonitoringState(Enum):
    """Lifecycle states for the monitoring manager runtime."""
    STOPPED = auto()
    STARTING = auto()
    RUNNING = auto()
    PAUSED = auto()
    STOPPING = auto()
    ERROR = auto()


class MonitoringManager:
    """
    Central manager for Windows monitoring collectors.
    
    Responsibilities:
    - Background task ownership (tracks and cancels worker asyncio.Task).
    - Pipeline orchestration: Collector -> RawEvent -> EventNormalizer -> GuardianEvent -> EventBus.publish().
    - Isolated error handling & degraded health reporting.
    - Idempotent lifecycle transitions (start, pause, resume, stop).
    """

    def __init__(
        self,
        config: Optional[GuardianConfig] = None,
        normalizer: Optional[EventNormalizer] = None,
        bus: Optional[EventBus] = None,
        collectors: Optional[List[EventCollector]] = None
    ) -> None:
        self._config = config or load_config()
        self._normalizer = normalizer or EventNormalizer()
        self._bus = bus or EventBus()
        self._logger = get_logger()

        self._state = MonitoringState.STOPPED
        self._worker_task: Optional[asyncio.Task] = None

        # Statistics
        self.events_collected = 0
        self.events_normalized = 0
        self.events_published = 0
        self.collector_errors = 0

        # Collectors
        if collectors is not None:
            self._collectors = collectors
        else:
            self._collectors = [
                WindowsEventLogCollector(channels=self._config.win_event_log_channels),
                ProcessCollector(poll_interval_seconds=self._config.process_poll_interval),
                SystemCollector(),
            ]

    @property
    def state(self) -> MonitoringState:
        """Return current monitoring lifecycle state."""
        return self._state

    @property
    def health_condition(self) -> str:
        """
        Evaluate monitoring health condition string ('HEALTHY', 'DEGRADED', 'FAILED').
        
        Note: Health condition is separate from lifecycle state.
        """
        if self._state == MonitoringState.ERROR:
            return "FAILED"
        if self._state == MonitoringState.STOPPED:
            return "STOPPED"

        active_states = [c.state for c in self._collectors]
        if not active_states:
            return "HEALTHY"

        has_running = any(s == CollectorState.RUNNING for s in active_states)
        has_error = any(s == CollectorState.ERROR for s in active_states)

        if has_running and has_error:
            return "DEGRADED"
        elif has_error and not has_running:
            return "FAILED"
        return "HEALTHY"

    @property
    def collectors(self) -> List[EventCollector]:
        """Return list of managed collectors."""
        return self._collectors

    def get_collector_status(self) -> Dict[str, str]:
        """Return dict of collector names mapped to their state string."""
        return {c.name: c.state.name for c in self._collectors}

    async def start(self) -> None:
        """Start monitoring manager runtime and background worker task idempotently."""
        if self._state == MonitoringState.RUNNING:
            return

        self._state = MonitoringState.STARTING
        self._logger.info("Starting MonitoringManager...")

        # Start all collectors
        for collector in self._collectors:
            try:
                await collector.start()
            except Exception as e:
                self.collector_errors += 1
                self._logger.error("Error starting collector '%s': %s", collector.name, e)

        self._state = MonitoringState.RUNNING

        # Spawn background loop task owned by MonitoringManager
        if self._worker_task is None or self._worker_task.done():
            self._worker_task = asyncio.create_task(self._run_monitoring_loop())

        self._logger.info("MonitoringManager started successfully (State: RUNNING, Health: %s).", self.health_condition)

    async def pause(self) -> None:
        """Pause monitoring collectors idempotently."""
        if self._state != MonitoringState.RUNNING:
            return

        self._state = MonitoringState.PAUSED
        for collector in self._collectors:
            collector.pause()

        self._logger.info("MonitoringManager paused.")

    async def resume(self) -> None:
        """Resume monitoring collectors idempotently."""
        if self._state != MonitoringState.PAUSED:
            return

        for collector in self._collectors:
            collector.resume()

        self._state = MonitoringState.RUNNING
        self._logger.info("MonitoringManager resumed.")

    async def stop(self) -> None:
        """
        Stop monitoring manager, cancel background tasks, and release resources.
        
        Idempotent and safe for repeated invocation: stop(); stop(); stop().
        """
        if self._state == MonitoringState.STOPPED:
            return

        self._state = MonitoringState.STOPPING
        self._logger.info("Stopping MonitoringManager...")

        # 1. Cancel background worker task
        if self._worker_task is not None and not self._worker_task.done():
            self._worker_task.cancel()
            try:
                await asyncio.wait_for(asyncio.shield(self._worker_task), timeout=2.0)
            except (asyncio.CancelledError, asyncio.TimeoutError, Exception):
                pass
            self._worker_task = None

        # 2. Stop all sub-collectors
        for collector in self._collectors:
            try:
                await collector.stop()
            except Exception as e:
                self._logger.error("Error stopping collector '%s': %s", collector.name, e)

        self._state = MonitoringState.STOPPED
        self._logger.info("MonitoringManager stopped cleanly.")

    async def _run_monitoring_loop(self) -> None:
        """Background worker loop polling collectors and feeding the Phase 2 pipeline."""
        self._logger.debug("Entering background monitoring worker loop...")
        while self._state in (MonitoringState.RUNNING, MonitoringState.PAUSED):
            try:
                if self._state == MonitoringState.RUNNING:
                    for collector in self._collectors:
                        if collector.is_running:
                            raw_events = await collector.collect_safe()
                            self.events_collected += len(raw_events)
                            if collector.state == CollectorState.ERROR:
                                self.collector_errors += 1

                            for raw_evt in raw_events:
                                try:
                                    guardian_evt = self._normalizer.normalize(raw_evt)
                                    self.events_normalized += 1
                                    matching_count = await self._bus.publish(guardian_evt)
                                    if matching_count > 0:
                                        self.events_published += 1
                                except Exception as e:
                                    self._logger.error("Error normalizing/publishing event: %s", e)

                # Poll interval loop sleep
                await asyncio.sleep(self._config.process_poll_interval)
            except asyncio.CancelledError:
                self._logger.debug("Background monitoring loop cancelled.")
                break
            except Exception as e:
                self._logger.error("Unexpected error in monitoring worker loop: %s", e, exc_info=True)
                await asyncio.sleep(1.0)
