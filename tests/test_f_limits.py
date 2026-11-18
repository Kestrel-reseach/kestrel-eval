"""Unit tests for Frontier Model F rate limits and runner (Step 2 Part 4-0 & 4c)."""

from pathlib import Path

from evaluation.runners.frontier_runner import FrontierConfig, FrontierRunner


def test_f_limits_yaml_loads():
    """Verify config/f_limits.yaml exists and parses frozen limits."""
    config_path = Path("config/f_limits.yaml")
    assert config_path.exists(), "config/f_limits.yaml must exist"

    cfg = FrontierConfig.from_yaml(config_path)
    assert cfg.model == "gemini-2.5-pro"
    assert cfg.provider == "Google AI Studio"
    assert cfg.cost_cap_usd == 0.0
    assert cfg.requests_per_minute == 2
    assert cfg.requests_per_day == 50
    assert cfg.max_context_tokens == 2048


def test_pending_key_status_when_env_unset(monkeypatch):
    """Verify runner detects missing GEMINI_API_KEY and sets status PENDING_KEY."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    runner = FrontierRunner()
    assert runner.api_key_status == "PENDING_KEY"
    assert runner._api_key is None


def test_ready_status_when_env_set(monkeypatch):
    """Verify runner detects GEMINI_API_KEY and sets status READY without exposing key."""
    monkeypatch.setenv("GEMINI_API_KEY", "test-mock-secret-key-12345")
    runner = FrontierRunner()
    assert runner.api_key_status == "READY"
    assert runner._api_key == "test-mock-secret-key-12345"


def test_estimate_run_duration_days():
    """Verify estimation arithmetic for pacing across days."""
    cfg = FrontierConfig(requests_per_day=50)
    runner = FrontierRunner(config=cfg)
    days = runner.estimate_run_duration_days(total_items=1200)
    assert days == 24.0


def test_frontier_mock_mode_execution():
    """Verify mock runner runs an item and returns valid JSONL fields."""
    runner = FrontierRunner(mock_mode=True)
    item = {
        "item_id": "math_001",
        "group": "math",
        "prompt": "What is 2 + 2?",
        "target": "4",
        "answer_check": "exact_numeric",
    }
    res = runner.run_item(item)
    assert res["correct"] is True
    assert res["passes"] == 1
    assert res["energy_status"] == "unmeasured"
    assert res["energy_joules"] == 0.0
    assert res["peak_vram_mb"] == 0.0
    assert res["retrieval_hits"] == 0


def test_frontier_history_modes():
    """Verify memory_probe prompt differences between no_history and full_history."""
    runner_no_hist = FrontierRunner(history_mode="no_history", mock_mode=True)
    runner_full_hist = FrontierRunner(history_mode="full_history", mock_mode=True)

    item = {
        "item_id": "mem_001",
        "group": "memory_probe",
        "question": "What is my city?",
        "prompt": "Past events: moved to Paris.\nQuestion: What is my city?",
        "target": "Paris",
        "answer_check": "key_from_source_history",
    }

    assert runner_no_hist._format_item_prompt(item) == "What is my city?"
    assert "Past events" in runner_full_hist._format_item_prompt(item)
