# GuardianAI Architecture Specification

## 1. High-Level Architecture Overview

GuardianAI is designed around an event-driven, diagnostic, and human-in-the-loop repair pipeline:

```
Windows/System
      ↓
Event Collector
      ↓
Event Normalizer  ◄── [PHASE 2 CORE EVENT SYSTEM]
      ↓
GuardianEvent     ◄── [PHASE 2 IMMUTABLE MODEL]
      ↓
  Event Bus       ◄── [PHASE 2 ASYNC DISPATCH]
      ↓
Event Handlers
      ↓
Incident Engine
      ↓
Context Builder
      ↓
Diagnostic AI
      ↓
    RAG
      ↓
Solution Planner
      ↓
Policy Engine
      ↓
User Approval
      ↓
Action Engine
      ↓
Computer Control
      ↓
 Verification
      ↓
Rollback/Recovery
      ↓
Memory/Learning
```

---

## 2. Phase 1 & Phase 2 Architecture Scope

GuardianAI currently includes:

1. **`guardian.core.config`**: Centralized configuration loading from defaults, YAML, and `GUARDIAN_*` environment variables.
2. **`guardian.core.lifecycle`**: Lifecycle manager managing state transitions (`STARTING`, `RUNNING`, `STOPPING`, `STOPPED`, `ERROR`).
3. **`guardian.core.state`**: State manager tracking runtime metrics, uptime, system environment details, and error history.
4. **`guardian.logging.logger`**: Sanitized dual-target logger (console + `logs/guardian.log`) with regex secret scrubbing.
5. **`guardian.health.checker`**: Self-diagnostic health checker evaluating Python runtime, filesystem, logging, state, and event system.
6. **`guardian.cli.commands`**: CLI providing `version`, `status`, `health`, and `start` handlers.
7. **`guardian.events.models`**: Strongly typed, frozen, read-only `GuardianEvent` and `RawEvent` models with UUID v4 event IDs and UTC timestamps.
8. **`guardian.events.normalizer`**: `EventNormalizer` normalizing raw telemetry, enum strings, and timestamps into UTC `GuardianEvent` instances.
9. **`guardian.events.bus`**: Asynchronous `EventBus` supporting filtering, concurrent `asyncio` dispatch, handler failure isolation, and metrics.

---

## 3. Future Architectural Interfaces (Deferred)

The following components will be introduced in subsequent phases:
* **Phase 3**: Windows Monitoring (Windows Event Log, Process, Performance).
* **Phase 4-6**: Event Classification & Incident Management.
* **Phase 7-8**: Ollama Local LLM Integration & RAG.
* **Phase 9+**: Controlled Computer Fixes, Verification, and Rollback Engine.
