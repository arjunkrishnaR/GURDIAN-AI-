"""Event normalizer for converting raw event structures into standardized GuardianEvent instances."""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Union

from guardian.core.exceptions import EventNormalizationError
from guardian.events.models import (
    EventCategory,
    EventSource,
    GuardianEvent,
    RawEvent,
    Severity,
    make_immutable,
)


class EventNormalizer:
    """Normalizes raw event payloads into valid, immutable GuardianEvent instances."""

    @staticmethod
    def _normalize_enum(enum_cls: Any, value: Any, field_name: str) -> Any:
        """Helper to resolve string or enum values into strict Enum members safely."""
        if isinstance(value, enum_cls):
            return value

        if isinstance(value, str):
            clean_val = value.strip().upper()
            try:
                return enum_cls[clean_val]
            except KeyError:
                # Try matching by enum value
                for member in enum_cls:
                    if member.value == clean_val:
                        return member
                raise EventNormalizationError(
                    f"Invalid {field_name} value '{value}'. Must be one of {[e.name for e in enum_cls]}"
                )

        raise EventNormalizationError(
            f"Invalid type for {field_name}: expected str or {enum_cls.__name__}, got {type(value).__name__}"
        )

    @staticmethod
    def _normalize_timestamp(ts: Any) -> datetime:
        """Helper to parse and normalize timestamps into timezone-aware UTC datetime."""
        if ts is None:
            return datetime.now(timezone.utc)

        if isinstance(ts, datetime):
            if ts.tzinfo is None:
                return ts.replace(tzinfo=timezone.utc)
            return ts.astimezone(timezone.utc)

        if isinstance(ts, (int, float)):
            try:
                return datetime.fromtimestamp(ts, tz=timezone.utc)
            except Exception as e:
                raise EventNormalizationError(f"Invalid numeric timestamp '{ts}': {e}") from e

        if isinstance(ts, str):
            clean_ts = ts.strip()
            if not clean_ts:
                return datetime.now(timezone.utc)
            try:
                dt = datetime.fromisoformat(clean_ts)
                if dt.tzinfo is None:
                    return dt.replace(tzinfo=timezone.utc)
                return dt.astimezone(timezone.utc)
            except Exception as e:
                raise EventNormalizationError(f"Invalid ISO-8601 string timestamp '{ts}': {e}") from e

        raise EventNormalizationError(f"Unsupported timestamp type: {type(ts).__name__}")

    def normalize(
        self,
        raw_event: Union[RawEvent, Dict[str, Any]],
        default_event_type: str = "GENERIC_EVENT",
        default_category: EventCategory = EventCategory.INFORMATION,
        default_severity: Severity = Severity.INFO,
        retain_raw_payload: bool = False
    ) -> GuardianEvent:
        """
        Convert a RawEvent object or dictionary into a normalized GuardianEvent.
        
        Args:
            raw_event: Input RawEvent object or raw dictionary payload.
            default_event_type: Default event_type if unspecified in raw payload.
            default_category: Default category fallback.
            default_severity: Default severity fallback.
            retain_raw_payload: Explicit flag to retain raw payload inside metadata.
        
        Returns:
            Normalized, immutable GuardianEvent instance.
        """
        try:
            if isinstance(raw_event, RawEvent):
                source_input = raw_event.source
                ts_input = raw_event.timestamp
                payload = raw_event.raw_payload
                source_meta = raw_event.source_metadata
                event_type_input = raw_event.event_type
            elif isinstance(raw_event, dict):
                if "source" not in raw_event:
                    raise EventNormalizationError("Raw event dictionary must contain a 'source' key.")
                source_input = raw_event.get("source")
                ts_input = raw_event.get("timestamp")
                payload = raw_event.get("raw_payload")
                source_meta = raw_event.get("source_metadata", {})
                event_type_input = raw_event.get("event_type", default_event_type)
            else:
                raise EventNormalizationError(f"Unsupported raw event type: {type(raw_event).__name__}")

            # 1. Normalize Source
            source = self._normalize_enum(EventSource, source_input, "source")

            # 2. Normalize Timestamp
            timestamp = self._normalize_timestamp(ts_input)

            # 3. Extract / Normalize Category & Severity
            cat_input = None
            sev_input = None
            title_input = ""
            desc_input = ""
            process_id = None
            process_name = None
            app_name = None
            corr_id = None
            event_id_input = None
            extra_meta: Dict[str, Any] = {}

            if isinstance(raw_event, dict):
                cat_input = raw_event.get("category", default_category)
                sev_input = raw_event.get("severity", default_severity)
                title_input = raw_event.get("title", "")
                desc_input = raw_event.get("description", "")
                process_id = raw_event.get("process_id")
                process_name = raw_event.get("process_name")
                app_name = raw_event.get("application_name")
                corr_id = raw_event.get("correlation_id")
                event_id_input = raw_event.get("event_id")

                # Copy additional metadata keys cleanly
                known_keys = {
                    "source", "timestamp", "raw_payload", "source_metadata", "event_type",
                    "category", "severity", "title", "description", "process_id",
                    "process_name", "application_name", "correlation_id", "event_id", "metadata"
                }
                for k, v in raw_event.items():
                    if k not in known_keys:
                        extra_meta[k] = v
                if "metadata" in raw_event and isinstance(raw_event["metadata"], dict):
                    extra_meta.update(raw_event["metadata"])
            else:
                cat_input = default_category
                sev_input = default_severity

            category = self._normalize_enum(EventCategory, cat_input, "category")
            severity = self._normalize_enum(Severity, sev_input, "severity")

            # 4. Normalize Text & Metadata
            event_type = str(event_type_input).strip() or default_event_type
            title = str(title_input).strip() or f"{source.value} {category.value}"
            description = str(desc_input).strip()

            combined_meta = dict(source_meta)
            combined_meta.update(extra_meta)

            if retain_raw_payload and payload is not None:
                combined_meta["raw_payload"] = payload

            # 5. Event ID generation
            event_id = str(event_id_input).strip() if event_id_input else str(uuid.uuid4())

            # 6. Validate process_id type
            if process_id is not None:
                try:
                    process_id = int(process_id)
                except (ValueError, TypeError):
                    raise EventNormalizationError(f"Invalid process_id '{process_id}': must be an integer.")

            return GuardianEvent(
                event_id=event_id,
                timestamp=timestamp,
                source=source,
                category=category,
                severity=severity,
                event_type=event_type,
                title=title,
                description=description,
                metadata=make_immutable(combined_meta),
                process_id=process_id,
                process_name=str(process_name) if process_name else None,
                application_name=str(app_name) if app_name else None,
                correlation_id=str(corr_id) if corr_id else None,
            )

        except Exception as e:
            if isinstance(e, EventNormalizationError):
                raise
            raise EventNormalizationError(f"Event normalization failed: {e}") from e
