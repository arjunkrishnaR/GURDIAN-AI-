"""Event model definitions, enumerations, and immutability wrappers for GuardianAI."""

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from types import MappingProxyType
from typing import Any, Dict, Optional, Union

from guardian.core.exceptions import EventError


class EventSource(Enum):
    """Architectural origin of the event."""
    SYSTEM = "SYSTEM"
    APPLICATION = "APPLICATION"
    PROCESS = "PROCESS"
    NETWORK = "NETWORK"
    PERFORMANCE = "PERFORMANCE"
    WINDOWS = "WINDOWS"
    USER = "USER"
    INTERNAL = "INTERNAL"


class EventCategory(Enum):
    """High-level classification category for the event."""
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFORMATION = "INFORMATION"
    PERFORMANCE = "PERFORMANCE"
    SECURITY = "SECURITY"
    NETWORK = "NETWORK"
    CONFIGURATION = "CONFIGURATION"
    COMPATIBILITY = "COMPATIBILITY"
    CRASH = "CRASH"
    UNKNOWN = "UNKNOWN"


class Severity(Enum):
    """Urgency / impact level of the event."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


def make_immutable(obj: Any) -> Any:
    """Recursively convert dictionaries into read-only MappingProxyType objects."""
    if isinstance(obj, dict):
        return MappingProxyType({k: make_immutable(v) for k, v in obj.items()})
    elif isinstance(obj, list):
        return tuple(make_immutable(v) for v in obj)
    return obj


def unwrap_immutable(obj: Any) -> Any:
    """Recursively convert MappingProxyType objects back into standard dictionaries."""
    if isinstance(obj, (MappingProxyType, dict)):
        return {k: unwrap_immutable(v) for k, v in obj.items()}
    elif isinstance(obj, (tuple, list)):
        return [unwrap_immutable(v) for v in obj]
    return obj


@dataclass
class RawEvent:
    """Representation of unstructured event payload from a source before normalization."""
    source: Union[EventSource, str]
    timestamp: Union[datetime, str, float, None] = None
    raw_payload: Any = None
    source_metadata: Dict[str, Any] = field(default_factory=dict)
    event_type: str = "RAW_EVENT"


@dataclass(frozen=True)
class GuardianEvent:
    """
    Standardized, strongly-typed, immutable event representation.
    
    All fields are frozen, and metadata is wrapped in a MappingProxyType to prevent
    mutation of nested keys.
    """
    event_id: str
    timestamp: datetime
    source: EventSource
    category: EventCategory
    severity: Severity
    event_type: str
    title: str
    description: str
    metadata: MappingProxyType = field(default_factory=lambda: MappingProxyType({}))
    process_id: Optional[int] = None
    process_name: Optional[str] = None
    application_name: Optional[str] = None
    correlation_id: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate fields and enforce true immutability on metadata upon creation."""
        # Ensure timestamp is timezone-aware UTC
        if self.timestamp.tzinfo is None:
            object.__setattr__(self, "timestamp", self.timestamp.replace(tzinfo=timezone.utc))

        # Enforce MappingProxyType for metadata
        if not isinstance(self.metadata, MappingProxyType):
            immutable_meta = make_immutable(self.metadata if isinstance(self.metadata, dict) else {})
            object.__setattr__(self, "metadata", immutable_meta)

    def to_dict(self) -> Dict[str, Any]:
        """Convert GuardianEvent to dictionary representation."""
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source.value,
            "category": self.category.value,
            "severity": self.severity.value,
            "event_type": self.event_type,
            "title": self.title,
            "description": self.description,
            "metadata": unwrap_immutable(self.metadata),
            "process_id": self.process_id,
            "process_name": self.process_name,
            "application_name": self.application_name,
            "correlation_id": self.correlation_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GuardianEvent":
        """Reconstruct GuardianEvent from a dictionary representation."""
        try:
            ts_val = data["timestamp"]
            if isinstance(ts_val, str):
                ts = datetime.fromisoformat(ts_val)
            elif isinstance(ts_val, (int, float)):
                ts = datetime.fromtimestamp(ts_val, tz=timezone.utc)
            elif isinstance(ts_val, datetime):
                ts = ts_val
            else:
                raise EventError(f"Invalid timestamp format: {ts_val}")

            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)

            source = EventSource(data["source"]) if isinstance(data["source"], str) else data["source"]
            category = EventCategory(data["category"]) if isinstance(data["category"], str) else data["category"]
            severity = Severity(data["severity"]) if isinstance(data["severity"], str) else data["severity"]

            meta = make_immutable(data.get("metadata", {}))

            return cls(
                event_id=str(data.get("event_id", str(uuid.uuid4()))),
                timestamp=ts,
                source=source,
                category=category,
                severity=severity,
                event_type=str(data["event_type"]),
                title=str(data.get("title", "")),
                description=str(data.get("description", "")),
                metadata=meta,
                process_id=data.get("process_id"),
                process_name=data.get("process_name"),
                application_name=data.get("application_name"),
                correlation_id=data.get("correlation_id"),
            )
        except Exception as e:
            if isinstance(e, EventError):
                raise
            raise EventError(f"Failed to deserialize GuardianEvent from dict: {e}") from e

    def to_json(self) -> str:
        """Serialize GuardianEvent to JSON string."""
        return json.dumps(self.to_dict(), indent=None)

    @classmethod
    def from_json(cls, json_str: str) -> "GuardianEvent":
        """Reconstruct GuardianEvent safely from a JSON string."""
        try:
            data = json.loads(json_str)
            if not isinstance(data, dict):
                raise EventError("JSON payload must resolve to a dictionary object.")
            return cls.from_dict(data)
        except Exception as e:
            if isinstance(e, EventError):
                raise
            raise EventError(f"Failed to deserialize GuardianEvent from JSON: {e}") from e
