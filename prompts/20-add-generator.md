# Add a Generator Technology (Template)

**Input (student fills):**
- New `idxGen` value: `<name>`
- Variation mapping: `<idxHVTGen name>` (reuse existing type if possible)
- Units/values to add: `VOM(€/GJ_output)`, `genCap(GJ/h)`, `uFuel(GJ_fuel/GJ_elec)` or 0 for non-fuel, any `pFuel`/`uEm` impacts, sources for README

**Agent steps:**
1) Append to `idxGen`; map in `idxGen2HVTGen` (prefer existing variation type).
2) Fill `VOM`, `genCap`, and `uFuel` rows. For non‑fuel techs, use 0 in `uFuel`.
3) Update README (`Sheet|Type|Unit|Index|Description|Source`) entries if needed.
4) Run #prompts/10-validate-datasets.md and propose a patch/PR.