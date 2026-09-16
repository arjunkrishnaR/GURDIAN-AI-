"""Unit tests for guardian.events.normalizer module."""

import pytest
from datetime import datetime, timezone

from guardian.events.normalizer import EventNormalizer
from guardian.events.models import RawEvent, EventSource, EventCategory, Severity, GuardianEvent
from guardian.core.exceptions import EventNormalizationError


def test_normalize_raw_event_object():
    """Verify normalizer handles RawEvent objects cleanly."""
    normalizer = EventNormalizer()
    raw = RawEvent(
        source=EventSource.SYSTEM,
        timestamp=datetime.now(timezone.utc),
        raw_payload={"details": "raw data"},
        source_metadata={"origin": "unit_test"},
        event_type="SYS_BOOT"
    )

    event = normalizer.normalize(raw)
    assert isinstance(event, GuardianEvent)
    assert event.source == EventSource.SYSTEM
    assert event.event_type == "SYS_BOOT"
    assert event.metadata["origin"] == "unit_test"
    # Verify raw payload NOT retained by default
    assert "raw_payload" not in event.metadata


def test_normalize_raw_event_retain_payload():
    """Verify explicit retention of raw payload in metadata."""
    normalizer = EventNormalizer()
    raw = RawEvent(
        source=EventSource.APPLICATION,
        raw_payload={"heavy": "data"}
    )
    event = normalizer.normalize(raw, retain_raw_payload=True)
    assert event.metadata["raw_payload"] == {"heavy": "data"}


def test_normalize_dict_input():
    """Verify normalizer handles raw dictionaries with string enums and case normalization."""
    normalizer = EventNormalizer()
    raw_dict = {
        "source": " process ",
        "category": " error ",
        "severity": " critical ",
        "event_type": "PROC_TERM",
        "title": "Process Terminated",
        "process_id": 9999,
        "correlation_id": "CORR_123"
    }

    event = normalizer.normalize(raw_dict)
    assert event.source == EventSource.PROCESS
    assert event.category == EventCategory.ERROR
    assert event.severity == Severity.CRITICAL
    assert event.process_id == 9999
    assert event.correlation_id == "CORR_123"


def test_normalize_timestamp_parsing():
    """Verify normalizer parses ISO strings and numeric timestamps correctly into UTC."""
    normalizer = EventNormalizer()

    # ISO string with offset
    e1 = normalizer.normalize({"source": EventSource.NETWORK, "timestamp": "2026-09-16T12:00:00+02:00"})
    assert e1.timestamp.tzinfo == timezone.utc
    assert e1.timestamp.hour == 10  # 12:00 +02:00 -> 10:00 UTC

    # Epoch timestamp
    e2 = normalizer.normalize({"source": EventSource.NETWORK, "timestamp": 1600000000})
    assert e2.timestamp.tzinfo == timezone.utc


def test_normalize_invalid_enum_raises_error():
    """Verify EventNormalizationError is raised for unrecognized source or category."""
    normalizer = EventNormalizer()
    with pytest.raises(EventNormalizationError) as exc_info:
        normalizer.normalize({"source": "INVALID_SOURCE"})
    assert "Invalid source value" in str(exc_info.value)


def test_normalize_invalid_process_id():
    """Verify EventNormalizationError is raised for non-integer process_id."""
    normalizer = EventNormalizer()
    with pytest.raises(EventNormalizationError) as exc_info:
        normalizer.normalize({"source": EventSource.SYSTEM, "process_id": "not_an_int"})
    assert "Invalid process_id" in str(exc_info.value)
