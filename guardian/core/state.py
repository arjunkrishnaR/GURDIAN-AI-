"""Application state management for GuardianAI."""

import sys
import platform
import time
from dataclasses import dataclass, field
from typing import Optional, Dict, Any

from guardian.core.lifecycle import LifecycleState


@dataclass
class AppState:
    """Dataclass holding current application state metadata."""
    version: str = "0.1.0"
    lifecycle_state: LifecycleState = LifecycleState.STOPPED
    start_timestamp: Optional[float] = None
    last_error: Optional[str] = None
    system_info: Dict[str, str] = field(default_factory=dict)


class StateManager:
    """Central manager for maintaining and reporting application state."""

    def __init__(self, version: str = "0.1.0") -> None:
        self._state = AppState(
            version=version,
            system_info={
                "python_version": sys.version.split()[0],
                "platform": platform.platform(),
                "architecture": platform.architecture()[0],
            }
        )

    @property
    def state(self) -> AppState:
        """Get copy or reference of current state."""
        return self._state

    def update_lifecycle(self, new_state: LifecycleState) -> None:
        """Update current lifecycle state and manage timestamps."""
        self._state.lifecycle_state = new_state
        if new_state in (LifecycleState.STARTING, LifecycleState.RUNNING) and self._state.start_timestamp is None:
            self._state.start_timestamp = time.time()
        elif new_state == LifecycleState.STOPPED:
            self._state.start_timestamp = None

    def record_error(self, error_message: str) -> None:
        """Record an error and update lifecycle state to ERROR."""
        self._state.last_error = error_message
        self._state.lifecycle_state = LifecycleState.ERROR

    def get_uptime_seconds(self) -> float:
        """Calculate current uptime in seconds if running."""
        if self._state.start_timestamp is None:
            return 0.0
        return round(time.time() - self._state.start_timestamp, 2)

    def to_dict(self) -> Dict[str, Any]:
        """Return state representation as a clean dictionary."""
        return {
            "version": self._state.version,
            "lifecycle_state": self._state.lifecycle_state.name,
            "uptime_seconds": self.get_uptime_seconds(),
            "last_error": self._state.last_error,
            "system_info": self._state.system_info,
        }
