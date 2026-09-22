# GuardianAI

**GuardianAI** is a Windows AI-powered autonomous computer assistant designed to monitor software and system issues, diagnose root causes using local AI, explain solutions, request user approval, execute approved fixes, verify results, and perform recovery or rollback.

---

## Vision & Core Pipeline

GuardianAI follows a safe, human-in-the-loop autonomous operational pipeline:

```
Monitor → Detect → Diagnose → Explain → Approve → Execute → Verify → Recover
```

---

## Current Phase

**Phase 3 — Windows Monitoring & Background Application Control**

Current Status: `PHASE_3_STATUS: COMPLETE`

GuardianAI now includes read-only observation of Windows Event Logs (`Application`, `System`), process lifecycle events (`PROCESS_STARTED`, `PROCESS_STOPPED`), and system events running safely in the background under the control of the `MonitoringManager`.

---

## Running GuardianAI CLI

```cmd
# Display GuardianAI Version
guardian version

# Display Application & Monitoring Status
guardian status

# Execute Health Checks
guardian health

# Start Application Runtime & Background Monitoring
guardian start

# Pause Background Monitoring Collectors
guardian pause

# Resume Background Monitoring Collectors
guardian resume

# Gracefully Stop GuardianAI Runtime
guardian stop
```

---

## Running Tests

Execute the full deterministic pytest suite:

```cmd
pytest -v
```

---

## Project Structure

```
C:\GuardianAI
├── guardian/
│   ├── core/
│   │   ├── config.py
│   │   ├── state.py
│   │   ├── lifecycle.py
│   │   ├── approval.py
│   │   └── exceptions.py
│   ├── events/
│   │   ├── models.py
│   │   ├── normalizer.py
│   │   ├── bus.py
│   │   └── handlers.py
│   ├── monitoring/
│   │   ├── base.py
│   │   ├── windows_event_log.py
│   │   ├── process.py
│   │   ├── system.py
│   │   ├── manager.py
│   │   └── exceptions.py
│   ├── logging/
│   │   └── logger.py
│   ├── health/
│   │   └── checker.py
│   └── cli/
│       └── commands.py
├── tests/
│   ├── test_monitoring_base.py
│   ├── test_windows_event_log.py
│   ├── test_process_monitor.py
│   ├── test_system_monitor.py
│   ├── test_monitoring_manager.py
│   ├── test_events_models.py
│   ├── test_events_normalizer.py
│   ├── test_events_bus.py
│   ├── test_approval.py
│   ├── test_config.py
│   ├── test_health.py
│   ├── test_lifecycle.py
│   └── test_state.py
├── config/
│   └── config.example.yaml
├── docs/
│   ├── ARCHITECTURE.md
│   ├── WINDOWS_MONITORING.md
│   ├── EVENT_SYSTEM.md
│   ├── DEVELOPMENT.md
│   ├── SECURITY.md
│   └── DEPENDENCIES.md
├── pyproject.toml
└── README.md
```
