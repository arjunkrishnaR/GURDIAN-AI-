# GuardianAI Dependency Manifest & Open-Source Policy

## 1. Open-Source Software vs. Open-Weight AI Models Policy

GuardianAI follows the principles of local-first, privacy-respecting computing:

> *"Use locally runnable open-source software and open-weight AI models wherever practical, with no mandatory proprietary cloud AI dependency."*

### Key Distinction:
* **Open-Source Software (OSS)**: Software released under OSI-approved open-source licenses (e.g., MIT, Apache 2.0, BSD) providing access to source code, modification rights, and redistribution rights.
* **Open-Weight AI Models**: Machine learning models whose trained weights are made publicly available (e.g., Llama 3, Qwen 2.5) for local execution under specific model usage licenses. They are not strictly open-source code repositories.

---

## 2. Phase 1 Dependency Manifest

Phase 1 keeps external dependencies minimal to maximize stability, performance, and security.

### Production Dependencies

| Package | Version Requirement | License | Category | Description / Purpose |
| :--- | :--- | :--- | :--- | :--- |
| **PyYAML** | `>=6.0` | MIT | Open-Source Software | YAML configuration file parsing in `guardian.core.config`. |

### Development & Testing Dependencies

| Package | Version Requirement | License | Category | Description / Purpose |
| :--- | :--- | :--- | :--- | :--- |
| **pytest** | `>=7.0.0` | MIT | Open-Source Software | Test runner for executing unit and integration test suites. |

---

## 3. Python 3.14 Compatibility Notes

* System Python version: `3.14.2`
* `PyYAML 6.0+` and `pytest 7.0+` are fully verified compatible with Python 3.14 standard library.
* Virtual environment creation uses Python standard library `venv`.
