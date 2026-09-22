# GuardianAI Windows Monitoring Subsystem Specification

## 1. Overview & Architecture

The **GuardianAI Windows Monitoring Subsystem** introduces read-only telemetry observation of Windows Event Logs (`Application`, `System`), process lifecycle events (`PROCESS_STARTED`, `PROCESS_STOPPED`), and system events.

GuardianAI operates strictly as an **OBSERVER ONLY** in Phase 3. It collects telemetry, normalizes events, and dispatches them to the `EventBus`. It does NOT classify, diagnose, repair, terminate processes, modify the registry, or execute remediation commands.

```text
                        WINDOWS
                           │
            ┌──────────────┼──────────────┐
            │              │              │
            ▼              ▼              ▼
     Windows Event      Process         System
      Log Collector     Collector      Collector
            │              │              │
            └──────────────┼──────────────┘
                           ▼
                        RawEvent
                           │
                           ▼
                   EventNormalizer
                           │
                           ▼
                    GuardianEvent
                           │
                           ▼
                        EventBus
```

---

## 2. Collector Modules

### 1. WindowsEventLogCollector
* **Channels**: `Application`, `System`.
* **Subprocess Security**: Calls `wevtutil.exe qe <channel>` using `subprocess.run(..., shell=False, timeout=5.0)`. Never uses `cmd /c`, `os.system`, PowerShell, `eval`, `exec`, or dynamic shell strings.
* **Bounded Deduplication**: Uses a `collections.deque(maxlen=1000)` and lookup set to deduplicate records based on `(channel, provider, event_id, record_id, timestamp)` composite keys.
* **Raw Payload Privacy**: Retains only normalized metadata fields by default (`timestamp`, `channel`, `provider`, `event_id`, `level`, `record_id`). Does not retain raw XML/JSON payloads unless `retain_raw_payload=True` is explicitly specified.

### 2. ProcessCollector
* **Polling Interval**: Configurable (default `2.0` seconds).
* **PID Reuse Handling**: Tracks processes using `(PID, process_name, start_time)` tuples to handle PID recycling cleanly.
* **Events**: Emits `PROCESS_STARTED` and `PROCESS_STOPPED`.
* **Privacy Enforcement**: Does NOT collect process command lines, environment variables, private memory contents, credentials, or browser data.

### 3. SystemCollector
* **Scope**: Strictly read-only observation of system startup, shutdown, and critical service state telemetry.
* **Constraint**: Never starts, stops, restarts, enables, disables, or configures Windows services.

---

## 3. Background Runtime & Task Ownership

### MonitoringManager Task Ownership
The `MonitoringManager` owns background `asyncio.Task` instances. Sub-collectors do not spawn unmanaged global background tasks.

### Strict Lifecycle State Machine
```text
STOPPED → STARTING → RUNNING
RUNNING → PAUSED → RUNNING
RUNNING → STOPPING → STOPPED
PAUSED → STOPPING → STOPPED
```
All lifecycle operations (`start()`, `pause()`, `resume()`, `stop()`) are strictly **idempotent**.

### Intentional User Shutdown Authority
During `stop()`, `MonitoringManager`:
1. Cancels worker tasks (`task.cancel()`).
2. Awaits cancellation handling `asyncio.CancelledError`.
3. Stops sub-collectors cleanly.
4. Releases resources.
5. Transitions state to `STOPPED`.

GuardianAI NEVER resists shutdown, hides processes, installs self-restarting watchdogs, or blocks Task Manager termination.

---

## 4. Error Isolation & Health Degradation

* Sub-collector exceptions transition the sub-collector to `CollectorState.ERROR` without crashing other collectors or the `MonitoringManager`.
* **Health Condition**:
  * `HEALTHY`: All active collectors are in `RUNNING` state.
  * `DEGRADED`: Some collectors are in `RUNNING` state while others are in `ERROR` state.
  * `FAILED`: All collectors or the manager are in `ERROR` state.

---

## 5. CLI Controls

* `guardian start`: Launches application and background monitoring subsystem.
* `guardian pause`: Idempotently pauses monitoring collectors.
* `guardian resume`: Idempotently resumes monitoring collectors.
* `guardian stop`: Gracefully stops monitoring, cancels all background tasks, and exits.
* `guardian status`: Displays runtime state, monitoring health condition, collector states, and telemetry metrics (`events_collected`, `events_normalized`, `events_published`, `collector_errors`).
* `guardian health`: Runs complete self-diagnostic health check suite.
