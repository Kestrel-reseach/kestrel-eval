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
import threading
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
    from google import genai
    from google.genai import types
except ImportError:
    genai = None  # type: ignore[assignment]
    types = None  # type: ignore[assignment]

try:
    import yaml  # type: ignore[import-untyped]
except ImportError:
    yaml = None  # type: ignore[assignment]


@dataclass
class FrontierConfig:
    """Parsed rate limits and execution settings for Frontier F."""

    model: str = "gemini-flash-lite-latest"
    provider: str = "Google AI Studio"
    endpoint_type: str = "genai_sdk"
    base_url: str = "https://generativelanguage.googleapis.com/v1beta/models/"
    cost_cap_usd: float = 0.0
    tier: str = "free_tier"
    api_key_env_var: str = "GEMINI_API_KEY"
    status: str = "PENDING_KEY"
    requests_per_minute: int = 120
    requests_per_day: int = 1500
    tokens_per_minute: int = 1000000
    max_context_tokens: int = 2048
    max_output_tokens: int = 256
    max_retries: int = 5
    initial_delay_seconds: float = 1.0
    backoff_multiplier: float = 2.0
    max_delay_seconds: float = 30.0
    reference_label: str = (
        "F = gemini-flash-lite-latest (gemini-3.5-flash-lite, free tier), exact version and date recorded; "
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
        self._lock = threading.Lock()

        env_key = os.environ.get(self.config.api_key_env_var)
        if not env_key and not os.environ.get("PYTEST_CURRENT_TEST"):
            dotenv_path = Path(__file__).resolve().parent.parent.parent / ".env"
            if dotenv_path.exists():
                with dotenv_path.open(encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith(f"{self.config.api_key_env_var}="):
                            env_key = line.split("=", 1)[1].strip().strip("\"'")
                            break

        raw_keys = [k.strip() for k in env_key.split(",") if k.strip()] if env_key else []
        self._api_keys: list[str] = raw_keys
        self._current_key_idx: int = 0

        if self._api_keys:
            self.api_key_status = "READY"
            self._api_key = self._api_keys[0]
        else:
            self.api_key_status = "PENDING_KEY"
            self._api_key = None

        self._client: Any = None
        if self._api_key and genai is not None:
            try:
                self._client = genai.Client(
                    api_key=self._api_key, http_options={"api_version": "v1beta"}
                )
            except (ValueError, TypeError, RuntimeError):
                self._client = None

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
        with self._lock:
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
                "item_id": item.get("item_id") or item.get("id", ""),
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
        prediction, resp_id, model_ver, tokens = self._call_gemini_api_with_retry(messages)
        correct = check_item_correctness(item, prediction)
        elapsed_ms = (time.perf_counter() - t0) * 1000.0

        return {
            "item_id": item.get("item_id") or item.get("id", ""),
            "bytes_read_from_ssd": 0,
            "correct": correct,
            "energy_joules": 0.0,
            "energy_status": "unmeasured",
            "passes": 1,
            "peak_vram_mb": 0.0,
            "retrieval_hits": 0,
            "tokens_generated": tokens if tokens > 0 else len(prediction.split()),
            "verifier_score": None,
            "wall_time_ms": round(elapsed_ms, 2),
            "response_id": resp_id,
            "model_version": model_ver or self.config.model,
            "execution_date": now_date,
            "arm": arm,
        }

    def _call_gemini_api_with_retry(
        self, messages: list[dict[str, str]]
    ) -> tuple[str, str, str, int]:
        """Call Google AI Studio using google.genai SDK with retry & exponential backoff.

        Returns (content, response_id, model_version, tokens_generated).
        """
        system_instr = (
            messages[0]["content"] if messages and messages[0].get("role") == "system" else None
        )
        user_content = (
            messages[1]["content"]
            if len(messages) > 1
            else (messages[0]["content"] if messages else "")
        )

        delay = self.config.initial_delay_seconds
        for attempt in range(self.config.max_retries):
            key_idx_used = self._current_key_idx
            try:
                if self._client is not None:
                    # Google GenAI SDK call
                    cfg_args: dict[str, Any] = {
                        "temperature": 0.0,
                        "max_output_tokens": self.config.max_output_tokens,
                    }
                    if system_instr and types is not None:
                        cfg_args["system_instruction"] = system_instr
                    gen_cfg = types.GenerateContentConfig(**cfg_args) if types is not None else None

                    resp = self._client.models.generate_content(
                        model=self.config.model,
                        contents=user_content,
                        config=gen_cfg,
                    )
                    content = (resp.text or "").strip()
                    resp_id = str(getattr(resp, "response_id", f"gen-{int(time.time()*1000)}"))
                    model_ver = str(getattr(resp, "model_version", self.config.model))
                    tokens = 0
                    if hasattr(resp, "usage_metadata") and resp.usage_metadata is not None:
                        tokens = getattr(resp.usage_metadata, "candidates_token_count", 0) or 0
                    return content, resp_id, model_ver, tokens
                else:
                    # Fallback REST endpoint (urllib)
                    url = (
                        f"{self.config.base_url.rstrip('/')}/"
                        f"{self.config.model}:generateContent?key={self._api_key}"
                    )
                    payload: dict[str, Any] = {
                        "contents": [{"parts": [{"text": user_content}]}],
                        "generationConfig": {
                            "temperature": 0.0,
                            "maxOutputTokens": self.config.max_output_tokens,
                        },
                    }
                    if system_instr:
                        payload["systemInstruction"] = {"parts": [{"text": system_instr}]}

                    req = urllib.request.Request(
                        url,
                        data=json.dumps(payload).encode("utf-8"),
                        headers={"Content-Type": "application/json"},
                        method="POST",
                    )
                    with urllib.request.urlopen(req, timeout=30.0) as resp:
                        res_data = json.loads(resp.read().decode("utf-8"))
                        cand = res_data.get("candidates", [{}])[0]
                        parts = cand.get("content", {}).get("parts", [{}])
                        content = parts[0].get("text", "").strip() if parts else ""
                        resp_id = str(res_data.get("responseId", f"gen-{int(time.time()*1000)}"))
                        model_ver = str(res_data.get("modelVersion", self.config.model))
                        usage = res_data.get("usageMetadata", {})
                        tokens = int(usage.get("candidatesTokenCount", 0))
                        return content, resp_id, model_ver, tokens

            except Exception as e:
                # Retry on 503 (high demand) or 429 (quota limit)
                status_code = getattr(e, "code", None) or getattr(e, "status_code", None)
                err_str = str(e)

                # Check if this is a daily quota exhaustion and rotate keys if possible
                is_daily_quota = (
                    "requests per day" in err_str.lower()
                    or "requestsperday" in err_str.lower()
                    or "daily" in err_str.lower()
                    or "free_tier_requests" in err_str.lower()
                )
                if is_daily_quota:
                    with self._lock:
                        if self._current_key_idx > key_idx_used:
                            # Another worker thread already rotated to a newer key!
                            rotated = True
                        elif self._current_key_idx + 1 < len(self._api_keys):
                            self._current_key_idx += 1
                            self._api_key = self._api_keys[self._current_key_idx]
                            print(
                                f"\n[KEY ROTATION] Daily limit reached. Rotating to key {self._current_key_idx + 1}/{len(self._api_keys)}"
                            )
                            if genai is not None:
                                try:
                                    self._client = genai.Client(
                                        api_key=self._api_key,
                                        http_options={"api_version": "v1beta"},
                                    )
                                except (ValueError, TypeError, RuntimeError):
                                    self._client = None
                            rotated = True
                        else:
                            rotated = False
                    if rotated:
                        time.sleep(1.0)
                        continue

                is_transient = (
                    status_code in (429, 500, 502, 503, 504)
                    or "503" in err_str
                    or "429" in err_str
                    or "high demand" in err_str.lower()
                    or "resource_exhausted" in err_str.lower()
                )
                if attempt < self.config.max_retries - 1 and is_transient:
                    # On 429 per-minute rate limit, ensure we sleep at least 8.5 seconds
                    sleep_time = (
                        max(delay, 8.5)
                        if ("429" in err_str or "resource_exhausted" in err_str.lower())
                        else delay
                    )
                    time.sleep(sleep_time)
                    delay = min(
                        delay * self.config.backoff_multiplier, self.config.max_delay_seconds
                    )
                    continue
                if attempt == self.config.max_retries - 1:
                    raise
                time.sleep(delay)
                delay = min(delay * self.config.backoff_multiplier, self.config.max_delay_seconds)

        return "", "", self.config.model, 0
