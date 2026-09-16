"""Unit tests for guardian.core.state module."""

import time
import pytest
from guardian.core.state import StateManager
from guardian.core.lifecycle import LifecycleState


def test_initial_state():
    """Verify state manager initial state."""
    mgr = StateManager(version="0.1.0")
    state = mgr.state
    assert state.version == "0.1.0"
    assert state.lifecycle_state == LifecycleState.STOPPED
    assert state.start_timestamp is None
    assert state.last_error is None
    assert "python_version" in state.system_info


def test_lifecycle_update():
    """Verify lifecycle state transition updates timestamp."""
    mgr = StateManager()
    mgr.update_lifecycle(LifecycleState.RUNNING)
    assert mgr.state.lifecycle_state == LifecycleState.RUNNING
    assert mgr.state.start_timestamp is not None

    time.sleep(0.05)
    assert mgr.get_uptime_seconds() > 0.0

    mgr.update_lifecycle(LifecycleState.STOPPED)
    assert mgr.state.lifecycle_state == LifecycleState.STOPPED
    assert mgr.state.start_timestamp is None
    assert mgr.get_uptime_seconds() == 0.0


def test_record_error():
    """Verify recording an error sets lifecycle state to ERROR."""
    mgr = StateManager()
    mgr.record_error("Test failure")
    assert mgr.state.last_error == "Test failure"
    assert mgr.state.lifecycle_state == LifecycleState.ERROR


def test_to_dict():
    """Verify dictionary serialization of state."""
    mgr = StateManager(version="0.1.0")
    d = mgr.to_dict()
    assert d["version"] == "0.1.0"
    assert d["lifecycle_state"] == "STOPPED"
    assert "system_info" in d
