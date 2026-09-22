# GuardianAI Dependency Manifest & Open-Source Policy

## 1. Open-Source Software vs. Open-Weight AI Models Policy

GuardianAI follows the principles of local-first, privacy-respecting computing:

> *"Use locally runnable open-source software and open-weight AI models wherever practical, with no mandatory proprietary cloud AI dependency."*

---

## 2. Dependency Manifest

GuardianAI keeps external dependencies minimal. Phase 1, Phase 2, and Phase 3 rely 100% on the Python standard library and native Windows APIs for event models, normalizer, event bus, and monitoring collectors.

### Production Dependencies

| Package | Version Requirement | License | Category | Description / Purpose |
| :--- | :--- | :--- | :--- | :--- |
| **PyYAML** | `>=6.0` | MIT | Open-Source Software | YAML configuration file parsing in `guardian.core.config`. |

### Standard Library Modules Utilized in Phase 3
* `subprocess`: Subprocess execution (`shell=False`, timeout cap) for `wevtutil.exe` and `tasklist.exe` queries
* `asyncio`: Background worker task management and polling loops
* `collections.deque`: Bounded event deduplication queues (`maxlen=1000`)
* `xml.etree.ElementTree`: XML parsing of Windows Event Log records
* `dataclasses`, `enum`, `datetime`, `uuid`, `ctypes`, `winreg`

### Development & Testing Dependencies

| Package | Version Requirement | License | Category | Description / Purpose |
| :--- | :--- | :--- | :--- | :--- |
| **pytest** | `>=7.0.0` | MIT | Open-Source Software | Test runner for unit and integration test suites. |

---

## 3. Python 3.14 Compatibility Notes

* System Python version: `3.14.2`
* All standard library modules (`subprocess`, `asyncio`, `collections`, `xml.etree.ElementTree`) are native and fully compatible.
