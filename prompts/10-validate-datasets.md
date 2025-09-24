# Validation Flow (MBasic & MBasicInt)

1) **Schema checks**
   - Every sheet named in README exists; types match (`set|variable|scalar`).
   - For each variable sheet: value column equals the symbol (sheet name); no extra columns.
   - Set sheets: if multiple columns, treat as MultiIndex.

2) **Unit checks**
   - MBasic: `genCap` GJ/h; `load` in GJ (daily energy).
   - MBasicInt: `genCap` GJ/h; `load` in GJ/h; `uHrCap` in [0,1]; `uHrLoad` mean by variation type = 1.

3) **Mapping checks**
   - All `idxGen` mapped in `idxGen2HVTGen`; prefer many‑to‑one (e.g., `thermal_flat`).
   - All `idxCons` mapped in `idxCons2HVTCons`.

4) **Derived assertions (MBasicInt)**
   - Build `loadHr = load × uHrLoad` and `genCapHr` and confirm dimensions and units (GJ/h).
   - Optionally plot hourly totals by consumer and capacity by generator.

5) **Output**
   - If issues: propose **minimal diffs** (rename value column to symbol; add missing mapping rows; fix README `Unit`/`Index`).
