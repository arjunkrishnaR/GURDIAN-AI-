# GuardianAI Core Event System Specification

## 1. Overview & Architecture

The **GuardianAI Core Event System** provides a standardized, asynchronous, thread-safe, and deterministic event-processing infrastructure. All future GuardianAI event collectors (Windows Event Log, process metrics, performance monitoring, network diagnostics) normalize incoming telemetry into standard `GuardianEvent` instances and dispatch them via the `EventBus`.

```text
Event Source
     ↓
 RawEvent
     ↓
EventNormalizer
     ↓
GuardianEvent (Immutable)
     ↓
  EventBus (Async Dispatch)
     ↓
 ┌───┴───┬───────┐
 ▼       ▼       ▼
Handler Handler Handler
```

---

## 2. Core Models

### RawEvent
Represents raw, unstructured telemetry from a system or application source before normalization.

* `source`: `EventSource` enum or string
* `timestamp`: Raw timestamp (ISO string, epoch float, datetime, or None)
* `raw_payload`: Unstructured raw payload
* `source_metadata`: Metadata dictionary
* `event_type`: Event type tag (default `"RAW_EVENT"`)

---

### GuardianEvent
Strongly-typed, frozen, and immutable event representation.

```python
@dataclass(frozen=True)
class GuardianEvent:
    event_id: str
    timestamp: datetime  # Timezone-aware UTC
    source: EventSource
    category: EventCategory
    severity: Severity
    event_type: str
    title: str
    description: str
    metadata: MappingProxyType
    process_id: Optional[int]
    process_name: Optional[str]
    application_name: Optional[str]
    correlation_id: Optional[str]
```

---

## 3. Immutability & Metadata Safety

### True Immutability
`GuardianEvent` is marked `frozen=True`. Furthermore, to prevent mutation of nested dictionaries or metadata keys (`event.metadata["key"] = "val"`), the normalizer and constructor convert all metadata into read-only `types.MappingProxyType` instances. Attempts to mutate metadata raise a `TypeError`.

### Metadata Safety
Raw payloads are **not** automatically stored in `metadata["raw_payload"]` by default. This prevents memory leaks, log pollution, and accidental retention of sensitive data. Explicit opt-in (`retain_raw_payload=True`) is required to retain raw payloads.

---

## 4. Correlation ID vs Event ID

* **`event_id`**: Globally unique UUID v4 identifying a single discrete event.
* **`correlation_id`**: Optional grouping identifier connecting multiple related events belonging to the same operational occurrence (e.g., process start, warning, crash sequence).

---

## 5. Event Bus & Failure Isolation

### Asynchronous & Concurrent Dispatch
The `EventBus` uses Python `asyncio`. When an event is published via `await bus.publish(event)`, all matching handlers are dispatched concurrently using `asyncio.gather(*tasks, return_exceptions=True)`.

### Handler Failure Isolation
If one event handler raises an exception:
1. The error is logged via the Phase 1 logger with full traceback context.
2. The `total_failures` metric counter is incremented.
3. Execution of remaining handlers proceeds without interruption.
4. The `EventBus` itself does not crash.

---

## 6. Serialization & Deserialization

`GuardianEvent` supports deterministic JSON round-trip conversion without unsafe deserialization (`pickle`, `eval`, or `exec` are strictly prohibited):

```python
# To JSON
json_data = event.to_json()

# From JSON
reconstructed_event = GuardianEvent.from_json(json_data)
```

---

## 7. Example Usage

```python
import asyncio
from guardian.events import (
    EventBus,
    EventNormalizer,
    EventSource,
    EventCategory,
    Severity,
    TestEventHandler,
)

async def main():
    normalizer = EventNormalizer()
    bus = EventBus()

    handler = TestEventHandler("MyHandler")
    bus.subscribe(handler, event_type="APP_CRASH")

    raw = {
        "source": "APPLICATION",
        "category": "CRASH",
        "severity": "CRITICAL",
        "event_type": "APP_CRASH",
        "title": "Application Exception",
        "description": "Segmentation fault in module core.dll",
        "application_name": "TestApp.exe"
    }

    event = normalizer.normalize(raw)
    await bus.publish(event)

    print(f"Processed {len(handler.received_events)} event(s) successfully.")

if __name__ == "__main__":
    asyncio.run(main())
```
