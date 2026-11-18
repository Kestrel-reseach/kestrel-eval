# Step 1 — Contamination Note and Suite v0 Handoff

Please see the comprehensive benchmark contamination analysis and evaluation reporting protocol in:
- [`reports/CONTAMINATION.md`](file:///home/ash09/project_x/kestrel-eval/reports/CONTAMINATION.md)
- [`suite/README.md`](file:///home/ash09/project_x/kestrel-eval/suite/README.md)

### Key Points for Step 1 PR 5:
1. **Public Sources & Verified Licenses**: GSM8K (MIT), ARC-Challenge (CC BY-SA 4.0), MMLU (MIT), HumanEval/MBPP (MIT / CC BY 4.0), Wikimedia (CC BY-SA 3.0/4.0).
2. **Contamination Mitigation**: 100% of the locked-test partition and validation suite v0 are backed by high-cardinality procedural generators with zero web pretraining contamination.
3. **Mandatory Dual Reporting**: Future evaluation tables must report $\text{Acc}_{\text{public}}$ and $\text{Acc}_{\text{synthetic}}$ separately alongside $\Delta_{\text{contam}}$.
4. **Validation Suite v0 Shipped**: 1,200 items across 6 groups shipped to `suite/validation/` with Python loader `load_suite_partition(split="validation")`.
5. **Locked Test Physical Quarantine**: 1,200 locked items stored strictly in `kestrel_private/locked_test/` outside the git repository; root hash `22fff5e0...` committed to `evaluation/manifest.yaml`.
