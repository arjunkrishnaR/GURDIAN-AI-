# GuardianAI Development Guide

## 1. Environment Setup

GuardianAI uses a standard Python virtual environment for isolated dependency management.

### Creating Virtual Environment
```cmd
py -m venv .venv
.venv\Scripts\activate
```

### Installing Dependencies
```cmd
pip install -e .[dev]
```

---

## 2. Running Commands

GuardianAI exposes a CLI entry point:

```cmd
# Check Version
guardian version

# Check Status
guardian status

# Run Health Check Framework
guardian health

# Test Startup Lifecycle
guardian start
```

---

## 3. Testing Standards

All tests are located in `tests/`. Tests must remain 100% deterministic and isolated from external networks or database instances.

Run tests using pytest:

```cmd
pytest -v
```

---

## 4. Code Quality & Guidelines

* **Type Annotations**: Use Python standard type hints for all function signatures and dataclasses.
* **Docstrings**: Provide clear module-level and function-level docstrings.
* **Exceptions**: Inherit from `GuardianError` in `guardian.core.exceptions`.
* **Secret Scrubbing**: Ensure all logging passes through `SensitiveDataScrubber`.
