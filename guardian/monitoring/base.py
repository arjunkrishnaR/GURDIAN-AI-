"""Base collector contract and collector state machine."""

from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import List, Optional

from guardian.events.models import RawEvent
from guardian.logging.logger import get_logger
from guardian.monitoring.exceptions import CollectorError


class CollectorState(Enum):
    """Possible runtime states for individual telemetry collectors."""
    STOPPED = auto()
    STARTING = auto()
    RUNNING = auto()
    PAUSED = auto()
    ERROR = auto()


class EventCollector(ABC):
    """Abstract base class for all telemetry event collectors."""

    def __init__(self, name: str) -> None:
        self._name = name
        self._state = CollectorState.STOPPED
        self._error_count = 0
        self._last_error: Optional[str] = None
        self._logger = get_logger()

    @property
    def name(self) -> str:
        """Return human-readable collector name."""
        return self._name

    @property
    def state(self) -> CollectorState:
        """Return current collector runtime state."""
        return self._state

    @property
    def error_count(self) -> int:
        """Return total count of collector errors encountered."""
        return self._error_count

    @property
    def last_error(self) -> Optional[str]:
        """Return string message of last recorded error if any."""
        return self._last_error

    @property
    def is_running(self) -> bool:
        """Check if collector is currently in RUNNING state."""
        return self._state == CollectorState.RUNNING

    async def start(self) -> None:
        """Start collector idempotently."""
        if self._state == CollectorState.RUNNING:
            return
        self._state = CollectorState.STARTING
        try:
            await self._on_start()
            self._state = CollectorState.RUNNING
            self._logger.info("Collector '%s' started successfully.", self._name)
        except Exception as e:
            self._record_error(f"Failed to start collector '{self._name}': {e}")
            raise CollectorError(f"Collector '{self._name}' start error: {e}") from e

    async def stop(self) -> None:
        """Stop collector idempotently."""
        if self._state == CollectorState.STOPPED:
            return
        self._state = CollectorState.STOPPED
        try:
            await self._on_stop()
            self._logger.info("Collector '%s' stopped cleanly.", self._name)
        except Exception as e:
            self._record_error(f"Error during collector '{self._name}' stop: {e}")

    async def collect_safe(self) -> List[RawEvent]:
        """Safely execute collect() with isolated error handling."""
        if self._state != CollectorState.RUNNING:
            return []

        try:
            events = await self._collect_impl()
            return events
        except Exception as e:
            self._record_error(f"Collection error in '{self._name}': {e}")
            self._state = CollectorState.ERROR
            return []

    def pause(self) -> None:
        """Pause collector operations idempotently."""
        if self._state == CollectorState.RUNNING:
            self._state = CollectorState.PAUSED
            self._logger.info("Collector '%s' paused.", self._name)

    def resume(self) -> None:
        """Resume collector operations idempotently."""
        if self._state == CollectorState.PAUSED or self._state == CollectorState.ERROR:
            self._state = CollectorState.RUNNING
            self._logger.info("Collector '%s' resumed.", self._name)

    def _record_error(self, message: str) -> None:
        """Internal helper to record error message and increment error count."""
        self._error_count += 1
        self._last_error = message
        self._logger.error(message)

    @abstractmethod
    async def _on_start(self) -> None:
        """Subclass implementation hook for starting collector resources."""
        pass

    @abstractmethod
    async def _on_stop(self) -> None:
        """Subclass implementation hook for stopping collector resources."""
        pass

    @abstractmethod
    async def _collect_impl(self) -> List[RawEvent]:
        """Subclass implementation hook for collecting telemetry RawEvent items."""
        pass
