"""Unit tests for guardian.events.models module."""

import json
import uuid
import pytest
from datetime import datetime, timezone
from types import MappingProxyType

from guardian.events.models import (
    EventSource,
    EventCategory,
    Severity,
    RawEvent,
    GuardianEvent,
    make_immutable,
    unwrap_immutable,
)
from guardian.core.exceptions import EventError


def test_raw_event_instantiation():
    """Verify RawEvent basic initialization."""
    raw = RawEvent(source=EventSource.SYSTEM, raw_payload={"key": "value"})
    assert raw.source == EventSource.SYSTEM
    assert raw.raw_payload == {"key": "value"}
    assert raw.event_type == "RAW_EVENT"


def test_guardian_event_immutability():
    """Verify GuardianEvent fields and metadata are strictly immutable."""
    event_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    meta = {"nested": {"key": "value"}}

    event = GuardianEvent(
        event_id=event_id,
        timestamp=now,
        source=EventSource.APPLICATION,
        category=EventCategory.ERROR,
        severity=Severity.HIGH if hasattr(Severity, "HIGH") else Severity.ERROR,
        event_type="APP_CRASH",
        title="Application Crash",
        description="App crashed unexpectedly",
        metadata=make_immutable(meta),
    )

    # 1. Direct field mutation attempt must fail
    with pytest.raises(AttributeError):
        event.title = "Modified Title"

    # 2. Metadata dictionary mutation attempt must fail (MappingProxyType)
    assert isinstance(event.metadata, MappingProxyType)
    with pytest.raises(TypeError):
        event.metadata["new_key"] = "new_value"

    # 3. Nested metadata dictionary mutation attempt must fail
    with pytest.raises(TypeError):
        event.metadata["nested"]["key"] = "modified_value"


def test_timestamp_timezone_enforcement():
    """Verify naive datetime is automatically converted to UTC aware datetime."""
    naive_now = datetime.now()
    event = GuardianEvent(
        event_id=str(uuid.uuid4()),
        timestamp=naive_now,
        source=EventSource.SYSTEM,
        category=EventCategory.INFORMATION,
        severity=Severity.INFO,
        event_type="TEST",
        title="Test Event",
        description="Test",
    )
    assert event.timestamp.tzinfo is not None
    assert event.timestamp.tzinfo == timezone.utc


def test_dict_serialization_round_trip():
    """Verify event to_dict and from_dict round-trip fidelity."""
    original_event = GuardianEvent(
        event_id=str(uuid.uuid4()),
        timestamp=datetime.now(timezone.utc),
        source=EventSource.PROCESS,
        category=EventCategory.PERFORMANCE,
        severity=Severity.WARNING,
        event_type="HIGH_CPU",
        title="High CPU Usage",
        description="CPU spike above 90%",
        metadata=make_immutable({"cpu_percent": 95.5, "tags": ["perf", "cpu"]}),
        process_id=1234,
        process_name="test_proc.exe",
        application_name="TestApp",
        correlation_id="CORR_001",
    )

    d = original_event.to_dict()
    assert d["event_id"] == original_event.event_id
    assert d["source"] == "PROCESS"
    assert d["category"] == "PERFORMANCE"

    reconstructed = GuardianEvent.from_dict(d)
    assert reconstructed.event_id == original_event.event_id
    assert reconstructed.source == EventSource.PROCESS
    assert reconstructed.process_id == 1234
    assert reconstructed.correlation_id == "CORR_001"
    assert reconstructed.metadata["cpu_percent"] == 95.5


def test_json_serialization_round_trip():
    """Verify event to_json and from_json round-trip fidelity."""
    event = GuardianEvent(
        event_id=str(uuid.uuid4()),
        timestamp=datetime.now(timezone.utc),
        source=EventSource.WINDOWS,
        category=EventCategory.CRASH,
        severity=Severity.CRITICAL,
        event_type="BSOD_EVENT",
        title="System Crash",
        description="Kernel panic",
        metadata=make_immutable({"stop_code": "0x0000000A"}),
    )

    json_str = event.to_json()
    assert isinstance(json_str, str)

    reconstructed = GuardianEvent.from_json(json_str)
    assert reconstructed.event_id == event.event_id
    assert reconstructed.source == EventSource.WINDOWS
    assert reconstructed.severity == Severity.CRITICAL
    assert reconstructed.metadata["stop_code"] == "0x0000000A"


def test_invalid_json_deserialization():
    """Verify error raised when deserializing invalid JSON."""
    with pytest.raises(EventError):
        GuardianEvent.from_json("not valid json")

    with pytest.raises(EventError):
        GuardianEvent.from_json('"string instead of dict"')
