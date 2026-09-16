# GuardianAI Security Model & Principles

GuardianAI operates as an intelligent assistant on Windows. Safety, transparency, privilege restriction, and explicit human approval are fundamental core requirements.

---

## 1. Core Security Directives

GuardianAI enforces the following strict security boundaries:

1. **Explicit Human Approval Checkpoint Contract**:
   > *"GuardianAI never treats an AI-generated recommendation as user authorization."*
   - `NO APPROVAL = NO ACTION`.
   - High-impact and critical actions require explicit `ApprovalDecision.APPROVED`.
   - Approvals are **specific** (bound to exact `action_id`), **time-bound** (`expires_at`), **auditable**, and **non-transitive** (approving action A does not authorize action B).
   - No bypass parameters exist (`force=True`, `auto_approve=True`, `skip_approval=True` are prohibited).
2. **No Arbitrary Shell Execution**: Shell execution must be restricted, audited, and strictly parameterized.
3. **No Automatic Administrator Escalation**: GuardianAI runs in standard user context. Admin elevation requires explicit user confirmation.
4. **No Windows Security Tampering**: No code shall disable Windows Defender, modify Firewall rules, or turn off system security services.
5. **No Registry Tampering**: Unrestricted modification of Windows registry keys is prohibited.
6. **No Credential Harvesting**: GuardianAI does not collect, record, transmit, or cache user passwords, private tokens, SSH keys, or secrets.
7. **Secret Scrubbing in Logs**: Centralized logging dynamically masks passwords, bearer tokens, and API credentials before writing to disk or console.
8. **No Arbitrary Binary Execution**: GuardianAI will not download or execute untrusted third-party binaries or unknown remote scripts.

---

## 2. Sensitive Data Masking

The `SensitiveDataScrubber` formatter in `guardian.logging.logger` automatically sanitizes output matching password and token regex patterns.

---

## 3. Vulnerability & Safety Reporting

Security issues should be reported to the GuardianAI development team following responsible disclosure guidelines.
