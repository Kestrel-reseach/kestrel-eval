"""Prompt formatting and chat templates for Kestrel evaluation suites.

Protocol: Step 2 Part 4R (Real Autoregressive Inference).
Standardizes prompt construction across all 6 suite groups:
- math: Chain-of-thought instructions ending with explicit 'Final Answer: <number>'.
- science_mcq & knowledge_mcq: Option selection instructions ending with 'Answer: <letter>'.
- code: Instructions to implement function inside a ```python ``` code block.
- knowledge_qa: Factual QA with context passages (BM25 retrieval or golden passage).
- memory_probe: Personal memory retrieval from chronological log.
"""

from __future__ import annotations

import hashlib
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
            "the single best option (A, B, C, or D).\n"
            "State your reasoning briefly if needed, and on the very last line conclude with your final choice in the format:\n"
            "Answer: <letter>"
        )
    if group == "code":
        return (
            "You are an expert Python software engineer. Write the Python code to implement the requested function. "
            "Include any necessary helper functions. Place your complete code inside a single ```python ... ``` code block."
        )
    if group == "knowledge_qa":
        return (
            "You are a factual question answering assistant. Answer the question accurately and concisely "
            "based on the provided passage. Give the direct factual answer."
        )
    if group == "memory_probe":
        return (
            "You are an assistant with access to personal history logs. Review the chronological log and answer "
            "the question using the most recent and up-to-date information. State the direct answer clearly and concisely."
        )
    return "You are a helpful, accurate, and concise AI assistant."


def format_user_prompt(
    item: dict[str, Any],
    *,
    use_retrieval: bool = True,
    retriever: Any | None = None,
) -> str:
    """Extract and format the user content for an item, applying retrieval if needed."""
    group = item.get("group", "")

    if group == "knowledge_qa" and use_retrieval and retriever is not None:
        prompt, _ = retriever.augment_knowledge_qa_prompt(item, top_k=3)
        return prompt

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
) -> tuple[str, str]:
    """Format full prompt string and return (prompt_str, prompt_sha256).

    If tokenizer has apply_chat_template, applies it with add_generation_prompt=True.
    Otherwise formats a clean markdown/text representation.
    """
    messages = build_chat_messages(item, use_retrieval=use_retrieval, retriever=retriever)

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

    prompt_hash = hashlib.sha256(prompt_str.encode("utf-8")).hexdigest()
    return prompt_str, prompt_hash


def _fallback_format_messages(messages: list[dict[str, str]]) -> str:
    """Fallback plain string representation if no chat template is available."""
    lines = []
    for m in messages:
        role = m["role"].upper()
        content = m["content"].strip()
        lines.append(f"[{role}]\n{content}\n")
    lines.append("[ASSISTANT]\n")
    return "\n".join(lines)
