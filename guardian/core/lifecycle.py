"""Application lifecycle management for GuardianAI."""

from enum import Enum, auto
from typing import Callable, List
from guardian.core.exceptions import LifecycleError


class LifecycleState(Enum):
    """Possible lifecycle states for GuardianAI application."""
    STARTING = auto()
    RUNNING = auto()
    STOPPING = auto()
    STOPPED = auto()
    ERROR = auto()


class LifecycleManager:
    """Manages state transitions and hooks during application execution lifecycle."""

    def __init__(self) -> None:
        self._state: LifecycleState = LifecycleState.STOPPED
        self._startup_hooks: List[Callable[[], None]] = []
        self._shutdown_hooks: List[Callable[[], None]] = []

    @property
    def current_state(self) -> LifecycleState:
        """Get current lifecycle state."""
        return self._state

    def register_startup_hook(self, hook: Callable[[], None]) -> None:
        """Register a hook callback to run on application startup."""
        self._startup_hooks.append(hook)

    def register_shutdown_hook(self, hook: Callable[[], None]) -> None:
        """Register a hook callback to run on application shutdown."""
        self._shutdown_hooks.append(hook)

    def start(self) -> None:
        """Transition application lifecycle to STARTING -> RUNNING."""
        if self._state == LifecycleState.RUNNING:
            return

        self._state = LifecycleState.STARTING
        try:
            for hook in self._startup_hooks:
                hook()
            self._state = LifecycleState.RUNNING
        except Exception as e:
            self._state = LifecycleState.ERROR
            raise LifecycleError(f"Error during lifecycle startup: {e}") from e

    def stop(self) -> None:
        """Transition application lifecycle to STOPPING -> STOPPED."""
        if self._state == LifecycleState.STOPPED:
            return

        self._state = LifecycleState.STOPPING
        try:
            for hook in reversed(self._shutdown_hooks):
                hook()
            self._state = LifecycleState.STOPPED
        except Exception as e:
            self._state = LifecycleState.ERROR
            raise LifecycleError(f"Error during lifecycle shutdown: {e}") from e

    def set_error(self, reason: str = "") -> None:
        """Transition application lifecycle to ERROR state."""
        self._state = LifecycleState.ERROR
