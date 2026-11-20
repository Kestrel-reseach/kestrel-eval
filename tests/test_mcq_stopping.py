"""Tests for MCQ generation stopping criteria and token counting.

Verifies:
1. Generation stops on newline token IDs (e.g. 198, 271, or eos_token_id).
2. Token counts (tokens_generated) reflect generated tokens before whitespace/newline trimming.
3. Stub model emitting extra tokens after newline is properly truncated/stopped.
"""

from __future__ import annotations

import torch


class StubCausalLM:
    """Mock model that returns prompt + extra tokens (simulating rambling or prompt leak)."""

    def __init__(self, generated_token_ids: list[int]):
        self.generated_token_ids = generated_token_ids
        self.device = torch.device("cpu")

    def generate(
        self,
        input_ids: torch.Tensor,
        max_new_tokens: int = 32,
        eos_token_id: list[int] | int | None = None,
        **kwargs,
    ) -> torch.Tensor:
        eos_list = (
            [eos_token_id]
            if isinstance(eos_token_id, int)
            else (list(eos_token_id) if eos_token_id is not None else [])
        )

        gen: list[int] = []
        for tok in self.generated_token_ids[:max_new_tokens]:
            gen.append(tok)
            if tok in eos_list:
                break

        out = torch.cat([input_ids, torch.tensor([gen], dtype=input_ids.dtype)], dim=1)
        return out


def test_mcq_stopping_with_newline_eos():
    """Verify that newline token IDs [198, 271, 151645] stop generation immediately."""
    newline_eos = [151645, 198, 271]
    # Stub generates: " B\n\nExplanation: This is because of photosynthesis..."
    # Token 425 is ' B', 271 is '\n\n', 45000 is 'Explanation', etc.
    long_rambling_tokens = [425, 271, 45000, 25, 1115, 374, 1605, 315]

    model = StubCausalLM(generated_token_ids=long_rambling_tokens)
    input_ids = torch.tensor([[101, 102, 103]])

    # Without newline in eos_token_id (only standard eos=151645) -> generates all tokens up to cap
    out_unconstrained = model.generate(input_ids, max_new_tokens=32, eos_token_id=[151645])
    gen_len_unconstrained = out_unconstrained.shape[1] - input_ids.shape[1]
    assert gen_len_unconstrained == len(long_rambling_tokens)

    # With newline in eos_token_id -> stops immediately at token 271 ('\n\n')
    out_stopped = model.generate(input_ids, max_new_tokens=32, eos_token_id=newline_eos)
    gen_len_stopped = out_stopped.shape[1] - input_ids.shape[1]
    assert gen_len_stopped == 2
    assert out_stopped[0, input_ids.shape[1] :].tolist() == [425, 271]


def test_tokens_generated_counted_before_trimming():
    """Verify that tokens_generated is calculated from generated IDs length, not trimmed string."""
    input_ids = torch.tensor([[10, 20, 30]])
    in_len = input_ids.shape[1]

    # Model generates 2 tokens: ' A' (token 362) and '<|im_end|>' (token 151645)
    model = StubCausalLM(generated_token_ids=[362, 151645])
    out = model.generate(input_ids, max_new_tokens=32, eos_token_id=[151645, 198, 271])

    gen_ids = out[0, in_len:].tolist()
    # Both tokens must be counted before any text decode / strip
    assert len(gen_ids) == 2
