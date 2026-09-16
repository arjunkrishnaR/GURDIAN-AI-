"""Unit tests for guardian.core.lifecycle module."""

import pytest
from guardian.core.lifecycle import LifecycleManager, LifecycleState
from guardian.core.exceptions import LifecycleError


def test_lifecycle_flow():
    """Verify normal startup and shutdown lifecycle transitions."""
    mgr = LifecycleManager()
    events = []

    mgr.register_startup_hook(lambda: events.append("started"))
    mgr.register_shutdown_hook(lambda: events.append("stopped"))

    assert mgr.current_state == LifecycleState.STOPPED

    mgr.start()
    assert mgr.current_state == LifecycleState.RUNNING
    assert events == ["started"]

    mgr.stop()
    assert mgr.current_state == LifecycleState.STOPPED
    assert events == ["started", "stopped"]


def test_lifecycle_startup_error():
    """Verify failed startup transitions state to ERROR and raises LifecycleError."""
    mgr = LifecycleManager()

    def failing_hook():
        raise RuntimeError("Startup hook failed")

    mgr.register_startup_hook(failing_hook)

    with pytest.raises(LifecycleError) as exc_info:
        mgr.start()

    assert mgr.current_state == LifecycleState.ERROR
    assert "Startup hook failed" in str(exc_info.value)


def test_lifecycle_shutdown_error():
    """Verify failed shutdown transitions state to ERROR and raises LifecycleError."""
    mgr = LifecycleManager()
    mgr.start()

    def failing_hook():
        raise RuntimeError("Shutdown hook failed")

    mgr.register_shutdown_hook(failing_hook)

    with pytest.raises(LifecycleError) as exc_info:
        mgr.stop()

    assert mgr.current_state == LifecycleState.ERROR
    assert "Shutdown hook failed" in str(exc_info.value)
