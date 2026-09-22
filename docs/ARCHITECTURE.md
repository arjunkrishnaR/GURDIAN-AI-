# GuardianAI Architecture Specification

## 1. High-Level Architecture Overview

GuardianAI is designed around an event-driven, diagnostic, human-in-the-loop repair pipeline:

```
Windows / System Telemetry
            │
  ┌─────────┴─────────┐
  ▼                   ▼
Event Log        Process / System
Collector           Collector     ◄── [PHASE 3 WINDOWS MONITORING]
  │                   │
  └─────────┬─────────┘
            ▼
        RawEvent
            │
            ▼
     EventNormalizer              ◄── [PHASE 2 CORE EVENT SYSTEM]
            │
            ▼
      GuardianEvent               ◄── [PHASE 2 IMMUTABLE MODEL]
            │
            ▼
        Event Bus                 ◄── [PHASE 2 ASYNC DISPATCH]
            │
            ▼
      Event Handlers
            │
     Incident Engine
            │
     Context Builder
            │
     Diagnostic AI (Recommendation Engine)
            │
     Solution Planner
            │
    Approval Checkpoint            ◄── [PHASE 2 APPROVAL CHECKPOINT CONTRACT]
            │
    User Decision (Explicit Human Approval)
            │
   Action Execution Engine
            │
      Verification
            │
    Rollback/Recovery
            │
     Memory/Learning
```

---

## 2. Phase Scope Summary

1. **`guardian.core`**: Configuration, application lifecycle, state manager, sanitized logging, approval checkpoint contract (`NO APPROVAL = NO ACTION`).
2. **`guardian.events`**: Strongly typed `GuardianEvent`, `RawEvent`, `EventNormalizer`, and asynchronous `EventBus` with concurrent dispatch and failure isolation.
3. **`guardian.monitoring`**: Windows Event Log collector (`Application`, `System`), process lifecycle monitor (`PROCESS_STARTED`, `PROCESS_STOPPED`), system collector, bounded deduplication, `MonitoringManager` task ownership, idempotent lifecycle (`start`, `pause`, `resume`, `stop`), and health condition reporting (`HEALTHY`, `DEGRADED`, `FAILED`).

---

## 3. Future Architectural Interfaces (Deferred)

The following components will be introduced in subsequent phases:
* **Phase 4**: Event Classification & Machine Learning / Rule Routing.
* **Phase 5-6**: Incident Engine & Context Builder.
* **Phase 7-8**: Ollama Local LLM Integration & RAG.
* **Phase 9+**: Controlled Computer Fixes, Verification, and Rollback Engine.
