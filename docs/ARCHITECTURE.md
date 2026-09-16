# GuardianAI Architecture Specification

## 1. High-Level Architecture Overview

GuardianAI is designed around an event-driven, diagnostic, and human-in-the-loop repair pipeline:

```
Windows/System
      ↓
Event Collector
      ↓
Event Normalizer
      ↓
Event Classifier
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

## 2. Phase 1 Foundational Scope

Phase 1 implements the core software architecture foundation required to support future components:

1. **`guardian.core.config`**: Deterministic configuration engine reading from defaults, YAML (`config.example.yaml`), and `GUARDIAN_*` environment variables.
2. **`guardian.core.lifecycle`**: `LifecycleManager` tracking application states (`STARTING`, `RUNNING`, `STOPPING`, `STOPPED`, `ERROR`) with hook callbacks.
3. **`guardian.core.state`**: `StateManager` tracking runtime metrics, uptime, system environment details, and error history.
4. **`guardian.logging.logger`**: Sanitized dual-target logger (console + `logs/guardian.log`) with regex secret scrubbing.
5. **`guardian.health.checker`**: Self-diagnostic health checker evaluating Python runtime, filesystem permissions, logging, configuration, and state.
6. **`guardian.cli.commands`**: Command line interface providing `version`, `status`, `health`, and `start` handlers.

---

## 3. Future Architectural Interfaces (Deferred)

The following components will be introduced in subsequent phases:
* **Phase 2**: Core Event System (Event Collector, Normalizer, Classifier).
* **Phase 3-6**: Windows Diagnostics & Incident Management.
* **Phase 7-8**: Ollama Local LLM Integration & RAG.
* **Phase 9+**: Controlled Computer Fixes, Verification, and Rollback Engine.
