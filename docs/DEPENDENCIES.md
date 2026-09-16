# GuardianAI Dependency Manifest & Open-Source Policy

## 1. Open-Source Software vs. Open-Weight AI Models Policy

GuardianAI follows the principles of local-first, privacy-respecting computing:

> *"Use locally runnable open-source software and open-weight AI models wherever practical, with no mandatory proprietary cloud AI dependency."*

---

## 2. Dependency Manifest

GuardianAI keeps external dependencies minimal. Phase 2 relies 100% on the Python standard library for its event models, normalizer, and asynchronous event bus.

### Production Dependencies

| Package | Version Requirement | License | Category | Description / Purpose |
| :--- | :--- | :--- | :--- | :--- |
| **PyYAML** | `>=6.0` | MIT | Open-Source Software | YAML configuration file parsing in `guardian.core.config`. |

### Standard Library Modules Utilized in Phase 2
* `dataclasses`: Data structure modeling (`RawEvent`, `GuardianEvent`)
* `enum`: Strict enumerations (`EventSource`, `EventCategory`, `Severity`)
* `datetime`: Timezone-aware UTC timestamps
* `uuid`: Cryptographically strong UUID v4 event IDs
* `asyncio`: Asynchronous event bus dispatch & concurrency
* `json`: Safe event serialization and deserialization
* `types.MappingProxyType`: Read-only dictionary views for true event metadata immutability

### Development & Testing Dependencies

| Package | Version Requirement | License | Category | Description / Purpose |
| :--- | :--- | :--- | :--- | :--- |
| **pytest** | `>=7.0.0` | MIT | Open-Source Software | Test runner for unit and integration test suites. |
| **pytest-asyncio** | *(Optional)* | MIT | Open-Source Software | Async test runner support if needed. |

---

## 3. Python 3.14 Compatibility Notes

* System Python version: `3.14.2`
* All standard library modules (`asyncio`, `dataclasses`, `types.MappingProxyType`) are native and fully compatible.
