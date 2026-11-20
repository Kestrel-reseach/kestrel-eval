"""Prompt templates and execution configuration for Frontier Reference Model F.

Part 6: F Preparation (DO NOT CALL F).
Zero external calls were made during this pass. Execution begins only on explicit instruction.

Deviation Notice:
- MCQ Prefill Deviation: External OpenAI-compatible APIs (Google AI Studio) do not support
  assistant response prefill (e.g. prefilling 'Answer: '). Therefore, MCQ prompts include the
  explicit instruction: 'Reply with only the option letter (e.g. A, B, C, D, or E) and nothing else.'
"""

from __future__ import annotations

from typing import Any

# Mandatory status and verification statement
F_EXECUTION_NOTICE = (
    "Zero external calls were made during this pass. Execution begins only on explicit instruction."
)

F_MCQ_DIRECTIVE = "Reply with only the option letter (e.g. A, B, C, D, or E) and nothing else."

F_SYSTEM_PROMPTS: dict[str, str] = {
    "math": "You are a precise mathematical problem solver. Reason step by step and conclude your response with 'Final Answer: <number>' or \\boxed{<number>}.",
    "science_mcq": f"You are a multiple-choice question solver. {F_MCQ_DIRECTIVE}",
    "knowledge_mcq": f"You are a multiple-choice question solver. {F_MCQ_DIRECTIVE}",
    "code": "You are an expert Python programmer. Return only executable Python code in a ```python code block.",
    "knowledge_qa": "You are a factual question answering system. Answer the question using solely the provided context. Answer in as few words as possible.",
    "memory_probe": "You are an assistant with personal chronological memory. Answer questions about the user's current status and preferences using the provided history logs.",
}


def format_f_prompt(
    item: dict[str, Any], context_passages: list[str] | None = None
) -> list[dict[str, str]]:
    """Format chat messages for Model F without assistant prefill."""
    group = item.get("group", "")
    system_text = F_SYSTEM_PROMPTS.get(group, "You are a helpful assistant.")
    prompt_text = item.get("prompt", "").strip()

    if group in ("science_mcq", "knowledge_mcq"):
        user_content = f"{prompt_text}\n\n{F_MCQ_DIRECTIVE}"

    elif group == "knowledge_qa":
        if context_passages:
            ctx_str = "\n\n".join(f"Passage [{i+1}]: {p}" for i, p in enumerate(context_passages))
            user_content = f"Context:\n{ctx_str}\n\nQuestion: {prompt_text}\nAnswer in as few words as possible:"
        else:
            user_content = f"Question: {prompt_text}\nAnswer in as few words as possible:"

    elif group == "code":
        metadata = item.get("metadata", {})
        arm = item.get("arm") or metadata.get("arm", "")
        ep = metadata.get("entry_point") or item.get("entry_point", "")
        tc = metadata.get("test_code") or item.get("test_code", "")

        if arm == "public" or "mbpp" in str(item.get("template_family", "")).lower():
            first_assert = ""
            if tc:
                for line in tc.splitlines():
                    if line.strip().startswith("assert "):
                        first_assert = line.strip()
                        break
            parts = [prompt_text]
            if first_assert:
                parts.append(
                    f"Your code should satisfy the following test:\n```python\n{first_assert}\n```"
                )
            if ep:
                parts.append(f"Write a function named `{ep}`.")
            user_content = "\n\n".join(parts)
        else:
            parts = [prompt_text]
            if ep:
                parts.append(f"Define a top-level function named `{ep}`, no class.")
            user_content = "\n\n".join(parts)

    else:
        user_content = prompt_text

    return [
        {"role": "system", "content": system_text},
        {"role": "user", "content": user_content},
    ]


def compute_f_pacing_schedule() -> dict[str, Any]:
    """Compute call counts and pacing timeline for Model F evaluation."""
    # Partition counts:
    # math: 200, science_mcq: 200, knowledge_mcq: 300, code: 100, knowledge_qa: 300
    # memory_probe: 150 items evaluated twice (no_history + full_history) = 300 calls
    validation_standard_items = 200 + 200 + 300 + 100 + 300  # 1100 items
    memory_probe_calls = 150 * 2  # 300 calls
    total_calls = validation_standard_items + memory_probe_calls  # 1400 calls

    # From config/f_limits.yaml
    free_tier_daily_cap = 50
    free_tier_rpm = 2
    free_tier_days = total_calls / free_tier_daily_cap  # 28 days

    return {
        "validation_items": 1250,
        "standard_calls": validation_standard_items,
        "memory_probe_passes": 2,
        "memory_probe_calls": memory_probe_calls,
        "total_f_calls": total_calls,
        "free_tier": {
            "daily_cap": free_tier_daily_cap,
            "rpm_limit": free_tier_rpm,
            "pacing_days_required": free_tier_days,
            "estimated_cost_usd": 0.0,
        },
        "paid_tier_estimate": {
            "pacing_days_required": "1-2 days (unconstrained RPM)",
            "estimated_cost_usd": "20.00 - 30.00 USD (est. 1.2M prompt tokens, 150k output tokens)",
        },
        "status": "PREPARED_UNEXECUTED",
        "notice": F_EXECUTION_NOTICE,
    }
