# GuardianAI Security Model & Principles

GuardianAI operates as an intelligent assistant on Windows. Safety, transparency, privilege restriction, privacy, and explicit human approval are fundamental core requirements.

---

## 1. Core Security & Privacy Directives

GuardianAI enforces the following strict security boundaries:

1. **Subprocess Execution Security in Monitoring**:
   - `wevtutil.exe` and read-only tools are invoked using `subprocess.run(..., shell=False)`.
   - Never uses `cmd /c`, `os.system`, PowerShell execution, `eval`, `exec`, or dynamic shell strings.
   - Fixed argument lists with timeout caps and stdout buffer limits.
   - Observed telemetry is treated strictly as **DATA**, never as executable code.
2. **User Shutdown Authority**:
   - `guardian stop` cleanly terminates all background tasks.
   - Prohibits watchdog self-restoration, anti-termination, Task Manager blocking, hidden monitoring processes, or shutdown interception.
3. **Explicit Human Approval Checkpoint Contract**:
   > *"GuardianAI never treats an AI-generated recommendation as user authorization."*
   - `NO APPROVAL = NO ACTION`. High-impact actions require explicit `ApprovalDecision.APPROVED`.
4. **Privacy Enforcement**:
   - Strictly NO collection of user passwords, tokens, credentials, command-line arguments, environment variables, private process memory, browser data, screenshots, or webcam/microphone inputs.
   - Raw Event Log payloads are excluded by default (`retain_raw_payload=False`).
5. **No Arbitrary System Tampering**:
   - No code shall disable Windows Defender, modify Firewall rules, alter UAC settings, or turn off system security services.
6. **Secret Scrubbing in Logs**:
   - Centralized logging dynamically masks passwords, bearer tokens, and API credentials before writing to disk or console.

---

## 2. Vulnerability & Safety Reporting

Security issues should be reported to the GuardianAI development team following responsible disclosure guidelines.
