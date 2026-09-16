# GuardianAI Phase 0 — Development Environment & Hardware Audit Report

**Generated Date:** September 16, 2026  
**Target Project:** GuardianAI  
**Target Platform:** Windows 11 (64-bit)  
**Status:** `PHASE_0_STATUS: BLOCKED`  

---

## 1. System Specifications

| Attribute | Specification Details |
| :--- | :--- |
| **Operating System** | Microsoft Windows 11 Home Single Language |
| **Version & Build** | Version 10.0.26200 (Build 26200) |
| **Architecture** | 64-bit (`x64`) |
| **PowerShell Version** | 5.1.26100.9444 (Desktop Edition) |
| **Administrator Status** | Non-Administrator (`IsAdmin: False`) |
| **CPU** | Intel(R) Core(TM) Ultra 9 275HX (24 Cores, 24 Logical Processors) |
| **Total System RAM** | 15.36 GB (~16 GB) |
| **Available RAM** | ~4.41 GB free |
| **Primary GPU** | NVIDIA GeForce RTX 5060 Laptop GPU (8 GB GDDR6 / 8151 MiB VRAM) |
| **GPU Driver & CUDA** | Driver Version: 592.00 \| CUDA Version: 13.1 supported |
| **Secondary GPU** | Intel(R) Graphics (2 GB Shared) |
| **Primary Drive (C:)** | Total: 924.12 GB \| Free Space: 718.14 GB |

---

## 2. Development Tools Verification

| Tool | Installed | Version | PATH Accessible | Status | Licensing Category | Action / Remediation Required |
| :--- | :---: | :--- | :---: | :--- | :--- | :--- |
| **Git** | Yes | `2.52.0.windows.1` | Yes | Ready | Open-Source (GPLv2) | Identity configured (`user.name: arjunkrishnaR`). No action needed. |
| **Python** | Yes | `3.14.2` (via `py` launcher) | Partial | Problem | Open-Source (PSFL) | `py` launcher works. `python` CLI alias triggers MS Store redirect. Add Python directory to PATH or use `py`. |
| **Node.js** | Yes | `v24.12.0` | Yes | Ready | Open-Source (MIT) | Node.js 24 LTS accessible. No action needed. |
| **npm** | Yes | `11.6.2` | Yes | Ready | Open-Source (Artistic 2.0) | Bundled with Node.js. No action needed. |
| **pnpm** | Partial | `12.4.2` (via Corepack) | No | Problem | Open-Source (MIT) | Standalone `pnpm` binary not in PATH. Run `corepack enable` or `npm install -g pnpm`. |
| **PowerShell** | Yes | `5.1.26100.9444` | Yes | Ready | Proprietary Freeware | Built-in Windows PowerShell 5.1 present. Installing PowerShell 7 (pwsh) recommended. |
| **VS Code** | Yes | `1.119.1` | Yes | Ready | Proprietary Freeware | Binary distribution freeware (Source: MIT). No action needed. |
| **Antigravity** | Yes | Host IDE Active | No CLI | Ready | Proprietary | Antigravity 2.0 Host IDE running. `agy` CLI alias optional for terminal usage. |
| **Ollama** | Yes | `0.34.0` | Yes | Ready | Open-Source (MIT) | Service running on `http://localhost:11434`. Model downloads postponed to Phase 1. |

---

## 3. Infrastructure Verification

| Tool | Installed | Version | PATH Accessible | Status | Licensing Category | Action / Remediation Required |
| :--- | :---: | :--- | :---: | :--- | :--- | :--- |
| **PostgreSQL** | No | N/A | No | Missing | Open-Source (PostgreSQL License) | Install PostgreSQL 16+ natively or run via Docker container in Phase 1. |
| **Docker** | No | N/A | No | Missing | Commercial / Open Engine | Install Docker Desktop or Docker Engine before starting Phase 1. |
| **Podman** | No | N/A | No | Missing | Open-Source (Apache 2.0) | Alternative to Docker. Neither Docker nor Podman is currently installed. |

---

## 4. AI Hardware Assessment

The hardware audit indicates a high-performance development machine equipped with an **Intel Core Ultra 9 275HX CPU (24 cores)** and an **NVIDIA GeForce RTX 5060 Laptop GPU (8 GB VRAM)** with **CUDA 13.1** acceleration.

