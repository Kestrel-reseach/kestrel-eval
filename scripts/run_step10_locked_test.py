#!/usr/bin/env python3
"""Step 10: One-time locked-test evaluation runner for F, B-LLM, and P1.

Runs strictly once on the private locked-test partition in KESTREL_PRIVATE_DIR:
  1. Verifies SHA-256 hashes and manifest root hash against evaluation/manifest.yaml.
  2. Executes F (gemini-flash-lite-latest, free tier, D21/D11/D12) on 1,250 items
     plus no_history memory_probe dual pass (150 items).
  3. Executes B-LLM (Qwen/Qwen2.5-1.5B-Instruct 4-bit NF4, canonical prompts,
     BM25 retriever over Wikipedia + fictional locked passages) on RTX 3050.
  4. Executes P1 Integrated (Step 7 frozen config: Qwen2.5-1.5B NF4 + Step 3 verifier
     head + Step 4 fixed two-pass on checkable + Step 5 SSD KnowledgeStore + Step 6
     WriteGatedMemory) on RTX 3050.
  5. Writes per-item JSONL provenance strictly out-of-repo (KESTREL_PRIVATE_DIR/step10_runs)
     and writes ONLY privacy-clean aggregates, CIs, paired deltas, energy, residency,
     latency, and gate verdicts to reports/locked_test_step10.json.

Do NOT print, commit, or export locked-test item text, prompts, or answers.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from evaluation.extractors import (  # noqa: E402
    extract_answer_for_group,
    score_frozen_exact_match,
)
from evaluation.generators.stale_fact_scorer import score_memory_probe_response  # noqa: E402
from evaluation.metrics import (  # noqa: E402
    MANDATORY_ENERGY_LABEL,
    cluster_bootstrap_ci,
    compute_cluster_icc,
    paired_bootstrap_ci,
    percentile_latency,
)
from evaluation.prompts import format_prompt_for_model  # noqa: E402
from evaluation.retrieval import BM25Retriever  # noqa: E402
from evaluation.runners.frontier_runner import FrontierConfig, FrontierRunner  # noqa: E402
from evaluation.suite import (  # noqa: E402
    GROUPS,
    compute_file_sha256,
    compute_root_hash,
    get_private_dir,
)

MANIFEST_ROOT_HASH = "15be5befee80bde2c624d06cd2b8826475e13bb3f45298be1ced584a884e6fa5"
LOCKED_TEST_HASHES = {
    "math": "2516fc845447352775e891845c2e1fcee4a6c02399aba3d4e69f737093fe9c51",
    "science_mcq": "aef023c27437e13fbe4af271aa589ac6f140ccbd72ea5c8177b7ee6e3313fcc6",
    "knowledge_mcq": "d83ce8a19a891dd159bff24d48b1bc5a9d250ddeb625387a5656859693c0799e",
    "code": "e807c55ff462535e80b81ee8cf640733c67abe2997ed86e44ec91511c066c20e",
    "knowledge_qa": "e1147853c87a5ac141dec5b77fd8373c926387c6ae087d93fd58cfd31d0c78ca",
    "memory_probe": "5468373aa172f81c9b4291e279cb74996a729911a48ff36341a10f84ba2dc0af",
}

CHECKABLE_GROUPS = ("math", "science_mcq", "knowledge_mcq", "code")
STORE_GROUP = "knowledge_qa"
MEMORY_GROUP = "memory_probe"

B_LLM_MODEL = "Qwen/Qwen2.5-1.5B-Instruct"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
IDLE_BASELINE_POWER_W = 6.1444  # Step 0 RTX 3050 formal baseline
MANIFEST_VERSION = "2.3"
CONTEXT_LENGTH = 2048
SEED_BLLM = 20260102
SEED_P1 = 20260107
SEED_SUMMARY = 20260102

GROUP_CAPS: dict[str, int] = {
    "math": 768,
    "science_mcq": 32,
    "knowledge_mcq": 32,
    "code": 1024,
    "knowledge_qa": 128,
    "memory_probe": 128,
}

F_REFERENCE_LABEL = (
    "F = gemini-flash-lite-latest (gemini-3.5-flash-lite, Google AI Studio free tier, D21); "
    "a free-tier reference, not the current frontier."
)


def wilson_ci_95(correct: int, total: int, z: float = 1.95996) -> list[float]:
    """Compute 95% Wilson score interval in percentage points."""
    if total <= 0:
        return [0.0, 0.0]
    p = correct / total
    denom = 1.0 + (z**2) / total
    center = (p + (z**2) / (2.0 * total)) / denom
    half = (z * math.sqrt((p * (1.0 - p)) / total + (z**2) / (4.0 * (total**2)))) / denom
    return [
        round(max(0.0, (center - half) * 100.0), 2),
        round(min(100.0, (center + half) * 100.0), 2),
    ]


def verify_and_load_locked_test(private_dir: Path) -> list[dict[str, Any]]:
    """Verify SHA-256 hashes of all locked-test files and load 1,250 items."""
    locked_dir = private_dir / "locked_test"
    if not locked_dir.is_dir():
        raise FileNotFoundError(f"Locked-test directory not found: {locked_dir}")

    observed_hashes: dict[str, str] = {}
    items: list[dict[str, Any]] = []
    for group in GROUPS:
        path = locked_dir / f"{group}.jsonl"
        if not path.is_file():
            raise FileNotFoundError(f"Missing locked-test file: {path}")
        digest = compute_file_sha256(path)
        expected = LOCKED_TEST_HASHES[group]
        if digest != expected:
            raise ValueError(
                f"SHA-256 mismatch for locked_test/{group}.jsonl: got {digest}, expected {expected}"
            )
        observed_hashes[group] = digest
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    items.append(json.loads(line))

    root_digest = compute_root_hash(observed_hashes)
    if root_digest != MANIFEST_ROOT_HASH:
        raise ValueError(f"Root hash mismatch: got {root_digest}, expected {MANIFEST_ROOT_HASH}")
    if len(items) != 1250:
        raise ValueError(f"Expected 1,250 locked-test items, loaded {len(items)}")
    return items


def load_jsonl_by_id(path: Path) -> dict[str, dict[str, Any]]:
    """Load checkpoint JSONL records keyed by item_id."""
    recs: dict[str, dict[str, Any]] = {}
    if not path.is_file():
        return recs
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rec = json.loads(line)
                iid = rec.get("item_id")
                if iid:
                    recs[str(iid)] = rec
    return recs


def _count_by(values: list[str]) -> dict[str, int]:
    """Count occurrences of each string value, sorted for reproducible reports."""
    counts: dict[str, int] = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def _require_full_locked_scope(limit: int | None, phase: str) -> None:
    """Refuse to emit a Step 10 summary from a partial --limit run."""
    if limit is not None and phase in ("all", "summarize"):
        raise RuntimeError(
            "Refusing to write a Step 10 locked-test summary with --limit; "
            "reports must cover all 1,250 items."
        )


def run_f_locked(
    items: list[dict[str, Any]],
    runs_dir: Path,
    *,
    limit: int | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Run F (gemini-flash-lite-latest) once on locked-test items (D12/D21/D11)."""
    runs_dir.mkdir(parents=True, exist_ok=True)
    main_path = runs_dir / "f_locked_test.jsonl"
    no_hist_path = runs_dir / "f_locked_memory_no_history.jsonl"

    cfg = FrontierConfig.from_yaml(REPO_ROOT / "config" / "f_limits.yaml")
    runner = FrontierRunner(config=cfg, history_mode="full_history", mock_mode=False)
    if runner.api_key_status != "READY":
        raise RuntimeError("GEMINI_API_KEY not found; cannot run real F on locked_test")

    eval_items = items[:limit] if limit else items
    existing = load_jsonl_by_id(main_path)
    print(f"[F] Loaded {len(existing)}/{len(eval_items)} existing main records.", flush=True)

    for idx, item in enumerate(eval_items, 1):
        iid = str(item["item_id"])
        if iid in existing:
            continue
        res = runner.run_item(item)
        rec = {
            "item_id": iid,
            "group": item.get("group"),
            "arm": item.get("arm") or item.get("metadata", {}).get("arm", "unknown"),
            "correct": bool(res["correct"]),
            "wall_time_ms": res["wall_time_ms"],
            "tokens_generated": res["tokens_generated"],
            "response_id": res["response_id"],
            "model_version": res["model_version"],
            "execution_date": res["execution_date"],
            # FrontierRunner does not return/score stale_fact_error; keep None rather than False.
            "stale_fact_error": None,
            "metadata": {
                "entity": item.get("metadata", {}).get("entity"),
                "attribute": item.get("metadata", {}).get("attribute"),
                "is_stale_fact": bool(item.get("metadata", {}).get("is_stale_fact", False)),
            },
        }
        existing[iid] = rec
        with main_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(rec) + "\n")
        if idx % 25 == 0 or idx == len(eval_items):
            acc = sum(1 for r in existing.values() if r["correct"]) / len(existing) * 100.0
            print(f"  [F main] {len(existing)}/{len(eval_items)} acc={acc:.2f}%", flush=True)

    # Dual memory_probe pass (no_history)
    mem_items = [it for it in eval_items if it.get("group") == MEMORY_GROUP]
    no_hist_runner = FrontierRunner(config=cfg, history_mode="no_history", mock_mode=False)
    existing_nh = load_jsonl_by_id(no_hist_path)
    print(f"[F no_history] Loaded {len(existing_nh)}/{len(mem_items)} records.", flush=True)

    for idx, item in enumerate(mem_items, 1):
        iid = str(item["item_id"])
        if iid in existing_nh:
            continue
        res = no_hist_runner.run_item(item)
        rec = {
            "item_id": iid,
            "group": MEMORY_GROUP,
            "arm": item.get("arm", "synthetic"),
            "correct": bool(res["correct"]),
            "wall_time_ms": res["wall_time_ms"],
            "tokens_generated": res["tokens_generated"],
            "response_id": res["response_id"],
            "model_version": res["model_version"],
            "execution_date": res["execution_date"],
        }
        existing_nh[iid] = rec
        with no_hist_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(rec) + "\n")
        if idx % 25 == 0 or idx == len(mem_items):
            acc = sum(1 for r in existing_nh.values() if r["correct"]) / len(existing_nh) * 100.0
            print(
                f"  [F no_history] {len(existing_nh)}/{len(mem_items)} acc={acc:.2f}%", flush=True
            )

    return [existing[str(it["item_id"])] for it in eval_items], [
        existing_nh[str(it["item_id"])] for it in mem_items
    ]


