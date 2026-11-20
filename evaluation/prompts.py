"""Prompt formatting and chat templates for Kestrel evaluation suites.

Protocol: Step 2 Part 4R (Real Autoregressive Inference).
Standardizes prompt construction across all 6 suite groups:
- math: Chain-of-thought instructions ending with explicit 'Final Answer: <number>'. Cap: 512.
- science_mcq & knowledge_mcq: Option selection with 'Answer:' prefill and newline stop. Cap: 8.
- code: Instructions to return only one python code block without explanation. Cap: 1024.
- knowledge_qa: Factual QA with context passages strictly from BM25 retrieval (NO gold passage). Cap: 64.
- memory_probe: Personal memory retrieval from chronological log. Cap: 64.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any


def get_system_prompt_for_group(group: str) -> str:
    """Return canonical system instruction for a task group."""
    if group == "math":
        return (
            "You are an expert mathematician. Solve the following word problem step by step. "
            "Show your reasoning clearly, and on the very last line state your final answer in the format:\n"
            "Final Answer: <number>"
        )
    if group in ("science_mcq", "knowledge_mcq"):
        return (
            "You are an expert assistant. Solve the following multiple choice question by selecting "
            "the single best option (A, B, C, or D). State the option letter directly."
        )
    if group == "code":
        return (
            "You are an expert Python software engineer. Write the Python code to implement the requested function. "
            "Return only one python code block, no explanation."
        )
    if group == "knowledge_qa":
        return (
            "You are a factual question answering assistant. Answer the question accurately and concisely "
            "based on the provided context if available, or your knowledge. Give the direct factual answer."
        )
    if group == "memory_probe":
        return (
            "You are an assistant with access to personal history logs. Review the chronological log and answer "
            "the question using the most recent and up-to-date information. State the direct answer clearly and concisely."
        )
    return "You are a helpful, accurate, and concise AI assistant."


def get_assistant_prefill(group: str) -> str | None:
    """Return prompt prefill for the assistant turn if applicable."""
    if group in ("science_mcq", "knowledge_mcq"):
        return "Answer:"
    return None


def extract_question_text(item: dict[str, Any]) -> str:
    """Extract standalone question string from item, stripping any baked passages."""
    if item.get("question"):
        return str(item["question"]).strip()

    prompt = item.get("prompt", "")
    m = re.search(r"Question:\s*(.*?)(?:\nAnswer:|$)", prompt, re.DOTALL)
    if m:
        return m.group(1).strip()
    return prompt.strip()


def format_user_prompt(
    item: dict[str, Any],
    *,
    use_retrieval: bool = True,
    retriever: Any | None = None,
) -> str:
    """Extract and format the user content for an item.

    Crucial: For knowledge_qa, when use_retrieval=False, the prompt contains ONLY the question
    (zero passages). When use_retrieval=True, it contains ONLY the retrieved passages from the store.
    The gold passage is NEVER leaked into the prompt.
    """
    group = item.get("group", "")

    if group == "knowledge_qa":
        question = extract_question_text(item)
        if use_retrieval and retriever is not None:
            prompt, _ = retriever.augment_knowledge_qa_prompt(item, top_k=3)
            return prompt
        # No retrieval: pure standalone question
        return f"Question: {question}\nAnswer:"

    if group == "code":
        base_prompt = item.get("prompt", "").strip()
        metadata = item.get("metadata", {})
        arm = item.get("arm") or metadata.get("arm", "")
        entry_point = metadata.get("entry_point") or item.get("entry_point", "")
        test_code = metadata.get("test_code") or item.get("test_code", "")

        # Standard MBPP style: show function name and first test assertion
        if arm == "public" or "mbpp" in str(item.get("template_family", "")).lower():
            first_assertion = ""
            if test_code:
                for line in test_code.splitlines():
                    clean_l = line.strip()
                    if clean_l.startswith("assert "):
                        first_assertion = clean_l
                        break
            parts = [base_prompt]
            if first_assertion:
                parts.append(f"Your code should satisfy the following test:\n```python\n{first_assertion}\n```")
            if entry_point:
                parts.append(f"Write a function named `{entry_point}`.")
            return "\n\n".join(parts)

        # Synthetic style: explicit top-level function instruction
        elif arm == "synthetic":
            parts = [base_prompt]
            if entry_point:
                parts.append(f"Define a top-level function named `{entry_point}`, no class.")
            return "\n\n".join(parts)

        return base_prompt

    return item.get("prompt", "")


def build_chat_messages(
    item: dict[str, Any],
    *,
    use_retrieval: bool = True,
    retriever: Any | None = None,
) -> list[dict[str, str]]:
    """Build OpenAI/HF standard list of message dicts: system + user."""
    group = item.get("group", "")
    system_text = get_system_prompt_for_group(group)
    user_text = format_user_prompt(item, use_retrieval=use_retrieval, retriever=retriever)

    return [
        {"role": "system", "content": system_text},
        {"role": "user", "content": user_text},
    ]


def format_prompt_for_model(
    item: dict[str, Any],
    tokenizer: Any | None = None,
    *,
    use_retrieval: bool = True,
    retriever: Any | None = None,
) -> tuple[str, str, str | None]:
    """Format full prompt string and return (prompt_str, prompt_sha256, assistant_prefill).

    If assistant turn prefill is defined (e.g. 'Answer:' for MCQ), appends it directly to prompt_str.
    """
    group = item.get("group", "")
    messages = build_chat_messages(item, use_retrieval=use_retrieval, retriever=retriever)
    prefill = get_assistant_prefill(group)

    if tokenizer is not None and hasattr(tokenizer, "apply_chat_template"):
        try:
            prompt_str = tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
            )
        except Exception:  # noqa: BLE001
            prompt_str = _fallback_format_messages(messages)
    else:
        prompt_str = _fallback_format_messages(messages)

    if prefill:
        prompt_str = prompt_str + prefill

    prompt_hash = hashlib.sha256(prompt_str.encode("utf-8")).hexdigest()
    return prompt_str, prompt_hash, prefill


def _fallback_format_messages(messages: list[dict[str, str]]) -> str:
    """Fallback plain string representation if no chat template is available."""
    lines = []
    for m in messages:
        role = m["role"].upper()
        content = m["content"].strip()
        lines.append(f"[{role}]\n{content}\n")
    lines.append("[ASSISTANT]\n")
    return "\n".join(lines)
