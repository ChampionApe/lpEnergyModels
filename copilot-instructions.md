# Repo Custom Instructions for Copilot Chat

## Scope
You are assisting with linear programming models of power systems in this repository: 
- **MBasic** – simple power system model (no hours). Located in "/lpEnergyModels/mBasic.py". The interactive notebook "MBasic.ipynb" provides additional information and testing in this model.
- **MBasicInt** – MBasic + hourly variation. Located in "/lpEnergyModels/mBasicInt.py". The interactive notebook "MBasicInt.ipynb" provides additional information and testing in this model.


## Loader Contract (STRICT)
- **Sets**: Sheet has one or more columns. 1 col → `pd.Index`; 2+ cols → `pd.MultiIndex`. Column *names and order in the sheet* define index level names and order (README is documentation-only). 
- **Variables**: Index columns first, then **one value column named exactly as the symbol** (equal to the sheet/sheet name). No extra columns.
- **Scalars**: One column named as the symbol; one non‑NA row.
- The files "data/EX_MBasic.xlsx" and "data/EX_MBasicInt_CA.xlsx" are examples of data sheets that are structured correctly. 

## Units & Symbols
MBasic:
- Sets: `idxGen`, `idxF`, `idxEm`, `idxCons`
- Variables (units): `pFuel(idxF) €/GJ`, `uEm(idxF,idxEm) tCO2/GJ_fuel`, `VOM(idxGen) €/GJ_output`, `uFuel(idxF,idxGen) GJ_fuel/GJ_elec`, `taxEm(idxEm) €/tCO2`, `genCap(idxGen) GJ/h`, `mwp(idxCons) €/GJ`, `load(idxCons) GJ` (total unconstrained **daily** energy)

MBasicInt (adds time):
- Sets: `idxHr`, `idxHVTGen`, `idxHVTCons`, `idxGen2HVTGen(idxGen, idxHVTGen)`, `idxCons2HVTCons(idxCons, idxHVTCons)`
- Variables: 
  - `uHrCap(idxHr, idxHVTGen) ratio_0to1` (hourly‑to‑max capacity; values in [0,1])
  - `uHrLoad(idxHr, idxHVTCons) ratio_to_mean` (mean over `idxHr` == 1)
  - `load(idxCons) GJ/h` (annual mean hourly demand)
- **Identity for any hour count (24/168/8760):**
  `hourly_demand(idxHr, idxCons) = load(idxCons) * uHrLoad(idxHr, idxHVTCons(idxCons))`
- **Dimensionality reduction:** May map several generators to a single variation (e.g., `thermal_flat` for `{nuclear, natgas, coal}`).

## Guardrails
- Fix **data**, not the loader. Keep value column = symbol name. Update README (`Sheet|Type|Unit|Index|Description|Source`) when changing data.
- Validate before proposing changes. Prefer minimal diffs. Show a patch where possible.

## Typical Workflows to Prefer
- Validation: run tests, ensure units/sheets, verify mappings; check `uHrLoad` means and `uHrCap ∈ [0,1]`.
- Add technology: add to set, fill variables, map to variation type (reusing types where possible).