def _load_4bit_qwen(device: str = "cuda:0") -> tuple[Any, Any, float]:
    """Load Qwen2.5-1.5B-Instruct in 4-bit NF4 and return (model, tokenizer, vram_mb)."""
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

    from evaluation.metrics import get_vram_breakdown_mb

    tokenizer = AutoTokenizer.from_pretrained(B_LLM_MODEL, local_files_only=True)
    bnb_cfg = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=torch.float16,
    )
    model = AutoModelForCausalLM.from_pretrained(
        B_LLM_MODEL,
        quantization_config=bnb_cfg,
        device_map=device,
        trust_remote_code=True,
        local_files_only=True,
    )
    model.eval()
    _ = model.generate(torch.tensor([[100, 200]], device=model.device), max_new_tokens=2)
    torch.cuda.synchronize()
    vram_info = get_vram_breakdown_mb()
    vram_mb = float(vram_info.get("nvml_process_used_mb") or 1416.0)
    return model, tokenizer, vram_mb


def run_bllm_locked(
    items: list[dict[str, Any]],
    private_dir: Path,
    runs_dir: Path,
    *,
    device: str = "cuda:0",
    seed: int = SEED_BLLM,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """Run B-LLM (Qwen2.5-1.5B NF4, canonical prompts, BM25) once on locked test."""
    runs_dir.mkdir(parents=True, exist_ok=True)
    out_jsonl = runs_dir / "bllm_locked_test.jsonl"
    eval_items = items[:limit] if limit else items
    existing = load_jsonl_by_id(out_jsonl)
    if len(existing) == len(eval_items):
        print(f"[B-LLM] Loaded all {len(existing)} cached records.", flush=True)
        return [existing[str(it["item_id"])] for it in eval_items]

    import torch

    from energy.harness import read_gpu_energy_mj

    corpus_paths = [
        REPO_ROOT / "data" / "wikipedia_abstracts_5k.jsonl",
        private_dir / "fictional_locked_passages.jsonl",
    ]
    retriever = BM25Retriever.from_jsonl([p for p in corpus_paths if p.is_file()])
    print(f"[B-LLM] BM25 indexed {len(retriever.docs)} corpus documents.", flush=True)

    random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

    model, tokenizer, vram_mb = _load_4bit_qwen(device=device)
    print(f"[B-LLM] Post-warmup NVML VRAM: {vram_mb:.1f} MB", flush=True)

    done = 0
    for _idx, item in enumerate(eval_items, 1):
        iid = str(item["item_id"])
        if iid in existing:
            continue

        group = str(item.get("group", ""))
        cap = GROUP_CAPS.get(group, 128)
        prompt_str, _, _ = format_prompt_for_model(
            item, tokenizer=tokenizer, use_retrieval=True, retriever=retriever
        )
        inputs = tokenizer(prompt_str, return_tensors="pt").to(model.device)
        in_len = inputs.input_ids.shape[1]

        gen_kwargs: dict[str, Any] = {
            "max_new_tokens": cap,
            "do_sample": False,
            "pad_token_id": tokenizer.eos_token_id,
        }
        if group in ("science_mcq", "knowledge_mcq"):
            gen_kwargs["eos_token_id"] = [tokenizer.eos_token_id, 198, 271]

        torch.cuda.synchronize()
        mj0 = read_gpu_energy_mj()
        t0 = time.perf_counter()
        with torch.no_grad():
            out = model.generate(**inputs, **gen_kwargs)
        torch.cuda.synchronize()
        t1 = time.perf_counter()
        mj1 = read_gpu_energy_mj()

        wall_ms = (t1 - t0) * 1000.0
        gross_j = max(0.0, (mj1 - mj0) / 1000.0)
        net_j = max(0.0, gross_j - IDLE_BASELINE_POWER_W * (wall_ms / 1000.0))
        gen_len = int(len(out[0]) - in_len)
        raw_output = tokenizer.decode(out[0][in_len:], skip_special_tokens=True).strip()

        _, is_correct = extract_answer_for_group(item, raw_output)
        stale_error = False
        if group == MEMORY_GROUP:
            stale_vals = item.get("stale_values") or item.get("metadata", {}).get(
                "stale_values", []
            )
            is_stale = bool(item.get("metadata", {}).get("is_stale_fact", False))
            mem_score = score_memory_probe_response(
                prediction=raw_output,
                target=str(item.get("target", "")),
                stale_values=stale_vals,
                is_stale_fact_item=is_stale,
            )
            stale_error = bool(mem_score["stale_fact_error"])

        rec = {
            "item_id": iid,
            "group": group,
            "arm": item.get("arm") or item.get("metadata", {}).get("arm", "unknown"),
            "correct": bool(is_correct),
            "stale_fact_error": stale_error,
            "tokens_generated": gen_len,
            "truncated": gen_len >= cap,
            "wall_time_ms": round(wall_ms, 2),
            "gross_energy_joules": round(gross_j, 4),
            "net_energy_joules": round(net_j, 4),
            "nvml_process_vram_mb": vram_mb,
            "metadata": {
                "entity": item.get("metadata", {}).get("entity"),
                "attribute": item.get("metadata", {}).get("attribute"),
                "is_stale_fact": bool(item.get("metadata", {}).get("is_stale_fact", False)),
            },
        }
        existing[iid] = rec
        with out_jsonl.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(rec) + "\n")
        done += 1
        if done % 25 == 0 or len(existing) == len(eval_items) or done <= 3:
            acc = sum(1 for r in existing.values() if r["correct"]) / len(existing) * 100.0
            print(
                f"  [B-LLM] {len(existing)}/{len(eval_items)} ({group}): "
                f"acc={acc:.2f}% net_E={net_j:.2f}J lat={wall_ms:.0f}ms",
                flush=True,
            )

    return [existing[str(it["item_id"])] for it in eval_items]


