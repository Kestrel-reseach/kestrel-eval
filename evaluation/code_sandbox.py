"""Isolated and secure code execution sandbox for evaluating generated Python code.

Protocol: Step 2 Part 4R (Sandboxed Execution).
Runs unit tests in an isolated subprocess with:
- Strict wall-clock timeout
- Resource limits (RLIMIT_AS for memory, RLIMIT_FSIZE for disk writes)
- Isolated temporary working directory
- Sanitized environment variables (stripping keys, tokens, credentials)
- Restricted pre-exec execution
"""

from __future__ import annotations

import ast
import os
import resource
import subprocess
import sys
import tempfile
from pathlib import Path


def _set_resource_limits(max_memory_mb: int = 512, max_cpu_s: int = 5) -> None:
    """Preexec hook to apply OS-level resource limits on POSIX platforms."""
    try:
        # Max virtual memory (512 MB)
        mem_bytes = max_memory_mb * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_AS, (mem_bytes, mem_bytes))
    except (ValueError, resource.error, OSError):
        pass

    try:
        # Max CPU time
        resource.setrlimit(resource.RLIMIT_CPU, (max_cpu_s, max_cpu_s + 1))
    except (ValueError, resource.error, OSError):
        pass

    try:
        # Max file size created (1 MB)
        max_file_bytes = 1024 * 1024
        resource.setrlimit(resource.RLIMIT_FSIZE, (max_file_bytes, max_file_bytes))
    except (ValueError, resource.error, OSError):
        pass


def run_code_in_sandbox(
    code: str,
    test_code: str,
    *,
    prompt: str | None = None,
    entry_point: str | None = None,
    timeout_s: float = 3.0,
    max_memory_mb: int = 512,
) -> bool:
    """Execute generated Python code against test assertions in an isolated sandbox.

    Returns True if the execution exits with returncode 0.
    Returns False on syntax error, assertion error, timeout, or exception.
    """
    if not code or not test_code:
        return False

    # Check if code requires prompt prefix (e.g. function signature)
    if prompt and not code.strip().startswith("def ") and "def " in prompt:
        lines = code.splitlines()
        first_non_empty = next((line for line in lines if line.strip()), "")
        if first_non_empty and not first_non_empty.startswith((" ", "\t")):
            indented = "\n".join(("    " + line if line.strip() else line) for line in lines)
            code_to_run = f"{prompt.rstrip()}\n{indented}"
        else:
            code_to_run = f"{prompt.rstrip()}\n{code}"
    else:
        code_to_run = code

    # AST validation before execution
    try:
        ast.parse(code_to_run)
        ast.parse(test_code)
    except (SyntaxError, Exception):
        return False

    # Construct complete self-contained test script
    # Inject socket neutralization and safe guard preamble
    script_content = f"""# -*- coding: utf-8 -*-
import sys

# Sandbox security guards: neutralize networking and filesystem tampering
try:
    import socket
    socket.socket = None  # Disable socket creation
except Exception:
    pass

# User implementation
{code_to_run}

# Verification unit tests
{test_code}

sys.exit(0)
"""

    with tempfile.TemporaryDirectory(prefix="kestrel_sandbox_") as tmp_dir:
        test_file = Path(tmp_dir) / "test_run.py"
        test_file.write_text(script_content, encoding="utf-8")

        # Sanitize environment: keep only safe system runtime paths
        safe_env = {
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "PYTHONPATH": "",
            "PYTHONDONTWRITEBYTECODE": "1",
            "LC_ALL": "C.UTF-8",
            "LANG": "C.UTF-8",
        }

        try:
            res = subprocess.run(
                [sys.executable, str(test_file)],
                cwd=tmp_dir,
                env=safe_env,
                capture_output=True,
                text=True,
                timeout=timeout_s,
                preexec_fn=lambda: _set_resource_limits(
                    max_memory_mb=max_memory_mb, max_cpu_s=int(timeout_s + 2)
                ),
            )
            return res.returncode == 0
        except subprocess.TimeoutExpired:
            return False
        except Exception:  # noqa: BLE001
            return False
