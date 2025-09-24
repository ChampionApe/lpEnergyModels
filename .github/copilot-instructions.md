# Repo Custom Instructions for Copilot Chat

## External dependencies
Models are built using the `symMaps` package, specifically the `symMaps.ModelShell` and `symMaps.LPSys` classes. The model relies on data arranged as pandas series defined over named pandas indices/multiindices. To this end, we rely a lot on the `pyDbs` package to structure data in databases `pyDbs.SimplyDB`, but the package also contains a lot of useful classes for managing and adjusting pandas objects.

*Documentation:*
- `pyDbs`: `docs/SimpleDB.ipynb` shows basic syntax. Comprehensive documentation at [https://github.com/ChampionApe/pyDbs](https://github.com/ChampionApe/pyDbs), e.g. notebooks "docs_broadcast", "docs_adj", and "docs_simpleDB". 
- `symMaps`: Comprehensive documentation at [https://github.com/ChampionApe/symMaps](https://github.com/ChampionApe/symMaps), e.g. notebooks "docs_LPSys.ipynb" and "docs_ModelShell.ipynb".

## Scope
You are assisting with linear programming models of power systems in this repository. Models are all built on the parent class `symMaps.ModelShell` that always draw on classes `symMaps.LPSys` and `pyDbs.SimpleDB`. The repo starts with two basic models:
- `MBasic`: A simple power system model with a set of generators and consumers. Three main resources for MBasic:
    - Source code: `lpEnergyModels/mBasic.py`. 
    - Notebook documentation: `docs/MBasic.ipynb`.
    - Data structure: `data/EX_MBasic.xlsx` and `data/EX_MBasic.pkl`.
- `MBasicInt`: Extension of the `MBasic` model that includes hourly variation. Three main resources for MBasicInt:
    - Source code: `lpEnergyModels/mBasicInt.py`.
    - Notebook documentation: `docs/MBasicInt.ipynb`.
    - Data structure: `data/EX_MBasicInt_CA.xlsx` and `data/EX_MBasticInt_CA.pkl`.

## Loader Contract (STRICT)
Data that are arranged in excel sheets are read using the `pyDbs.ExcelSymbolLoader` class. The class has strict requirements for structure:
- The first sheet is always named `README` with 6 columns: ['Sheet', 'Type', 'Unit', 'Index', 'Description', 'Source'] that describes each symbol that is loaded. The README must contain at least:
    - 'Sheet' lists the sheetnames that are read in using `pyDbs.ExcelSymbolLoader`. They have to correspond to symbol names.
    - 'Type' lists the type of symbol; valid types 'set','variable','scalar'.
- The sheets listed in the README are then added with the specific structure:
    - **Sets**: Sheet has one or more columns. 1 col → `pd.Index`; 2+ cols → `pd.MultiIndex`. Column *names and order in the sheet* define index level names and order. 
    - **Variables**: Index columns first, then **one value column named exactly as the symbol** (equal to the sheet/sheet name). No extra columns. 
    - **Scalars**: One column named as the symbol; one non‑NA row.
- The files "data/EX_MBasic.xlsx" and "data/EX_MBasicInt_CA.xlsx" are examples of data sheets that are structured correctly. 
- If necessary, additional documentation can be found in [https://github.com/ChampionApe/pyDbs/blob/main/docs_ExcelSymbolLoader.ipynb](https://github.com/ChampionApe/pyDbs/blob/main/docs_ExcelSymbolLoader.ipynb).

## Units & Symbols
A few additional notes on the MBasicInt model:
- Several parameters consists of a yearly and an hourly component. Examples: `load[idxCons]`, `genCap[idxGen]`.
- Hourly components measure ratios, e.g.
    - `uHrCap`: Hourly-to-max capacity; values in [0,1].
    - `uHrLoad`: Hourly load relative to mean; mean over `idxHr` == 1.
- Hourly components are defined over hours (`idxHr`) and often a type index, e.g. `idxHVTGen` and `idxHVTCons`. Mappings (2-dimensional multiindices) then map from individual set elements to types (many-to-one mappings). For instance:
    - `uHrCap[idxHr, idxHVTGen]` includes typical variation types in `idxHVTGen`; the mapping `idxGen2HVTGen` maps from generators in `idxGen` to the type of hourly variation it features.
    - `uHrLoad[idxHr, idxHVTCons]` includes typical variation types in `idxHVTCons`; the mapping `idxCons2HVTCons` maps from consumers in `idxCons` to the type of hourly variation it features.
    - Several generators/consumers can map to a single variation type. 


## Guardrails
- Fix **data**, not the loader. Keep value column = symbol name. Update README (`Sheet|Type|Unit|Index|Description|Source`) when changing data.
- Validate before proposing changes. Prefer minimal diffs. Show a patch where possible.
- Do **not** change core files: lpEnergyModels/base.py, lpEnergyModels/mBasic.py, lpEnergyModels/mBasicInt.py. Create new files instead. 