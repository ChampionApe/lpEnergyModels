# Change Time Resolution (e.g., 24 → 168 or 8760)

**Target:** Update `idxHr` and rebuild `uHrLoad`/`uHrCap`.

**Agent steps:**
1) Extend `idxHr` to the requested length and regenerate rows.
2) Recompute `uHrLoad(idxHr, idxHVTCons)` so the **mean over `idxHr` = 1** for each variation type. Keep `load(idxCons)` unchanged (still **GJ/h**).
3) If generator profiles need refinement, ensure `uHrCap ∈ [0,1]` and preserve any many‑to‑one mapping (e.g., `thermal_flat`).
4) Validate (#prompts/10-validate-datasets.md). Provide a patch/PR with changes scoped to time sheets only.