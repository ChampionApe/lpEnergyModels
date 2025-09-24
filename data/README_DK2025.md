# Danish 2025 Dataset (EX_MBasicInt_DK2025.xlsx)

This dataset provides a stylized representation of the Danish power system in 2025 for use with the `MBasicInt` model (24 representative hours with scaling factor 8760/24).

## Purpose
Designed for quick experimentation with:
- Wind + solar variability (onshore/offshore distinction)
- Dispatchable thermal (biomass, natural gas)
- Segmented demand with differing hourly profiles
- Simple CO2 pricing (fuel-based emissions + tax)

## File
`EX_MBasicInt_DK2025.xlsx`

## Loader Contract (pyDbs.ExcelSymbolLoader)
All sheets follow the strict symbol format. First sheet is `README` describing symbols. Types used: `set`, `variable`.

## Sets & Mappings
| Sheet | Description |
|-------|-------------|
| idxGen | Generator technologies: solar, wind_onshore, wind_offshore, biomass, natgas |
| idxF | Fuels: biomass, natgas, none |
| idxEm | Emission categories (CO2 only) |
| idxCons | Demand segments: residential, services, industry, data_centers |
| idxHr | 24 representative hours: h01–h24 |
| idxHVTGen | Hourly variation types for generation (capacity availability) |
| idxHVTCons | Hourly variation types for load (shape factors) |
| idxGen2HVTGen | Mapping generators → generation variation type |
| idxCons2HVTCons | Mapping consumers → load variation type |

## Core Variables
| Sheet | Unit | Meaning |
|-------|------|---------|
| genCap | GJ/h | Installed generating capacity (MW * 3.6) |
| uHrCap | ratio | Hourly availability (≤1) by variation type |
| VOM | €/GJ | Variable O&M cost per unit output |
| FOM | 1000€/(GJ/h)/y | Annual fixed O&M per unit capacity |
| INVC | 1000€/(GJ/h)/y | Annualized investment cost (CapEx * CRF 0.085) |
| pFuel | €/GJ | Fuel prices (biomass, natural gas) |
| uFuel | GJ fuel / GJ el | Inverse efficiency (e.g. 2.0 → 50% eff) |
| uEm | tCO2 / GJ fuel | Fuel emission intensity (biomass treated neutral) |
| taxEm | €/tCO2 | Emission tax (ETS + assumed national) |
| load | GJ/h | Mean hourly load per segment (sum * 8760 = annual energy) |
| uHrLoad | ratio | Hourly load shape (mean = 1 per variation type) |
| mwp | €/GJ | Marginal willingness to pay (downward ranking across segments) |

## Scaling Logic
`MBasicInt.scale = 8760 / 24 = 365`. Annualized indicators (fuel use, emissions, unit costs) are produced by multiplying summed 24h results by 365. The `load` values are mean hourly levels; hourly caps for demand are `load * uHrLoad`.

## Demand Calibration
Total annual demand target ≈ 41 TWh (147.6 PJ):
Sum(load) ≈ 16,849 GJ/h → * 8760 h = 147.6 PJ.
Shares: residential 32%, services 28%, industry 30%, data_centers 10%.

## Generation Capacities (Approximate 2025 Outlook)
| Tech | MW | GJ/h | Notes |
|------|----|------|-------|
| Solar | 6000 | 21,600 | Rapid build-out |
| Wind Onshore | 5200 | 18,720 | Mature fleet |
| Wind Offshore | 4400 | 15,840 | Existing + near-term additions |
| Biomass | 2000 | 7,200 | CHP & waste (aggregated) |
| Natgas | 1800 | 6,480 | CHP + peakers |

## Cost & Fuel Assumptions
- Fuel prices: biomass 4.5 €/GJ, natural gas 7.0 €/GJ (moderate 2025 outlook)
- Emission intensity: gas 0.056 tCO2/GJ fuel, biomass 0 (policy accounting)
- CO2 price (taxEm): 110 €/tCO2
- Efficiencies (inverse form uFuel): biomass 2.9 (~35% eff), gas 2.0 (~50% eff)
- Investment annualization uses CRF 0.085.

## Hourly Profiles
- Solar: stylized diurnal (midday peak, zero at night)
- Wind onshore/offshore: distinct variability; offshore smoother & higher CF
- Biomass / Natgas: flat availability (thermal_flat = 1.0)
- Load segments: residential (morning/evening peaks), services (daytime peak), industry (near flat), data centers (flat)
Each `uHrLoad` profile normalized to mean 1; each `uHrCap` within [0,1].

## Typical Usage (Pseudo-Code)
```python
from pyDbs import ExcelSymbolLoader
from lpEnergyModels.mBasicInt import MBasicInt

loader = ExcelSymbolLoader('data/EX_MBasicInt_DK2025.xlsx')
db = loader.db  # if loader auto-populates; else adapt to your loading pattern
model = MBasicInt(db=db)
model.compile()
sol = model.solve()  # depends on solver integration in base classes
print(sol['pAvg'], sol['emissions'])
```

## Extension Ideas
- Add `emCap` sheet and use `MBasicIntEmCap` for emission caps.
- Introduce interconnector pseudo-generator with low VOM to mimic imports.
- Create 8760-hour expansion by cloning profiles and adding seasonal variation.

## Provenance & Caveats
Values are illustrative—not official forecasts. Based on public Danish Energy Agency technology catalog ranges, Energinet statistics, and general market assumptions. Adjust before policy or investment analysis.

## Change Log
- v1 (initial): Created on first addition to repo (2025-09-24).

---
Feel free to refine parameters or add constraints; keep README sheet updated if symbols change.
