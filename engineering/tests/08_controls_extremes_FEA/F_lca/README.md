# F. Life-cycle CO₂ (order of magnitude): one unit over 60 years

**Method.** Quantity take-offs from the sized gantry (A) plus our assumptions for the training wall, collector, concrete, HDPE pipe and marine installation. Cradle-to-gate factors are ICE v3 / worldsteel class values, quoted from memory and to be verified, each with a range. Monte Carlo with 20,000 triangular samples gives P10/P50/P90.

Operations: 0.35-0.75 MW (pipe pump 195-286 kW per v3, plus screw and drives) running 20-60 bloom days per year, at a grid factor of 0.30-0.50 t/MWh. Status quo: trawlers, workboats and trucks burning 2.8-6.5 t of diesel per bloom day [ASM].

**Results** (`out/lca_results.json`, `figs/lca.png`):

| Item | P50 (t CO₂e) |
|---|---|
| Embodied, total | ~7,600. Hot-spots: the 5 km HDPE pipe, marine installation fuel and the sheet-pile training wall |
| Operations, 60 y | ~12,600 |
| JAZR total | ~20,000 (P10-P90: 16,000-25,000) |
| Boats and crews, 60 y | ~37,000 |
| **One lost unit-day replaced by gas (32 GWh)** | **~12,700** |

**Verdicts.**

- F1 **PASS**: JAZR's whole life-cycle CO₂ equals about **1.6 avoided unit-days** (P10-P90: 1.3-2.0).
- F2 **PASS**: 5 t CO₂ per bloom day vs about 15 t for boats and crews.
- F3 INFO: a polymer mesh would cut mesh CO₂ about 4x.

End of life: steel is about 90 % recyclable, giving an indicative module-D credit. HDPE can be recycled or landfilled.

**Limits.** This is not an ISO 14040 LCA. The factors are class averages. The status-quo fuel figures are assumptions, because no plant publishes them.

Run: `python3 run_lca.py`.
