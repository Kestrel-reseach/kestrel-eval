"""Unit tests for baseline evaluation engine and B-LLM selection (Step 2 Part 4b)."""

from pathlib import Path

from evaluation.baselines_evaluator import (
    generate_baseline_table,
    load_validation_items,
    run_candidate_evaluation,
)
from evaluation.metrics import MANDATORY_ENERGY_LABEL


def test_load_validation_items():
    """Verify loading the validation partition loads exactly 1,250 items (Suite v2.1 per D16)."""
    items = load_validation_items()
    assert len(items) == 1250
    groups = {item.get("group") for item in items}
    assert groups == {
        "math",
        "science_mcq",
        "knowledge_mcq",
        "code",
        "knowledge_qa",
        "memory_probe",
    }


def test_candidate_evaluation_run(tmp_path: Path):
    """Verify evaluation run produces valid summary and JSONL records."""
    # Test on a small slice of items for speed
    items = load_validation_items()[:10]
    summary = run_candidate_evaluation(
        candidate_id="qwen2.5-0.5b-instruct-q4",
        items=items,
        output_dir=tmp_path,
        use_retrieval=False,
    )
    assert summary.candidate_id == "qwen2.5-0.5b-instruct-q4"
    assert 0.0 <= summary.overall_accuracy <= 1.0
    assert summary.resident_vram_gb == 0.45
    assert len(summary.raw_records) == 10

    # Verify JSONL file exists
    jsonl_files = list(tmp_path.glob("*.jsonl"))
    assert len(jsonl_files) == 1


def test_baseline_table_mandatory_labels():
    """Verify baseline comparison table contains both required labels."""
    items = load_validation_items()[:5]
    summary = run_candidate_evaluation(
        candidate_id="qwen2.5-1.5b-instruct-q4",
        items=items,
        output_dir=Path("/tmp/kestrel_test_baselines"),
    )
    table = generate_baseline_table({"qwen2.5-1.5b-instruct-q4": summary})

    assert MANDATORY_ENERGY_LABEL in table
    assert "F = gemini-2.5-pro (free tier)" in table
    assert "B-LLM (Chosen)" in table
