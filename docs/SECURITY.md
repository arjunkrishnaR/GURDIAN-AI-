# GuardianAI Security Model & Principles

GuardianAI will eventually operate as an intelligent assistant on Windows. Safety, transparency, and privilege restriction are fundamental core requirements.

---

## 1. Core Security Directives

Phase 1 establishes the following security boundaries that all future code must strictly obey:

1. **No Arbitrary Shell Execution**: Shell execution must be restricted, audited, and strictly parameterized.
2. **No Automatic Administrator Escalation**: GuardianAI will run in standard user context. Admin elevation will require explicit user confirmation.
3. **No Windows Security Tampering**: No code shall disable Windows Defender, modify Firewall rules, or turn off system security services.
4. **No Registry Tampering**: Unrestricted modification of Windows registry keys is prohibited.
5. **No Credential Harvesting**: GuardianAI does not collect, record, transmit, or cache user passwords, private tokens, SSH keys, or secrets.
6. **Secret Scrubbing in Logs**: Centralized logging dynamically masks passwords, bearer tokens, and API credentials before writing to disk or console.
7. **No Arbitrary Binary Execution**: GuardianAI will not download or execute untrusted third-party binaries or unknown remote scripts.
8. **Explicit Human Approval**: Computer control, system repairs, or configuration changes must be reviewed and approved by the user.

---

## 2. Sensitive Data Masking

The `SensitiveDataScrubber` formatter in `guardian.logging.logger` automatically sanitizes output matching password and token regex patterns.

---

## 3. Vulnerability & Safety Reporting

Security issues should be reported to the GuardianAI development team following responsible disclosure guidelines.
