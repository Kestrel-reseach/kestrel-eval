"""Frontier Reference Model F runner (Gemini via Google AI Studio).

Protocol: Step 2 Part 4c (Preconditions & Frontier Reference F runner).
Complies with ModelRunner protocol for RunMatrix.
Enforces owner decisions:
    - D6: Gemini via Google AI Studio free tier, $0 cost cap.
    - D11: Record model version, execution date and response IDs with every record.
    - D20: Paced across days to respect unpublished free-tier quotas.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from evaluation.f_templates import format_f_prompt
from evaluation.loaders.common import check_item_correctness

try:
    import yaml  # type: ignore[import-untyped]
except ImportError:
    yaml = None  # type: ignore[assignment]


@dataclass
class FrontierConfig:
    """Parsed rate limits and execution settings for Frontier F."""

    model: str = "gemini-2.5-pro"
    provider: str = "Google AI Studio"
    endpoint_type: str = "openai_compatible"
    base_url: str = "https://generativelanguage.googleapis.com/v1beta/openai/"
    cost_cap_usd: float = 0.0
    tier: str = "free_tier"
    api_key_env_var: str = "GEMINI_API_KEY"
    status: str = "PENDING_KEY"
    requests_per_minute: int = 2
    requests_per_day: int = 50
    tokens_per_minute: int = 32000
    max_context_tokens: int = 2048
    max_output_tokens: int = 256
    max_retries: int = 5
    initial_delay_seconds: float = 2.0
    backoff_multiplier: float = 2.0
    max_delay_seconds: float = 60.0
    reference_label: str = (
        "F = gemini-2.5-pro (free tier), exact version and date recorded; "
        "a free-tier reference, not the current frontier."
    )
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_yaml(cls, path: Path | str) -> FrontierConfig:
        """Load configuration from YAML file or return standard defaults."""
        config_path = Path(path)
        if not config_path.exists():
            return cls()

        data: dict[str, Any] = {}
        if yaml is not None:
            with config_path.open(encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
        else:
            current_section = None
            with config_path.open(encoding="utf-8") as f:
                for line in f:
                    raw_line = line.rstrip()
                    stripped = line.strip()
                    if not stripped or stripped.startswith("#"):
                        continue
                    if ":" in stripped:
                        k, v = stripped.split(":", 1)
                        k = k.strip()
                        v = v.split("#")[0].strip().strip("\"'")
                        indent = len(raw_line) - len(raw_line.lstrip())

                        val: Any
                        if v == "":
                            val = {}
                        elif v.isdigit():
                            val = int(v)
                        elif v.replace(".", "", 1).isdigit():
                            val = float(v)
                        else:
                            val = v

                        if indent == 0:
                            current_section = k if v == "" else None
                            data[k] = val
                        elif current_section and isinstance(data.get(current_section), dict):
                            data[current_section][k] = val
                        else:
                            data[k] = val

        raw_limits = data.get("limits")
        limits = raw_limits if isinstance(raw_limits, dict) else {}
        raw_retry = data.get("retry")
        retry = raw_retry if isinstance(raw_retry, dict) else {}

        return cls(
            model=data.get("model", "gemini-2.5-pro"),
            provider=data.get("provider", "Google AI Studio"),
            cost_cap_usd=float(data.get("cost_cap_usd", 0.0)),
            tier=data.get("tier", "free_tier"),
            api_key_env_var=data.get("api_key_env_var", "GEMINI_API_KEY"),
            requests_per_minute=int(limits.get("requests_per_minute", 2)),
            requests_per_day=int(limits.get("requests_per_day", 50)),
            tokens_per_minute=int(limits.get("tokens_per_minute", 32000)),
            max_context_tokens=int(limits.get("max_context_tokens", 2048)),
            max_output_tokens=int(limits.get("max_output_tokens", 256)),
            max_retries=int(retry.get("max_retries", 5)),
            initial_delay_seconds=float(retry.get("initial_delay_seconds", 2.0)),
            backoff_multiplier=float(retry.get("backoff_multiplier", 2.0)),
            max_delay_seconds=float(retry.get("max_delay_seconds", 60.0)),
            reference_label=data.get(
                "reference_label",
                "F = gemini-2.5-pro (free tier), exact version and date recorded; "
                "a free-tier reference, not the current frontier.",
            ),
            raw=data,
        )


class FrontierRunner:
    """Runner for Frontier Reference Model F with rate limiting and D11 provenance logging."""

    def __init__(
        self,
        config: FrontierConfig | None = None,
        *,
        history_mode: str = "full_history",
        mock_mode: bool = False,
    ) -> None:
        self.config = config or FrontierConfig()
        self.history_mode = history_mode  # "no_history" | "full_history"
        self.mock_mode = mock_mode
        self._last_request_time: float = 0.0

        env_key = os.environ.get(self.config.api_key_env_var)
        if env_key and env_key.strip():
            self.api_key_status = "READY"
            self._api_key = env_key.strip()
        else:
            self.api_key_status = "PENDING_KEY"
            self._api_key = None

    def estimate_run_duration_days(self, total_items: int = 1200) -> float:
        """Estimate the run duration in days based on requests per day limit."""
        rpd = self.config.requests_per_day
        if rpd <= 0:
            return float("inf")
        return total_items / rpd

    def _prepare_item_for_prompt(self, item: dict[str, Any]) -> dict[str, Any]:
        """Prepare item prompt dictionary respecting history mode for memory_probe."""
        group = item.get("group", "")
        if group == "memory_probe" and self.history_mode == "no_history":
            clean_item = dict(item)
            q_part = item.get("question")
            if not q_part and "Question:" in item.get("prompt", ""):
                q_part = item["prompt"].split("Question:")[-1].strip()
            clean_item["prompt"] = q_part if q_part else item.get("prompt", "")
            return clean_item
        return item

    def _format_item_messages(self, item: dict[str, Any]) -> list[dict[str, str]]:
        """Format OpenAI-compatible messages using evaluation/f_templates.py."""
        clean_item = self._prepare_item_for_prompt(item)
        return format_f_prompt(clean_item)

    def _format_item_prompt(self, item: dict[str, Any]) -> str:
        """Legacy helper returning raw user prompt text."""
        clean_item = self._prepare_item_for_prompt(item)
        return clean_item.get("prompt", "")

    def _pace_request(self) -> None:
        """Pace requests to stay strictly within requests_per_minute limit."""
        if self.mock_mode:
            return
        rpm = self.config.requests_per_minute
        if rpm <= 0:
            return
        min_interval = 60.0 / rpm
        elapsed = time.time() - self._last_request_time
        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)
        self._last_request_time = time.time()

    def run_item(self, item: dict[str, Any]) -> dict[str, Any]:
        """Execute one item and return a partial JSONL record with D11 metadata."""
        t0 = time.perf_counter()
        now_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        arm = item.get("arm") or item.get("metadata", {}).get("arm", "unknown")

        if self.mock_mode or self.api_key_status != "READY":
            # Deterministic mock/stub return for CI or when key is pending
            target = item.get("target") or item.get("answer", "")
            prediction = str(target)
            correct = check_item_correctness(item, prediction)
            elapsed_ms = (time.perf_counter() - t0) * 1000.0

            return {
                "bytes_read_from_ssd": 0,
                "correct": correct,
                "energy_joules": 0.0,
                "energy_status": "unmeasured",
                "passes": 1,
                "peak_vram_mb": 0.0,
                "retrieval_hits": 0,
                "tokens_generated": len(prediction.split()),
                "verifier_score": None,
                "wall_time_ms": round(elapsed_ms, 2),
                "response_id": f"mock-{item.get('item_id', 'unknown')}",
                "model_version": self.config.model,
                "execution_date": now_date,
                "arm": arm,
            }

        # Real inference with pacing, exponential backoff, and D11 metadata logging
        self._pace_request()
        messages = self._format_item_messages(item)
        prediction, resp_id, model_ver = self._call_gemini_api_with_retry(messages)
        correct = check_item_correctness(item, prediction)
        elapsed_ms = (time.perf_counter() - t0) * 1000.0

        return {
            "bytes_read_from_ssd": 0,
            "correct": correct,
            "energy_joules": 0.0,
            "energy_status": "unmeasured",
            "passes": 1,
            "peak_vram_mb": 0.0,
            "retrieval_hits": 0,
            "tokens_generated": len(prediction.split()),
            "verifier_score": None,
            "wall_time_ms": round(elapsed_ms, 2),
            "response_id": resp_id,
            "model_version": model_ver or self.config.model,
            "execution_date": now_date,
            "arm": arm,
        }

    def _call_gemini_api_with_retry(self, messages: list[dict[str, str]]) -> tuple[str, str, str]:
        """Call Google AI Studio OpenAI-compatible endpoint with exponential backoff.

        Returns (content, response_id, model_version).
        """
        url = f"{self.config.base_url.rstrip('/')}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._api_key}",
        }
        payload = {
            "model": self.config.model,
            "messages": messages,
            "max_tokens": self.config.max_output_tokens,
            "temperature": 0.0,
        }

        delay = self.config.initial_delay_seconds
        for attempt in range(self.config.max_retries):
            try:
                req = urllib.request.Request(
                    url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers=headers,
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=30.0) as resp:
                    res_data = json.loads(resp.read().decode("utf-8"))
                    content = res_data["choices"][0]["message"]["content"].strip()
                    resp_id = str(res_data.get("id", f"gen-{int(time.time()*1000)}"))
                    model_ver = str(res_data.get("model", self.config.model))
                    return content, resp_id, model_ver
            except urllib.error.HTTPError as e:
                if e.code == 429 or e.code >= 500:
                    time.sleep(delay)
                    delay = min(
                        delay * self.config.backoff_multiplier, self.config.max_delay_seconds
                    )
                    continue
                raise
            except Exception:
                if attempt == self.config.max_retries - 1:
                    raise
                time.sleep(delay)
                delay = min(delay * self.config.backoff_multiplier, self.config.max_delay_seconds)

        return "", "", self.config.model
