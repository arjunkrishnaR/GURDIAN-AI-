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

**Phase 1 — Project Foundation & Engineering Base**

Current Status: `PHASE_1_STATUS: COMPLETE`

This initial phase establishes the core Python project structure, centralized configuration system, application state manager, logging framework with sensitive data scrubbing, health check framework, CLI, security foundation, and pytest test suite.

---

## Architecture Overview

GuardianAI's modular system architecture consists of:

* **Core Runtime & Lifecycle**: Application startup/shutdown hooks and state tracking.
* **Centralized Configuration**: YAML & environment variable hierarchy (`GUARDIAN_*`).
* **Sanitized Logging**: Dual console/file logger with secret masking.
* **Health Check Engine**: Self-diagnostic health system.
* **CLI Interface**: Control interface (`guardian version`, `status`, `health`, `start`).

---

## Development Setup

### 1. Requirements
* Windows 10/11 (64-bit)
* Python 3.10+ (Tested on Python 3.14.2)
* Git

### 2. Create Virtual Environment
```cmd
py -m venv .venv
.venv\Scripts\activate
```

### 3. Install Dependencies
```cmd
pip install -e .[dev]
```

---

## Running GuardianAI CLI

```cmd
# Display GuardianAI Version
guardian version

# Display Application Status
guardian status

# Execute Health Checks
guardian health

# Start Application Lifecycle
guardian start
```

---

## Running Tests

Execute the deterministic pytest suite:

```cmd
pytest -v
```

---

## Project Structure

```
C:\GuardianAI
├── guardian/
│   ├── __init__.py
│   ├── main.py
│   ├── core/
│   │   ├── config.py
│   │   ├── state.py
│   │   ├── lifecycle.py
│   │   └── exceptions.py
│   ├── logging/
│   │   └── logger.py
│   ├── health/
│   │   └── checker.py
│   └── cli/
│       └── commands.py
├── tests/
│   ├── test_config.py
│   ├── test_health.py
│   ├── test_state.py
│   ├── test_lifecycle.py
│   └── test_cli.py
├── config/
│   └── config.example.yaml
├── docs/
│   ├── ARCHITECTURE.md
│   ├── DEVELOPMENT.md
│   ├── SECURITY.md
│   └── DEPENDENCIES.md
├── data/
├── logs/
├── pyproject.toml
├── .gitignore
├── .env.example
├── README.md
└── LICENSE
```

---

## Development Philosophy

* **Explicit Boundaries**: Later features (LLMs, Databases, Windows Event Monitoring, Auto-fixing) are intentionally deferred to their respective phases.
* **Deterministic & Safe**: No uncontrolled background tasks, secret leakage, or arbitrary system modification.
