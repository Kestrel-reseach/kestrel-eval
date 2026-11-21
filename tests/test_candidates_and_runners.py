"""Unit tests for candidates, local runner, and RunMatrix integration (Step 2 Part 4b)."""

from pathlib import Path

from evaluation.candidates import (
    CANDIDATE_SHORTLIST,
    get_candidate,
    list_gpu_candidates,
    verify_vram_budget,
)
from evaluation.retrieval import BM25Retriever
from evaluation.run_matrix import RunConfig, RunMatrix
from evaluation.runners.local_runner import LocalRunner
from evaluation.schema import validate_record


def test_candidate_shortlist_budget_verification():
    """Verify GPU candidate models fit the 1.5 GB VRAM budget."""
    gpu_candidates = list_gpu_candidates(max_budget_gb=1.5)
    assert len(gpu_candidates) >= 2

    # Qwen2.5-0.5B and Qwen2.5-1.5B must fit
    c_05 = get_candidate("qwen2.5-0.5b-instruct-q4")
    assert verify_vram_budget(c_05, 1.5) is True
    assert c_05.estimated_4bit_vram_gb <= 1.5

    c_15 = get_candidate("qwen2.5-1.5b-instruct-q4")
    assert verify_vram_budget(c_15, 1.5) is True
    assert c_15.estimated_4bit_vram_gb <= 1.5

    # 3B model must exceed GPU assistant budget (CPU tier only)
    c_3b = get_candidate("qwen2.5-3b-instruct-q4")
    assert verify_vram_budget(c_3b, 1.5) is False
    assert c_3b.tier == "cpu"


def test_candidate_metadata_fields():
    """Verify all candidates have required license, context, and revision."""
    for c in CANDIDATE_SHORTLIST.values():
        assert c.license in ("Apache-2.0", "Llama 3.2 Community")
        assert c.context_length == 2048
        assert c.revision_hash


def test_local_runner_retrieval_diagnostic(tmp_path: Path):
    """Verify local runner records retrieval hits and bytes read for knowledge_qa."""
    corpus_path = Path("data/wikipedia_abstracts_5k.jsonl")
    retriever = BM25Retriever.from_jsonl(corpus_path) if corpus_path.exists() else None

    # Test with retrieval
    runner_with = LocalRunner(
        candidate="qwen2.5-0.5b-instruct-q4",
        retriever=retriever,
        use_retrieval=True,
        mock_mode=True,
    )
    item = {
        "item_id": "knowledge_qa_001",
        "group": "knowledge_qa",
        "question": "When was Bartolomeo Ammannati born?",
        "target": "18 June 1511",
        "answer_check": "key_match",
    }
    res_with = runner_with.run_item(item)
    if retriever:
        assert res_with["retrieval_hits"] == 3
        assert res_with["bytes_read_from_ssd"] > 0
    assert res_with["correct"] is True

    # Test without retrieval (diagnostic baseline)
    runner_without = LocalRunner(
        candidate="qwen2.5-0.5b-instruct-q4",
        retriever=retriever,
        use_retrieval=False,
        mock_mode=True,
    )
    res_without = runner_without.run_item(item)
    assert res_without["retrieval_hits"] == 0
    assert res_without["bytes_read_from_ssd"] == 0


def test_run_matrix_checkpointing_and_validation(tmp_path: Path):
    """Verify RunMatrix with LocalRunner outputs valid JSONL and respects checkpoints."""
    output_file = tmp_path / "test_run.jsonl"
    config = RunConfig(
        run_id="run-step2-test-001",
        git_commit="abc1234",
        seed=20260102,
        split="validation",
        system="B_LLM",
        output_path=output_file,
        energy_status="relative_only",
    )
    runner = LocalRunner(
        candidate="qwen2.5-0.5b-instruct-q4",
        mock_mode=True,
    )
    matrix = RunMatrix(config, runner=runner)

    items = [
        {
            "item_id": "math_001",
            "group": "math",
            "prompt": "Compute 5 * 5",
            "target": "25",
            "answer_check": "exact_numeric",
        },
        {
            "item_id": "science_mcq_001",
            "group": "science_mcq",
            "prompt": "Which planet is closest to the Sun?\nA) Venus\nB) Mercury\nC) Mars\nD) Earth\nAnswer:",
            "target": "B",
            "answer_check": "answer_key",
        },
    ]

    # First run
    records = matrix.run(items)
    assert len(records) == 2
    for r in records:
        assert r["correct"] is True
        errs = validate_record(r, expected_config_hash=config.config_hash)
        assert errs == []

    # Second run should skip already checkpointed items
    records_second = matrix.run(items)
    assert len(records_second) == 0
