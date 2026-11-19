"""Unit tests verifying code sandbox security, resource limits, and execution safety."""

from __future__ import annotations

from evaluation.code_sandbox import run_code_in_sandbox


def test_sandbox_valid_solution() -> None:
    code = """def add(a, b):
    return a + b
"""
    test_code = """assert add(2, 3) == 5
assert add(-1, 1) == 0
"""
    assert run_code_in_sandbox(code, test_code) is True


def test_sandbox_assertion_failure() -> None:
    code = """def add(a, b):
    return a * b
"""
    test_code = "assert add(2, 3) == 5"
    assert run_code_in_sandbox(code, test_code) is False


def test_sandbox_syntax_error() -> None:
    code = "def broken(: return 42"
    test_code = "assert True"
    assert run_code_in_sandbox(code, test_code) is False


def test_sandbox_infinite_loop_timeout() -> None:
    code = """def hang():
    while True:
        pass
"""
    test_code = "hang()"
    # Should timeout quickly (1.0s) and return False
    assert run_code_in_sandbox(code, test_code, timeout_s=1.0) is False


def test_sandbox_memory_bomb() -> None:
    code = """def blow_up():
    # Attempt to allocate 2 GB in a 128 MB sandbox
    return [0] * (250 * 1024 * 1024)
"""
    test_code = "blow_up()"
    assert run_code_in_sandbox(code, test_code, max_memory_mb=128) is False


def test_sandbox_network_disabled() -> None:
    code = """import socket

def try_connect():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("8.8.8.8", 80))
"""
    test_code = "try_connect()"
    # socket.socket was neutralized or connect will fail
    assert run_code_in_sandbox(code, test_code, timeout_s=1.0) is False
