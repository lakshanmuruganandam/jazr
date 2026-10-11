# TESTS/08: controls, extremes, structural FEA, seismic, human factors, LCA, climate

These are computational tests of **JAZR Gate v3**: structure, environment, control logic and people. They complement 00-07 and do not repeat the hydraulics hand-calcs, lane CFD, biology/FMEA, economics, twin V&V or the virtual tank.

Every result is marked **PASS / MARGINAL / FAIL / INFO** against a stated criterion. Every number is tagged [V3], [DATA], [LIT], [ASM] or [ENG] in `common/params.py`, which also holds the full source list.

| Folder | Test |
|---|---|
| `common/` | Design basis (`params.py`), our 3D frame FE solver (`fe3d.py`), gantry model and loads (`gantry.py`) |
| `A_structural_FEA/` | Gantry bay FEA: statics, deflection, modal vs waves, VIV, buckling, 60-y fatigue, sensitivity; roll-down mesh check |
| `B_seismic/` | Response-spectrum check: UAE 2475-yr hazard (Irfan 2012) and a 0.3 g nuclear envelope; Seismic II/I notes |
| `C_extremes/` | Wind, 100-yr waves, surge, sea-level rise to 2085, low tide, 36-38 °C water, air temperature, dust, storm-vs-bloom policy |
| `D_controls/` | PLC-style controller, explicit-state model checking, fault-injection simulation, filter test, timing, cyber checklist |
| `E_human_factors/` | Alarm rate and alarm flood (naive vs ISA-18.2 rationalised), workload, procedure coverage |
| `F_lca/` | Order-of-magnitude life-cycle CO₂ vs boats/crews vs one lost unit-day |
| `G_climate_future/` | Incident trend, hot-season length to 2085, modular lift headroom |
| `tests/` | pytest: 23 tests (FE solver verification, controller model checks, sensing, structures, procedures) |
| `SUMMARY.md` / `RTM.md` / `RESULTS.json` | Auto-generated verdict table and requirement traceability matrix |

Run everything with `python3 run_all.py`. Each script takes under 10 min on an idle 10-core machine (model_check about 5 min, run_controls 3-7 min); under heavy shared load they took up to 3x longer. `python3 run_all.py --aggregate` rebuilds the tables only. Current tally: PASS 48, MARGINAL 12, FAIL 15, INFO 6, of which 4 FAILs are rejected alternatives. Run `python3 -m pytest -q tests` for the test suite (~25 s).

## Headline findings

**FAIL** (each comes with a design change):

1. **Mesh wire bends past yield on the drum.** E·d/D = 820 MPa for 2.5 mm wire on a 0.61 m drum, about 56k wraps in 60 y. Use a hinged-link belt or a polymer mesh, or a drum of at least 2.8 m (A8c).
2. **Wetted duplex at 36-38 °C** (about 39 °C by 2085) is above NORSOK's 20 °C crevice limit. Use titanium, Cu-Ni or polymer (C7, G3).
3. **Roll-up cleaning + an always-open relief bay leak 18-29 % of the biomass to the plant** at 0.3/m³. That contradicts the twin's η = 0.9. An **endless-belt clean-in-place face + a passive flap relief** gives 1.2 %, or 9.5 % with all faults injected (D11, D15).
4. **The pulse rule fails under comms loss** unless the bays have **TDMA slots plus a hard-wired busy loop**. Model checking shows TDMA alone or a busy loop alone also fail (D3).
5. Air gap in 2085: the **exposed outer guide line is 2.4 m short**. Inner gantry: MARGINAL (C5).
6. Low-tide max-flow approach velocity is 0.22 m/s vs the 0.12 m/s limit (C6b).
7. A taut membrane (2 % sag) in the stuck-drum case overstresses the piles at 1.08 (A7).
8. Single-channel trips: a naive dP threshold false-trips 52-828 times per bay-day in Hs 1.5-2 m seas, and a 1oo1 hard trip is fooled by a stuck transmitter (D6b, D7b). The specified 2oo3 + filter design passes.

**MARGINAL:**

- Deploy takes 573 s vs the 10-minute claim.
- The < 1 t pulse claim holds only at 0.3/m³ with 60 s residence.
- Per-bay dP is not bay-selective, because the bays share one line dP.
- A seized drum stays latent for about 31 min.
- Staged seismic all-up takes 34 min.
- Equipment is near its 40 °C rating.
- Hot season gets longer.
- 2 lift lines are needed at 172.5 m³/s.
- 9 cyber items are unspecified (RISK).

**PASS:**

- Stresses in every case; modal (f1 1.5 Hz, clear of the 2-8 s wave band); VIV, buckling and 60-y fatigue.
- Seismic up to the 0.3 g envelope.
- 100-yr wind and wave survival.
- OS invariants, no deadlock and liveness (26k states).
- Wildlife and outlet logic; IT/OT separation.
- Filtered sensing; alarm rate after rationalisation; procedures.
- LCA: about 1.6 avoided unit-days pays back the CO₂.
