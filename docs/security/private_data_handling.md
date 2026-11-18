# Project Kestrel — Private Data Handling & Agent Access Policy

**Document:** `docs/security/private_data_handling.md`  
**Date:** 2026-11-18  
**Scope:** Physical storage, isolation invariants, and agent restrictions for locked test data.  

---

## 1. Storage Location & Physical Isolation

The Project Kestrel Prototype 1 locked test partition (1,200 items across 6 groups) is physically quarantined outside the `kestrel-eval` git repository:

- **Directory Path**: `/home/ash09/project_x/kestrel_private/locked_test/`
- **Environment Variable**: `KESTREL_PRIVATE_DIR` (defaults to `/home/ash09/project_x/kestrel_private`)
- **Contained Files**:
  - `math.jsonl` (200 items)
  - `science_mcq.jsonl` (200 items)
  - `knowledge_mcq.jsonl` (300 items)
  - `code.jsonl` (100 items)
  - `knowledge_qa.jsonl` (300 items)
  - `memory_probe.jsonl` (100 items)
- **Tracking Rule**: Zero locked test data files may ever be staged, committed, or tracked in git. Only SHA-256 file digests and the root hash (`22fff5e0...`) are tracked in `evaluation/manifest.yaml`.

---

## 2. Mandatory Agent & IDE Tool Invariants

Any AI agent, IDE extension, language model assistant, or background file watcher operating on the local workstation is subject to the following non-negotiable security rules:

1. **Strict Prohibition on Reading Locked Files**:
   No agent tool (`read_file`, `cat`, `grep`, `head`, `run_command` displaying file text) may open, read, or print contents from `/home/ash09/project_x/kestrel_private/`.
2. **Prevention of Cloud Exposure**:
   Reading locked files within an AI assistant transmits prompt and ground-truth text into external cloud inference endpoints, burning the test partition and destroying experimental validity.
3. **Count-Only / Hash-Only Automation**:
   Harnesses and verification scripts may interact with this folder exclusively through automated count-only or hash-verification subroutines where item contents never enter agent prompts, logs, or reports.
4. **Step 10 One-Time Access Guard**:
   Programmatic execution is blocked by `load_suite_partition` unless `KESTREL_ALLOW_LOCKED_TEST="1"` is explicitly set in the execution environment for the official Step 10 evaluation run.

---

## 3. Current Directory Permissions (`ls -ld`)

Current filesystem permissions reported on the host:
```bash
$ ls -ld /home/ash09/project_x/kestrel_private
drwxrwxrwx 3 ash09 ash09 4096 Nov 18 17:17 /home/ash09/project_x/kestrel_private

$ ls -ld /home/ash09/project_x/kestrel_private/locked_test
drwxrwxrwx 2 ash09 ash09 4096 Nov 18 17:17 /home/ash09/project_x/kestrel_private/locked_test
```

---

## 4. Recommended Security Hardening for Owners

Per instructions, permissions have **not** been modified by the agent. The following hardening steps are strongly recommended for the owners:

1. **Restrict POSIX Directory Permissions (`chmod 700`)**:
   Remove world-readable and world-writable permissions so only the owner user (`ash09`) can traverse or read the folder:
   ```bash
   chmod 700 /home/ash09/project_x/kestrel_private
   chmod 700 /home/ash09/project_x/kestrel_private/locked_test
   chmod 600 /home/ash09/project_x/kestrel_private/locked_test/*.jsonl
   ```
2. **Exclude from IDE Indexing & File Watchers**:
   Add `kestrel_private` to `.vscode/settings.json` under `files.watcherExclude` and `search.exclude` to prevent language servers and AI extensions from auto-scanning file buffers:
   ```json
   "search.exclude": {
     "**/kestrel_private/**": true
   },
   "files.watcherExclude": {
     "**/kestrel_private/**": true
   }
   ```
3. **Hardware Encrypted Volume for Step 10**:
   For production runs or multi-user environments, move `kestrel_private` to an encrypted loopback volume or GPG-encrypted tarball (`locked_test.tar.gz.gpg`), decrypted strictly in memory at Step 10.