### Preliminary Model Compatibility Categorization

1. **Small Models (1B – 3B Parameters)** — *Excellent Compatibility*
   - **VRAM Requirements:** ~1.5 GB – 3.0 GB VRAM.
   - **Examples:** `Qwen2.5-Coder-1.5B`, `Qwen2.5-Coder-3B`, `Llama-3.2-3B`, `Phi-3.5-mini`, `nomic-embed-text`.
   - **Assessment:** Fits completely in VRAM with high token generation speeds (>80–120 tokens/sec). Ideal for fast local background reasoning, code parsing, and text embeddings.

2. **Medium Models (7B – 8B Parameters)** — *Good Compatibility (Recommended Baseline)*
   - **VRAM Requirements:** ~4.5 GB – 5.5 GB VRAM (Q4_K_M / Q5_K_M quantization).
   - **Examples:** `Qwen2.5-Coder-7B-Instruct`, `Llama-3.1-8B-Instruct`, `Qwen2-VL-7B-Instruct`.
   - **Assessment:** Fits within the 8 GB VRAM capacity while leaving ~2.5 GB VRAM headroom for context buffers and OS display driving. Recommended target class for primary local AI diagnosis and code generation.

3. **Large Models (14B – 70B Parameters)** — *Limited / Not Recommended for Local VRAM Inference*
   - **VRAM Requirements:** >9.5 GB VRAM (14B Q4) to >40 GB VRAM (70B Q4).
   - **Assessment:** A 14B model exceeds the 8 GB VRAM buffer, forcing CPU/RAM offloading. Given the current 16 GB system RAM with ~4.4 GB free, executing 14B+ models locally will cause severe memory swapping and slow response times.

*Note: Final model selection and benchmarking will be performed in a subsequent phase.*

---

## 5. Development Directory Audit

- **Directory Path:** `C:\GuardianAI`
- **Status:** Verified clean and empty.
- **Suitability:** Ready to host the GuardianAI project in Phase 1. No existing project files or subdirectories were overwritten or disturbed.

---

## 6. Problems & Environment Issues Discovered

1. **Python CLI Command Execution Alias:**  
   The `python` command resolves to the Windows App Execution Alias (`C:\Users\arjun\AppData\Local\Microsoft\WindowsApps\python.exe`), prompting Microsoft Store installation. However, Python 3.14.2 is fully functional via the Python Launcher (`py`) and standard location (`AppData\Local\Python\pythoncore-3.14-64`).

2. **Missing Standalone `pnpm` CLI:**  
   Corepack version `0.34.5` is installed with Node.js, and running `corepack pnpm` works (pnpm 12.4.2). However, running `pnpm` directly in a standard shell fails because Corepack symlinks are not enabled globally.

3. **Missing Container Infrastructure (Docker / Podman):**  
   Neither Docker Desktop nor Podman is installed. Containerization support is required to run Qdrant vector database and PostgreSQL seamlessly during local development.

4. **Missing Native PostgreSQL:**  
   PostgreSQL service and `psql` binary are not present on the system.

5. **Non-Administrator Privilege Level:**  
   The current shell process is running without administrator privileges (`IsAdmin: False`). Administrator permissions will be required when installing Docker Desktop or PostgreSQL.

---

## 7. Recommended Next Steps (Unblocking Phase 1)

To transition from `PHASE_0_STATUS: BLOCKED` to `PHASE_0_STATUS: READY`, complete the following steps:

1. **Enable Corepack / pnpm:**  
   Run `corepack enable` or `npm install -g pnpm` in terminal to expose `pnpm` directly in PATH.
2. **Configure Python Environment PATH:**  
   Add `C:\Users\arjun\AppData\Local\Python\pythoncore-3.14-64\` and its `Scripts` directory to the user/system `PATH`, or ensure `py` is used as the default interpreter invoker.
3. **Install Container Engine (Docker Desktop or Podman):**  
   Install Docker Desktop for Windows (with WSL2 backend enabled) or Podman Desktop with administrator rights.
4. **Install PostgreSQL or Prepare Docker Container:**  
   Install PostgreSQL 16+ or prepare a `docker-compose.yml` for PostgreSQL and Qdrant container orchestration in Phase 1.

---

`PHASE_0_STATUS: BLOCKED`