def run_p1_locked(
    items: list[dict[str, Any]],
    kestrel_dir: Path,
    private_dir: Path,
    runs_dir: Path,
    *,
    device: str = "cuda:0",
    seed: int = SEED_P1,
    limit: int | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Run P1 Integrated (Step 7 frozen config) once on locked test."""
    if str(kestrel_dir) not in sys.path:
        sys.path.insert(0, str(kestrel_dir))

    from kestrel.knowledge_store import Chunk, KnowledgeStore
    from kestrel.memory_gated import MemoryEntry, WriteGatedMemory
    from kestrel.router import (
        CalibratedVerifierAdapter,
        GatedMemoryAdapter,
        KnowledgeStoreRetriever,
        Router,
    )
    from kestrel.verifier import VerifierExample, VerifierFeatures, temperature_scale
    from kestrel.verifier_numpy import NumpyLogisticHead

    runs_dir.mkdir(parents=True, exist_ok=True)
    out_jsonl = runs_dir / "p1_locked_test.jsonl"
    eval_items = items[:limit] if limit else items
    existing = load_jsonl_by_id(out_jsonl)

    # Build/load locked SSD KnowledgeStore outside git repo
    store_dir = runs_dir / "locked_store_index"
    store_meta: dict[str, Any] = {}
    if len(existing) == len(eval_items) and (store_dir / "vectors.bin").is_file():
        print(f"[P1] Loaded all {len(existing)} cached records.", flush=True)
        store_obj = KnowledgeStore(store_dir)
        store_obj.load_chunks()
        store_meta = {
            "disk_bytes": store_obj.disk_bytes,
            "resident_bytes": store_obj.resident_bytes,
            "corpus_chunks": len(store_obj._chunks),
        }
        return [existing[str(it["item_id"])] for it in eval_items], store_meta

    # Fit Step 3 verifier head. The train feature cache is gitignored, so only
    # load it when there are uncached records to score.
    train_cache = kestrel_dir / "reports" / ".cache_train_examples.jsonl"
    step3_json = kestrel_dir / "reports" / "verifier_step3.json"
    train_ex = [
        VerifierExample(
            item_id=d["item_id"],
            split="train",
            features=VerifierFeatures(last_token_hidden=tuple(d["features"]["last_token_hidden"])),
            correct=bool(d["correct"]),
        )
        for d in map(json.loads, train_cache.open(encoding="utf-8"))
    ]
    head = NumpyLogisticHead()
    head.fit(train_ex)
    temp = float(json.loads(step3_json.read_text(encoding="utf-8")).get("temperature", 2.0))

    import torch
    from transformers import AutoModel, AutoTokenizer

    from energy.harness import read_gpu_energy_mj

    class MiniLMCPU:
        def __init__(self, model_id: str = EMBEDDING_MODEL) -> None:
            self.tok = AutoTokenizer.from_pretrained(model_id, local_files_only=True)
            self.mod = AutoModel.from_pretrained(model_id, local_files_only=True)
            self.mod.eval()
            self._dim = int(self.mod.config.hidden_size)
            self._cache: dict[str, tuple[float, ...]] = {}

        @property
        def dimension(self) -> int:
            return self._dim

        def precompute_batch(self, texts: list[str], batch_size: int = 64) -> None:
            uncached = [t for t in texts if t not in self._cache]
            for i in range(0, len(uncached), batch_size):
                batch = uncached[i : i + batch_size]
                inp = self.tok(
                    batch, return_tensors="pt", padding=True, truncation=True, max_length=128
                )
                with torch.no_grad():
                    out = self.mod(**inp)
                    mask = inp["attention_mask"].unsqueeze(-1).expand(out[0].size()).float()
                    emb = torch.sum(out[0] * mask, 1) / torch.clamp(mask.sum(1), min=1e-9)
                    emb = torch.nn.functional.normalize(emb, p=2, dim=1)
                    for txt, vec in zip(batch, emb):
                        self._cache[txt] = tuple(float(x) for x in vec)

        def vectorize(self, text: str) -> tuple[float, ...]:
            if text in self._cache:
                return self._cache[text]
            inp = self.tok(text, return_tensors="pt", truncation=True, max_length=128)
            with torch.no_grad():
                out = self.mod(**inp)
                mask = inp["attention_mask"].unsqueeze(-1).expand(out[0].size()).float()
                emb = torch.sum(out[0] * mask, 1) / torch.clamp(mask.sum(1), min=1e-9)
                emb = torch.nn.functional.normalize(emb, p=2, dim=1)
                vec = tuple(float(x) for x in emb[0])
                self._cache[text] = vec
                return vec

    vectorizer = MiniLMCPU()
    store = KnowledgeStore(store_dir, vectorizer)
    if not (store.vectors_path.is_file() and store.chunks_path.is_file()):
        chunks: list[Chunk] = []
        for src_name, path in (
            ("wikipedia", REPO_ROOT / "data" / "wikipedia_abstracts_5k.jsonl"),
            ("fictional", private_dir / "fictional_locked_passages.jsonl"),
        ):
            if path.is_file():
                for line in path.open(encoding="utf-8"):
                    if line.strip():
                        d = json.loads(line)
                        txt = f"{d.get('title', '')}: {d.get('abstract', '')}".strip()
                        chunks.append(Chunk(chunk_id=d["article_id"], text=txt, source=src_name))
        print(f"[P1] Building locked SSD KnowledgeStore ({len(chunks)} chunks)...", flush=True)
        vectorizer.precompute_batch([c.text for c in chunks], batch_size=64)
        store.build(chunks)
    else:
        store.load_chunks()

    store_meta = {
        "disk_bytes": store.disk_bytes,
        "resident_bytes": store.resident_bytes,
        "corpus_chunks": len(store._chunks),
    }

    # Verify Router wiring conforms to Step 7 contract
    _ = Router(
        verifier=CalibratedVerifierAdapter(head=head, temperature=temp),
        retriever=KnowledgeStoreRetriever(store),
        memory=GatedMemoryAdapter(WriteGatedMemory(write_threshold=0.5)),
        threshold=0.5,
        abstain_below=0.1,
    )

    model, tokenizer, vram_mb = _load_4bit_qwen(device=device)
    print(f"[P1] Post-warmup NVML VRAM: {vram_mb:.1f} MB", flush=True)

    done = 0
    for _idx, item in enumerate(eval_items, 1):
        iid = str(item["item_id"])
        if iid in existing:
            continue
        group = str(item.get("group", ""))
        arm = item.get("arm") or item.get("metadata", {}).get("arm", "unknown")

        if group in CHECKABLE_GROUPS:
            prompt_str, _, _ = format_prompt_for_model(item, tokenizer=tokenizer)
            inputs = tokenizer(prompt_str, return_tensors="pt").to(model.device)
            plen = inputs.input_ids.shape[1]
            cap = GROUP_CAPS[group]
            is_mcq = group in ("science_mcq", "knowledge_mcq")
            eos_ids = [tokenizer.eos_token_id, 198, 271] if is_mcq else tokenizer.eos_token_id

            torch.manual_seed(
                seed + int(iid.split("_")[-1]) if iid.split("_")[-1].isdigit() else seed
            )
            attempts: list[dict[str, Any]] = []
            tot_wall_ms = 0.0
            tot_gross_j = 0.0
            tot_net_j = 0.0
            tot_tokens = 0
            any_trunc = False

            for p_cfg in (
                {"do_sample": False, "temperature": None},
                {"do_sample": True, "temperature": 0.7},
            ):
                torch.cuda.synchronize()
                mj0 = read_gpu_energy_mj()
                t0 = time.perf_counter()
                gkw: dict[str, Any] = {
                    "max_new_tokens": cap,
                    "do_sample": p_cfg["do_sample"],
                    "pad_token_id": tokenizer.eos_token_id,
                    "eos_token_id": eos_ids,
                }
                if p_cfg["temperature"] is not None:
                    gkw["temperature"] = p_cfg["temperature"]
                with torch.no_grad():
                    seq = model.generate(**inputs, **gkw)
                    out = model(input_ids=seq, output_hidden_states=True)
                torch.cuda.synchronize()
                t1 = time.perf_counter()
                mj1 = read_gpu_energy_mj()

                p_wall_ms = (t1 - t0) * 1000.0
                p_gross_j = max(0.0, (mj1 - mj0) / 1000.0)
                p_net_j = max(0.0, p_gross_j - IDLE_BASELINE_POWER_W * (p_wall_ms / 1000.0))
                ntok = int(seq.shape[1] - plen)
                text = tokenizer.decode(seq[0, plen:], skip_special_tokens=True).strip()
                _, ok = extract_answer_for_group(item, text)
                hidden = out.hidden_states[-1][0, -1, :].float().cpu().tolist()
                raw_s = head.predict(VerifierFeatures(last_token_hidden=tuple(hidden)))
                cal_s = float(temperature_scale([raw_s], temp)[0])
                attempts.append({"correct": bool(ok), "score": cal_s})
                tot_wall_ms += p_wall_ms
                tot_gross_j += p_gross_j
                tot_net_j += p_net_j
                tot_tokens += ntok
                any_trunc = any_trunc or (ntok >= cap)

            chosen = max(attempts, key=lambda a: a["score"])
            rec = {
                "item_id": iid,
                "group": group,
                "arm": arm,
                "correct": bool(chosen["correct"]),
                "stale_fact_error": False,
                "passes": 2,
                "tokens_generated": tot_tokens,
                "truncated": any_trunc,
                "wall_time_ms": round(tot_wall_ms, 2),
                "gross_energy_joules": round(tot_gross_j, 4),
                "net_energy_joules": round(tot_net_j, 4),
                "nvml_process_vram_mb": vram_mb,
                "metadata": {},
            }

        elif group == STORE_GROUP:
            q = str(item.get("question") or item.get("prompt", "")).strip()
            t_s0 = time.perf_counter()
            lookup = store.lookup(q)
            ssd_ms = (time.perf_counter() - t_s0) * 1000.0
            chunk_text = lookup.chunk.text if lookup.chunk else ""
            src = lookup.chunk.source if lookup.chunk else "store"
            sys_p = (
                "You are a factual question answering assistant. "
                "Answer with only the direct factual value (e.g. date, number, or name). "
                "Do not write full sentences or explanations."
            )
            messages = [
                {"role": "system", "content": sys_p},
                {"role": "user", "content": f"Context:\n[{src}]\n{chunk_text}\n\nQuestion: {q}"},
            ]
            prompt = (
                tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
                + "Answer:"
            )
            inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
            torch.cuda.synchronize()
            mj0 = read_gpu_energy_mj()
            t0 = time.perf_counter()
            with torch.no_grad():
                out = model.generate(
                    **inputs,
                    max_new_tokens=32,
                    do_sample=False,
                    pad_token_id=tokenizer.eos_token_id,
                    eos_token_id=[tokenizer.eos_token_id, 198, 271],
                )
            torch.cuda.synchronize()
            t1 = time.perf_counter()
            mj1 = read_gpu_energy_mj()
            gen_ms = (t1 - t0) * 1000.0
            tot_wall_ms = ssd_ms + gen_ms
            gross_j = max(0.0, (mj1 - mj0) / 1000.0)
            net_j = max(0.0, gross_j - IDLE_BASELINE_POWER_W * (tot_wall_ms / 1000.0))
            ntok = int(out.shape[1] - inputs.input_ids.shape[1])
            raw_ans = tokenizer.decode(
                out[0][inputs.input_ids.shape[1] :], skip_special_tokens=True
            ).strip()
            aliases = item.get("aliases") or item.get("metadata", {}).get("aliases", [])
            ok = score_frozen_exact_match(raw_ans, str(item.get("target", "")), aliases=aliases)
            rec = {
                "item_id": iid,
                "group": group,
                "arm": arm,
                "correct": bool(ok),
                "stale_fact_error": False,
                "passes": 1,
                "tokens_generated": ntok,
                "truncated": ntok >= 32,
                "wall_time_ms": round(tot_wall_ms, 2),
                "lookup_latency_ms": round(lookup.latency_ms, 2),
                "bytes_read_from_ssd": lookup.bytes_read,
                "gross_energy_joules": round(gross_j, 4),
                "net_energy_joules": round(net_j, 4),
                "nvml_process_vram_mb": vram_mb,
                "metadata": {"entity": item.get("metadata", {}).get("entity")},
            }

        elif group == MEMORY_GROUP:
            wgm = WriteGatedMemory(write_threshold=0.5)
            events = item.get("metadata", {}).get("events", [])
            attr = item.get("metadata", {}).get("attribute")
            for e_idx, ev in enumerate(events):
                wgm.write(
                    MemoryEntry(
                        entry_id=f"{iid}_{e_idx}",
                        text=ev["content"],
                        source=ev["source"],
                        timestamp=ev["timestamp"],
                        confidence=1.0,
                        attribute=attr,
                    )
                )
            prompt_raw = item.get("prompt", "")
            q_part = (
                "Question:" + prompt_raw.split("Question:")[-1]
                if "Question:" in prompt_raw
                else str(item.get("question", prompt_raw))
            )
            recalled = wgm.recall(q_part)
            sys_p = (
                "You are an assistant with personal memory. "
                "Answer using the verified active personal memory provided. "
                "Give only the direct factual value (name, place, item, or preference)."
            )
            user_c = (
                "Review the personal history log below and answer the question.\n\n"
                f"--- PERSONAL HISTORY LOG ---\n{recalled}\n--- END LOG ---\n\n{q_part}"
            )
            messages = [{"role": "system", "content": sys_p}, {"role": "user", "content": user_c}]
            prompt = (
                tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
                + "Answer:"
            )
            inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
            torch.cuda.synchronize()
            mj0 = read_gpu_energy_mj()
            t0 = time.perf_counter()
            with torch.no_grad():
                out = model.generate(
                    **inputs,
                    max_new_tokens=32,
                    do_sample=False,
                    pad_token_id=tokenizer.eos_token_id,
                    eos_token_id=[tokenizer.eos_token_id, 198, 271],
                )
            torch.cuda.synchronize()
            t1 = time.perf_counter()
            mj1 = read_gpu_energy_mj()
            wall_ms = (t1 - t0) * 1000.0
            gross_j = max(0.0, (mj1 - mj0) / 1000.0)
            net_j = max(0.0, gross_j - IDLE_BASELINE_POWER_W * (wall_ms / 1000.0))
            ntok = int(out.shape[1] - inputs.input_ids.shape[1])
            raw_ans = tokenizer.decode(
                out[0][inputs.input_ids.shape[1] :], skip_special_tokens=True
            ).strip()
            stale_vals = item.get("metadata", {}).get("stale_values", [])
            is_stale = bool(item.get("metadata", {}).get("is_stale_fact", False))
            mscore = score_memory_probe_response(
                prediction=raw_ans,
                target=str(item.get("target", "")),
                stale_values=stale_vals,
                is_stale_fact_item=is_stale,
            )
            rec = {
                "item_id": iid,
                "group": group,
                "arm": arm,
                "correct": bool(mscore["correct"]),
                "stale_fact_error": bool(mscore["stale_fact_error"]),
                "passes": 1,
                "tokens_generated": ntok,
                "truncated": ntok >= 32,
                "wall_time_ms": round(wall_ms, 2),
                "gross_energy_joules": round(gross_j, 4),
                "net_energy_joules": round(net_j, 4),
                "nvml_process_vram_mb": vram_mb,
                "metadata": {
                    "attribute": attr,
                    "is_stale_fact": is_stale,
                },
            }
        else:
            raise ValueError(f"Unexpected group: {group}")

        existing[iid] = rec
        with out_jsonl.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(rec) + "\n")
        done += 1
        if done % 25 == 0 or len(existing) == len(eval_items) or done <= 3:
            acc = sum(1 for r in existing.values() if r["correct"]) / len(existing) * 100.0
            print(
                f"  [P1] {len(existing)}/{len(eval_items)} ({group}): "
                f"acc={acc:.2f}% net_E={rec['net_energy_joules']:.2f}J lat={rec['wall_time_ms']:.0f}ms",
                flush=True,
            )

    return [existing[str(it["item_id"])] for it in eval_items], store_meta


def summarize_system(
    records: list[dict[str, Any]],
    *,
    resident_gb: float | None = None,
    ssd_disk_mb: float | None = None,
    ssd_resident_mb: float | None = None,
    no_history_records: list[dict[str, Any]] | None = None,
    stale_fact_errors_measured: bool = True,
    seed: int = SEED_SUMMARY,
) -> dict[str, Any]:
    """Compute privacy-clean accuracy, CI, energy, latency, and group breakdown."""

    def _scope_stats(recs: list[dict[str, Any]]) -> dict[str, Any]:
        c = sum(1 for r in recs if r["correct"])
        n = len(recs)
        pct = round(c / n * 100.0, 2) if n else 0.0
        net_e = sum(float(r.get("net_energy_joules", 0.0)) for r in recs)
        return {
            "correct": c,
            "total": n,
            "accuracy_pct": pct,
            "wilson_ci_95": wilson_ci_95(c, n),
            "net_energy_joules": round(net_e, 2)
            if any("net_energy_joules" in r for r in recs)
            else None,
            "net_joules_per_correct": (
                round(net_e / c, 2)
                if (c > 0 and any("net_energy_joules" in r for r in recs))
                else None
            ),
        }

    chk_recs = [r for r in records if r["group"] in CHECKABLE_GROUPS]
    store_recs = [r for r in records if r["group"] == STORE_GROUP]
    mem_recs = [r for r in records if r["group"] == MEMORY_GROUP]

    groups_out: dict[str, Any] = {}
    for g in GROUPS:
        g_recs = [r for r in records if r["group"] == g]
        groups_out[g] = _scope_stats(g_recs)

    arms_out: dict[str, Any] = {}
    for arm in ("public", "synthetic", "real_wikipedia", "fictional_entity"):
        a_recs = [r for r in records if r.get("arm") == arm]
        if a_recs:
            arms_out[arm] = _scope_stats(a_recs)

    mem_stale_recs = [r for r in mem_recs if r.get("metadata", {}).get("is_stale_fact")]
    mem_static_recs = [r for r in mem_recs if not r.get("metadata", {}).get("is_stale_fact")]
    stale_errors: int | str = (
        sum(1 for r in mem_stale_recs if r.get("stale_fact_error"))
        if stale_fact_errors_measured
        else "unmeasured"
    )
    stale_error_rate: float | str = (
        (round(stale_errors / len(mem_stale_recs) * 100.0, 2) if mem_stale_recs else 0.0)
        if isinstance(stale_errors, int)
        else "unmeasured"
    )

    latencies = [float(r.get("wall_time_ms", 0.0)) for r in records]
    p50_ms = (
        round(percentile_latency([{"wall_time_ms": x} for x in latencies], 50), 2)
        if latencies
        else 0.0
    )
    p95_ms = (
        round(percentile_latency([{"wall_time_ms": x} for x in latencies], 95), 2)
        if latencies
        else 0.0
    )
    mean_ms = round(sum(latencies) / len(latencies), 2) if latencies else 0.0

    has_energy = any("net_energy_joules" in r for r in records)
    tot_net_j = sum(float(r.get("net_energy_joules", 0.0)) for r in records) if has_energy else None
    tot_gross_j = (
        sum(float(r.get("gross_energy_joules", 0.0)) for r in records) if has_energy else None
    )
    tot_correct = sum(1 for r in records if r["correct"])
    vram_vals = [float(r["nvml_process_vram_mb"]) for r in records if r.get("nvml_process_vram_mb")]

    out: dict[str, Any] = {
        "scopes": {
            "full_suite_1250": _scope_stats(records),
            "matched_checkable_800": _scope_stats(chk_recs),
            "store_knowledge_qa_300": _scope_stats(store_recs),
            "memory_probe_150": _scope_stats(mem_recs),
        },
        "groups": groups_out,
        "arms": arms_out,
        "memory_probe_detail": {
            "stale": _scope_stats(mem_stale_recs),
            "static": _scope_stats(mem_static_recs),
            "stale_fact_errors": stale_errors,
            "stale_fact_error_rate_pct": stale_error_rate,
        },
        "resources": {
            "resident_gb": resident_gb,
            "nvml_process_vram_mb": round(max(vram_vals), 1) if vram_vals else None,
            "gross_energy_joules": round(tot_gross_j, 2) if tot_gross_j is not None else None,
            "net_energy_joules": round(tot_net_j, 2) if tot_net_j is not None else None,
            "net_joules_per_correct_full_suite": (
                round(tot_net_j / tot_correct, 2)
                if (tot_net_j is not None and tot_correct > 0)
                else None
            ),
            "latency_mean_ms": mean_ms,
            "latency_p50_ms": p50_ms,
            "latency_p95_ms": p95_ms,
            "ssd_disk_mb": ssd_disk_mb,
            "ssd_resident_mb": ssd_resident_mb,
        },
    }

    if no_history_records is not None:
        out["memory_probe_dual"] = {
            "full_history": _scope_stats(mem_recs),
            "no_history": _scope_stats(no_history_records),
        }

    # Cluster bootstrap for memory_probe (by attribute/history) & fictional_entity (by entity)
    if mem_recs and any(r.get("metadata", {}).get("attribute") for r in mem_recs):
        # Match records shape expected by cluster_bootstrap_ci
        cb_mem = [
            {
                "correct": r["correct"],
                "history": r.get("metadata", {}).get("attribute", r["item_id"]),
            }
            for r in mem_recs
        ]
        m_mean, m_lo, m_hi = cluster_bootstrap_ci(cb_mem, cluster_key="history", seed=seed)
        m_icc = compute_cluster_icc(cb_mem, cluster_key="history")
        out["memory_probe_detail"]["cluster_bootstrap_95"] = [m_lo, m_hi]
        out["memory_probe_detail"]["cluster_icc"] = m_icc

    return out


def _safe_git_rev(repo_path: Path) -> str:
    """Return short git commit hash or 'unknown' if path is not a git repo."""
    try:
        return subprocess.check_output(
            ["git", "-C", str(repo_path), "rev-parse", "--short", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (subprocess.SubprocessError, OSError):
        return "unknown"


def assemble_locked_summary(
    f_records: list[dict[str, Any]],
    f_no_hist_records: list[dict[str, Any]],
    bllm_records: list[dict[str, Any]],
    p1_records: list[dict[str, Any]],
    store_meta: dict[str, Any],
    *,
    kestrel_dir: Path,
) -> dict[str, Any]:
    """Assemble privacy-clean reports/locked_test_step10.json from raw run records."""
    eval_commit = _safe_git_rev(REPO_ROOT)
    kestrel_commit = _safe_git_rev(kestrel_dir)

    ssd_disk_mb = round(store_meta.get("disk_bytes", 0) / (1024 * 1024), 2) if store_meta else None
    ssd_res_mb = (
        round(store_meta.get("resident_bytes", 0) / (1024 * 1024), 2) if store_meta else None
    )

    bllm_vram_mb = max(
        (float(r.get("nvml_process_vram_mb", 0.0)) for r in bllm_records), default=1416.0
    )
    p1_vram_mb = max(
        (float(r.get("nvml_process_vram_mb", 0.0)) for r in p1_records), default=1416.0
    )
    bllm_res_gb = round(bllm_vram_mb / 1024.0, 3)
    p1_res_gb = round((p1_vram_mb / 1024.0) + (ssd_res_mb / 1024.0 if ssd_res_mb else 0.0), 3)

    f_stale_scored = bool(
        f_records and all(r.get("stale_fact_errors_scored") is True for r in f_records)
    )
    sys_f = summarize_system(
        f_records,
        no_history_records=f_no_hist_records,
        stale_fact_errors_measured=f_stale_scored,
    )
    sys_b = summarize_system(bllm_records, resident_gb=bllm_res_gb)
    sys_p1 = summarize_system(
        p1_records,
        resident_gb=p1_res_gb,
        ssd_disk_mb=ssd_disk_mb,
        ssd_resident_mb=ssd_res_mb,
    )

    # Index by item_id for paired bootstrap intervals
    f_by_id = {r["item_id"]: r for r in f_records}
    b_by_id = {r["item_id"]: r for r in bllm_records}
    p_by_id = {r["item_id"]: r for r in p1_records}
    ordered_ids = [r["item_id"] for r in p1_records]

    def _paired(scope_ids: list[str]) -> dict[str, Any]:
        pf = [bool(f_by_id[i]["correct"]) for i in scope_ids]
        pb = [bool(b_by_id[i]["correct"]) for i in scope_ids]
        pp = [bool(p_by_id[i]["correct"]) for i in scope_ids]
        lo_pb, hi_pb = paired_bootstrap_ci(pp, pb, seed=SEED_SUMMARY)
        lo_pf, hi_pf = paired_bootstrap_ci(pp, pf, seed=SEED_SUMMARY)
        lo_fb, hi_fb = paired_bootstrap_ci(pf, pb, seed=SEED_SUMMARY)
        acc_p = sum(pp) / len(pp) * 100.0
        acc_b = sum(pb) / len(pb) * 100.0
        acc_f = sum(pf) / len(pf) * 100.0
        return {
            "n": len(scope_ids),
            "p1_minus_b_llm_pp": round(acc_p - acc_b, 2),
            "p1_minus_b_llm_ci_95": [lo_pb, hi_pb],
            "p1_minus_f_pp": round(acc_p - acc_f, 2),
            "p1_minus_f_ci_95": [lo_pf, hi_pf],
            "f_minus_b_llm_pp": round(acc_f - acc_b, 2),
            "f_minus_b_llm_ci_95": [lo_fb, hi_fb],
        }

    chk_ids = [i for i in ordered_ids if p_by_id[i]["group"] in CHECKABLE_GROUPS]
    store_ids = [i for i in ordered_ids if p_by_id[i]["group"] == STORE_GROUP]
    mem_ids = [i for i in ordered_ids if p_by_id[i]["group"] == MEMORY_GROUP]

    paired = {
        "full_suite_1250": _paired(ordered_ids),
        "matched_checkable_800": _paired(chk_ids),
        "store_knowledge_qa_300": _paired(store_ids),
        "memory_probe_150": _paired(mem_ids),
    }

    # Evaluate frozen gates on locked_test
    p1_chk = sys_p1["scopes"]["matched_checkable_800"]
    b_chk = sys_b["scopes"]["matched_checkable_800"]
    f_chk = sys_f["scopes"]["matched_checkable_800"]

    delta_pb = paired["matched_checkable_800"]["p1_minus_b_llm_pp"]
    ci_pb = paired["matched_checkable_800"]["p1_minus_b_llm_ci_95"]
    p1_j_chk = p1_chk["net_joules_per_correct"]
    b_j_chk = b_chk["net_joules_per_correct"]

    c1_pass = (
        delta_pb >= 5.0
        and ci_pb[0] > 0.0
        and p1_j_chk is not None
        and b_j_chk is not None
        and p1_j_chk <= b_j_chk
    )
    c2_pass = (
        p1_chk["accuracy_pct"] >= b_chk["accuracy_pct"] - 3.0
        and p1_j_chk is not None
        and b_j_chk is not None
        and p1_j_chk <= 0.5 * b_j_chk
    )
    g_q_pass = c1_pass or c2_pass

    denom_gf = round(f_chk["accuracy_pct"] - b_chk["accuracy_pct"], 2)
    gap_closed = (
        round((p1_chk["accuracy_pct"] - b_chk["accuracy_pct"]) / denom_gf * 100.0, 2)
        if denom_gf > 0
        else 0.0
    )

    p1_mem_acc = sys_p1["scopes"]["memory_probe_150"]["accuracy_pct"]
    f_full_mem = sys_f["memory_probe_dual"]["full_history"]["accuracy_pct"]
    f_no_mem = sys_f["memory_probe_dual"]["no_history"]["accuracy_pct"]
    p1_stale_err = sys_p1["memory_probe_detail"]["stale_fact_errors"]
    b_stale_err = sys_b["memory_probe_detail"]["stale_fact_errors"]
    g_m_pass = (
        p1_mem_acc >= f_no_mem
        and p1_mem_acc >= f_full_mem - 5.0
        # Frozen manifest v2.3 gates.G_M.target_max_stale_errors (22 baseline / 2).
        and p1_stale_err <= 11
    )

    g_r_pass = p1_vram_mb <= 1536.0

    decision = "prototype_2" if (g_q_pass and g_r_pass) else "publish_negative_result"

    f_model_values = [str(r.get("model_version", "")) for r in f_records if r.get("model_version")]
    f_date_values = [str(r.get("execution_date", "")) for r in f_records if r.get("execution_date")]
    f_models = sorted(set(f_model_values))
    f_dates = sorted(set(f_date_values))

    f_model_counts = _count_by(f_model_values)
    f_date_counts = _count_by(f_date_values)
    f_date_summary = ", ".join(f"{d}: {cnt}" for d, cnt in f_date_counts.items())
    caveats = [
        (
            "P1 Step 10 memory_probe used system prompt 'You are an assistant with personal memory. "
            "Answer using the verified active personal memory provided. Give only the direct factual "
            "value (name, place, item, or preference).' with 'Question:' + text instead of Step 6/7's "
            "'You are a helpful personal assistant...' and 'Question: {text}'. Recorded as evaluated "
            "Step 10 config caveat (Option a, issue #25; no locked re-exposure, decision driven by G-Q FAIL)."
        ),
        (
            "F private D11 logs retain response_id, model_version, execution_date, and boolean correctness "
            "without raw prediction text; F stale_fact_errors is unmeasured (not zero)."
        ),
        (
            f"F executed once via checkpoint pacing across {len(f_date_counts)} date(s) "
            f"({f_date_summary}; {len(f_records)} unique main + {len(f_no_hist_records)} no_history), "
            "covering all 1,250 locked items once without reuse."
        ),
    ]

    return {
        "status": "RUN",
        "note": (
            "One-time locked-test evaluation completed across F, B-LLM, and P1 "
            "using frozen manifest v2.3 config on Ryzen 7 7435HS + RTX 3050 4 GB."
        ),
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": eval_commit,
        "kestrel_git_commit": kestrel_commit,
        "manifest_version": MANIFEST_VERSION,
        "manifest_root_hash": MANIFEST_ROOT_HASH,
        "hardware_tier": "AMD Ryzen 7 7435HS + NVIDIA GeForce RTX 3050 Laptop GPU (4 GB)",
        "energy_label": MANDATORY_ENERGY_LABEL,
        "frontier_reference": F_REFERENCE_LABEL,
        "run_config": {
            "manifest_version": MANIFEST_VERSION,
            "manifest_root_hash": MANIFEST_ROOT_HASH,
            "context_length": CONTEXT_LENGTH,
            "b_llm_model": B_LLM_MODEL,
            "embedding_model": EMBEDDING_MODEL,
            "group_caps": GROUP_CAPS,
            "seeds": {
                "b_llm": SEED_BLLM,
                "p1": SEED_P1,
                "paired_bootstrap": SEED_SUMMARY,
                "cluster_bootstrap": SEED_SUMMARY,
            },
        },
        "exposure_record": {
            "decision": "D12",
            "policy": "Locked-test partition used strictly once; minimal prompts sent to F free tier.",
            "f_model_versions_observed": f_models,
            "f_execution_dates": f_dates,
            "f_counts_by_model_version": f_model_counts,
            "f_counts_by_execution_date": f_date_counts,
            "f_response_ids_logged": len(f_records) + len(f_no_hist_records),
        },
        "caveats": caveats,
        "systems": {
            "F": sys_f,
            "B_LLM": sys_b,
            "P1": sys_p1,
        },
        "paired_comparisons": paired,
        "gates": {
            "G_Q": {
                "status": "PASS" if g_q_pass else "FAIL",
                "scope": "matched_checkable_800",
                "p1_accuracy_pct": p1_chk["accuracy_pct"],
                "b_llm_accuracy_pct": b_chk["accuracy_pct"],
                "delta_pp": delta_pb,
                "paired_bootstrap_ci_95_pp": ci_pb,
                "p1_net_joules_per_correct": p1_j_chk,
                "b_llm_net_joules_per_correct": b_j_chk,
                "clause_1_passes": c1_pass,
                "clause_2_passes": c2_pass,
            },
            "G_F": {
                "status": "reported (not promised)",
                "scope": "matched_checkable_800",
                "f_accuracy_pct": f_chk["accuracy_pct"],
                "b_llm_accuracy_pct": b_chk["accuracy_pct"],
                "gap_denominator_pp": denom_gf,
                "gap_to_f_pp": round(f_chk["accuracy_pct"] - p1_chk["accuracy_pct"], 2),
                "gap_closed_pct": gap_closed,
                "store_group_p1_vs_f_pp": paired["store_knowledge_qa_300"]["p1_minus_f_pp"],
            },
            "G_M": {
                "status": "PASS" if g_m_pass else "FAIL",
                "scope": "memory_probe_150",
                "p1_accuracy_pct": p1_mem_acc,
                "f_full_history_pct": f_full_mem,
                "f_no_history_pct": f_no_mem,
                "p1_stale_fact_errors": p1_stale_err,
                "b_llm_stale_fact_errors": b_stale_err,
            },
            "G_R": {
                "status": "PASS" if g_r_pass else "FAIL",
                "nvml_process_vram_mb": p1_vram_mb,
                "vram_cap_mb": 1536.0,
                "resident_gb": p1_res_gb,
            },
        },
        "decision": decision,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--phase",
        choices=["all", "f", "bllm", "p1", "summarize"],
        default="all",
    )
    parser.add_argument("--kestrel-dir", type=Path, default=REPO_ROOT.parent / "kestrel")
    parser.add_argument(
        "--out", type=Path, default=REPO_ROOT / "reports" / "locked_test_step10.json"
    )
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()
    _require_full_locked_scope(args.limit, args.phase)

    private_dir = get_private_dir()
    runs_dir = private_dir / "step10_runs"
    items = verify_and_load_locked_test(private_dir)
    print(f"Verified SHA-256 hashes and loaded {len(items)} locked-test items.")

    if args.phase in ("all", "f"):
        run_f_locked(items, runs_dir, limit=args.limit)

    if args.phase in ("all", "bllm"):
        run_bllm_locked(items, private_dir, runs_dir, device=args.device, limit=args.limit)

    store_meta: dict[str, Any] = {}
    if args.phase in ("all", "p1"):
        _, store_meta = run_p1_locked(
            items, args.kestrel_dir, private_dir, runs_dir, device=args.device, limit=args.limit
        )

    if args.phase in ("all", "summarize"):
        eval_items = items[: args.limit] if args.limit else items
        f_by_id = load_jsonl_by_id(runs_dir / "f_locked_test.jsonl")
        f_nh_by_id = load_jsonl_by_id(runs_dir / "f_locked_memory_no_history.jsonl")
        b_by_id = load_jsonl_by_id(runs_dir / "bllm_locked_test.jsonl")
        p_by_id = load_jsonl_by_id(runs_dir / "p1_locked_test.jsonl")

        mem_ids = [str(it["item_id"]) for it in eval_items if it.get("group") == MEMORY_GROUP]
        all_ids = [str(it["item_id"]) for it in eval_items]
        f_recs = [f_by_id[i] for i in all_ids if i in f_by_id]
        f_nh_recs = [f_nh_by_id[i] for i in mem_ids if i in f_nh_by_id]
        b_recs = [b_by_id[i] for i in all_ids if i in b_by_id]
        p_recs = [p_by_id[i] for i in all_ids if i in p_by_id]

        if not store_meta and (runs_dir / "locked_store_index" / "vectors.bin").is_file():
            if str(args.kestrel_dir) not in sys.path:
                sys.path.insert(0, str(args.kestrel_dir))
            from kestrel.knowledge_store import KnowledgeStore

            ks = KnowledgeStore(runs_dir / "locked_store_index")
            ks.load_chunks()
            store_meta = {"disk_bytes": ks.disk_bytes, "resident_bytes": ks.resident_bytes}

        if (
            len(f_recs) != len(all_ids)
            or len(b_recs) != len(all_ids)
            or len(p_recs) != len(all_ids)
        ):
            raise RuntimeError(
                f"Incomplete locked records: F={len(f_recs)}/{len(all_ids)}, "
                f"B-LLM={len(b_recs)}/{len(all_ids)}, P1={len(p_recs)}/{len(all_ids)}"
            )

        summary = assemble_locked_summary(
            f_recs, f_nh_recs, b_recs, p_recs, store_meta, kestrel_dir=args.kestrel_dir
        )
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        print(f"\nWrote locked-test summary to {args.out}")
        print(f"Step 10 Decision: {summary['decision']}")


if __name__ == "__main__":
    main()
