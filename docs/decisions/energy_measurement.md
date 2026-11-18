# Decision Record: Energy Measurement Protocol & Hardware Sensors

**Date**: 2026-11-18  
**Status**: `PENDING OWNER CONFIRMATION in writing (PR or issue comment)` *(Not final)*  
**Source**: Relayed by Member A  

---

## 1. Verbatim Owner Statement

> "Vendam software laye pananum / Laptop oda own sensors vachi dhan"

**Source**: Relayed orally/by message by Member A on 2026-11-18.

---

## 2. Translation & Interpretation

**Member A's translation**:
> "no wall meter; measure energy at the software layer using the laptop's own sensors only."

---

## 3. Operational Implications for Prototype 1

1. **Wall-Meter Calibration Skipped**:
   - The planned physical wall power meter calibration against software counters is skipped pursuant to this decision.
2. **Application of Plan Kill Gate**:
   - `PLAN.md` (Step 0 Kill Gate, line 96) states:  
     *"Kill: if counters cannot be calibrated, report relative energy only."*
   - Consequently, all energy measurements for Prototype 1 are classified as **relative energy only** (`energy_status: "relative_only"`).
3. **Measurement Scope**:
   - Measurements rely on the laptop's software-accessible onboard sensors (NVIDIA NVML for GPU power).
   - Absolute joule figures against grid wall power cannot be claimed.
   - Cross-machine energy comparisons are invalid; energy comparisons are valid only within the same machine, session, and power state.
4. **Pending Confirmation**:
   - This decision record remains in status `PENDING OWNER CONFIRMATION in writing (PR or issue comment)` until the project owner provides written confirmation in a GitHub PR review or issue comment.
