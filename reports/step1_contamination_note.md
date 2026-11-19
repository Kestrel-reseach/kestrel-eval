# Step 1 — Contamination Note and Suite v2.0 Handoff

Please see the comprehensive benchmark contamination analysis and evaluation reporting protocol in:
- [`reports/CONTAMINATION.md`](file:///home/ash09/project_x/kestrel-eval/reports/CONTAMINATION.md)
- [`suite/README.md`](file:///home/ash09/project_x/kestrel-eval/suite/README.md)

### Key Points for Suite v2.0 (Decision D14 / Option B):
1. **Public Sources & Verified Licenses**: GSM8K (MIT), ARC-Challenge (CC BY-SA 4.0), MMLU 10 subjects (MIT), MBPP (CC BY 4.0), Wikimedia (CC BY-SA 4.0).
2. **Dual-Arm Structure**: Separate public benchmark arms (comparability) and clean procedural synthetic / fictional-entity arms (uncontaminated reasoning reference).
3. **MCQ Groups 100% Public**: Synthetic MCQ arms dropped per pre-registered A3 artifact audit failure.
4. **Mandatory Dual Reporting**: Future evaluation tables report $\text{Acc}_{\text{public}}$ and $\text{Acc}_{\text{synthetic}}$ separately alongside $\Delta_{\text{contam}}$.
5. **Validation Suite v2.0 Shipped**: 1,200 items across 6 groups shipped to `suite/validation/` with Python loader `load_suite_partition(split="validation")`.
6. **Locked Test Physical Quarantine**: 1,200 locked items stored strictly in `kestrel_private/locked_test/` outside the git repository; locked root hash `39cbe48e...` committed to `evaluation/manifest.yaml` (Manifest v2.0).
