# JAZR Gate v3: virtual tank (tank-scale twin of physical protocols T01–T16)

> **SIMULATED virtual tank — not physical evidence.** Every number here comes from a model. None is a measurement, and none may appear on a slide as "tested". Suggested slide line: *"Virtual-tank simulation, 1:20 Froude, N seeded runs; not a physical test; not field-validated."*

The real kitchen or flume tank still decides. This folder rehearses the pre-registered protocols (`../06_physical_protocols/PROTOCOLS.md`) before the physical tests. It shows which outcomes are fragile, which parameters to measure first, and where a 1:20 tank cannot represent the prototype. Lane-scale CFD is in `../03_cfd_flow` and is not repeated here.

## Files
| File | What it is |
|---|---|
| `vtank.py` | Model: geometry, flow solver, particle (bell/turtle/fish/fragment) engine |
| `run_protocols.py` | Runs T01–T16 and writes `results/SIM_T##_*.csv` (copies of the blank datasheets with an added `data_type` column) and `results/sim_results.json` |
| `verification.py` | Mass balance, uniform-flow, sweep/through and grid/time-step checks (`results/SIM_verification.json`) |
| `sensitivity.py` | Calibration and uncertainty scans (`results/SIM_sensitivity.json`) |
| `animate_T03.py` | Pitch animation `charts/T03_11deg_noscreen_vs_screen.mp4` / `.gif` (22 s, 1280×720, red "SIMULATED" banner) |
| `charts.py` | PNG charts in `charts/` (each one watermarked) |

Re-run: `python3 run_protocols.py && python3 verification.py && python3 sensitivity.py && python3 charts.py && python3 animate_T03.py`. Seeds are fixed. Each simulated run takes 5–30 s on an idle machine.

## Model
- **Tank:** 1.5 m × 0.4 m plan view, water 0.25 m deep, 1:20 Froude scale. Card training walls form a 16 cm lane. The approach speed is 11 cm/s, which is 0.5 m/s at full scale.
- **Inner screen:** a roll-down mesh at 8, 11, 15 or 20° from the lane wall, split into 4 bays that can each be raised. Mesh opening is 5 mm with 50% open area, freeboard 2 cm, bottom-bar gap 1 mm.
- **Bypass entrances:** a 6 cm entrance at the downstream end of the face plus 1 entrance mid-face (2 entrances), or 3 mid-face (4 entrances). Bypass flow is 10% of the lane flow (nominal) and is scanned.
- **Flow:** steady 2-D potential (Darcy-form) flow on a 5 mm finite-volume grid.
  - Walls are zero-conductance links; the mesh is a resistive link whose resistance rises with blinding.
  - The pump is a uniform inflow, the intake a fixed-potential outflow, and the bypass entrances volumetric sinks.
  - The flow is re-solved whenever blinding changes or a bay is lifted (two-way coupling).
  - Head loss and load on the screen use the quadratic wire-mesh law K(β).
- **Bells:** 30 soft spheres, 4–6 cm across, with dome volume.
  - Dynamics follow Maxey–Riley: fluid acceleration, added mass and Re-dependent drag. Turbulence is an Ornstein–Uhlenbeck process (10% intensity).
  - Buoyant settling uses the density model from T01.
  - Contacts are soft spring–dashpot (DEM). On the mesh there is Coulomb friction (μ = 0.4) plus the mesh-pressure load.
  - Bells can extrude through the mesh when ΔP > c·E·(d/a − 1) (a Cauchy-number criterion). They can also squeeze under or over gaps.
  - Each bypass entrance has a finite throughput: one bell per layer per passage time.
- **Turtle:** a rigid 5 cm body, either weighted (sinks), neutral and passive, or swimming at 8 cm/s. Detection uses a camera or person trigger with a detection probability and latency, followed by a diverter, then a spring door.
- **Waves:** a linear wave orbital velocity and surface-elevation term.
- **Fish:** rigid beads, 1 cm.
- **Not modelled:** 3-D recirculation, separation and vortex shedding behind walls; swimming bells; bell tearing during contact (handled separately in T09); vertical flow under or over the outer curtain beyond a simple "draw" term.

## Verification (`results/SIM_verification.json`, `charts/verification_grid.png`)
- **Mass balance:** cell-level continuity residual ≤ 1.7e-11 m²/s in every configuration. Global inflow = intake + bypass to within 1e-5 relative; the remainder is the 1e-10 diagonal regularisation.
- **Uniform lane** (no screen, no bypass): u = 0.10999 m/s against the 0.11 imposed, maximum error 0.2%.
- **Sweep/through ratio on the face:** 0.85–0.95 × cot θ. For example, at 11° the ratio is 4.87 against 5.14 for a near-transparent screen. Through-velocity is 1.03–1.30 × U·sin θ. The screen therefore turns the flow as expected.
- **Grid check (dx = 10 / 5 / 2.5 mm):**
  - η_r(11°): 0.46 / 0.50 / 0.48 (10 seeds each, s.e. ≈ 0.015). This is converged to about ±0.04, which is less than the seed-to-seed scatter.
  - Absolute screen head: 0.41 / 0.28 / 0.23 mm. This is **grid-sensitive** because of the end-of-face flow concentration, so treat absolute ΔP values as ±40%.
- **Time step:** dt 0.01 vs 0.005 s gives η_r 0.50 vs 0.52, within noise.

## Results vs pre-registered criteria
*Sixteen tests: 7 PASS, 5 FAIL or KILL, 4 report-only, and 5 flagged SENSITIVE. Each verdict is the simulation's verdict only.*

**PASS**
| Test | Simulated result | Criterion | Verdict |
|---|---|---|---|
| **T04** entrance spacing | 2 → 4 entrances: η_r 0.51 → 0.71, stuck bells 12.5 → 8.5 per 30 | more entrances → fewer stuck | **PASS** |
| **T06** roll-down seal | Deploy time 8.6 s (6.5–11.3). Seated gap 1.0–2.5 mm. **0 bells under the seated bar in 10/10 runs**; no bell was pinned. However, 4–12 bells slipped under while the bar was being lowered | gap ≈0, 0 under; kill >10% of runs | **PASS** (deploy before bells arrive) |
| **T08** outer guide line | η_g 0.94–1.00 at 15/20/25°, flood and ebb alike | η_g ≥ 0.4 both directions | **PASS, but optimistic.** The curtain model has no real 3-D under/over flow, and flood/ebb are symmetric by construction |
| **T09** passage damage | Gelatin bells: screw 100% intact, siphon 100%, pump 0% (shredded). **Agar bells (brittle): siphon 67%, 1–5 m tube 63–68%** | ≥90% intact via screw/siphon | **PASS (gelatin) / SENSITIVE** to recipe. Use gelatin bells and a ≥6 cm bore. The model is parametric (strain/impact), not flow-resolved |
| **T12** drift-back | Returned to the intake after 3 cycles: 79% (30 cm), 56% (60 cm), 26% (100 cm) | returns fall with distance | **PASS** (mostly kinematic) |
| **T13** waves | Waves 1–4 cm at 1.0–1.5 s **raise** η_r by 5–84% because shaking unjams bells. 0 leaks; overtopping needs a crest above roughly freeboard + bell radius | η_r drop <20% | **PASS** |
| **T15** bay load | Strip force 0.16 N clean → 0.37 / 1.5 / 6.9 N at 25 / 50 / 75% blinding (11 cm/s). That is 1.6–2.3× the uniform hand calculation, because blinding concentrates flow. Prototype equivalent is about ×8000 | scales with blinding | **PASS**. A luggage scale (~0.5 N resolution) cannot read the clean case; use a load cell |

**FAIL or KILL**
| Test | Simulated result | Criterion | Verdict |
|---|---|---|---|
| **T01** surrogates | 20% hover (13–23%). Hovering means \|settling velocity\| ≤ 5 mm/s, which requires density control to σ ≈ 0.03 kg/m³ (30 ppm). Kitchen-scale scatter (air bubbles, gel %) is about 0.2 kg/m³ | ≥80% hover | **FAIL (nominal) / SENSITIVE** to the hover definition and to bubble control |
| **T03** guidance η_r | 8° 0.47 · **11° 0.50** · 15° 0.56 · 20° 0.69 (3 protocol runs; 15-seed means 0.50 / 0.51 / 0.57 / 0.62). **0% reached the intake in every screen run.** The loss is bells jammed at the face and the bypass mouth (~40%) | η_r ≥ 0.7 at 11°; kill if <0.4 at every angle | **FAIL at 11° (not kill) / SENSITIVE** to bypass flow and bell-to-entrance size |
| **T05** clogging | Design rate ≈37 bells/min (prototype 0.3 /m³ face loading, Froude time-scaled). Head over 5 min: 0.28 → 4.6 mm without cycling, 0.28 → 2.3 mm with cycling. Face cover 33% vs 25%. Never >50% within 1 min. At 74/min, 50% cover is reached after 3.6–4.6 min without cycling. **Cycling sends 21% of bells into the intake** | cycling keeps ΔP stable (we set: ≤1.5× start); kill >50% cover in <1 min | **FAIL** (cycling halves ΔP but does not hold it). No kill |
| **T10** turtle | **Camera only:** 1–2 per 30 reach the screw path. **Person mock:** 10/30 swimmers reach it. **Camera + door:** 0 swimmers reach it, because the door threshold of 6 mN separates a swimmer from a bell pile. Passive turtles exert about 1 mN and do not open the door. **Neutral turtles impinge on the face (19/30)** and never reach the bypass. The weighted clay model does not move at 11 cm/s, so it must be hand-placed | 100% diverted/exit; kill if any reach the screw | **KILL in several configurations / SENSITIVE** to detection probability (needs ≥0.999). Door forces are mN, below spring-scale resolution |
| **T16** repeatability | Counter discrepancy 0 / 0 / 6.25% (mean 2.1%). With ~15 counts per run, a single miss is 6.7%, so P(run ≤5%) is only 36–69% | ≤5% | **FAIL (1 of 3 runs) / SENSITIVE**. Need ≥20 counts per run, or the criterion should be read as ±1 bell |

**Report-only (no pre-registered target)**
| Test | Simulated result | Note | Verdict |
|---|---|---|---|
| **T02** baseline | Bypass off: 95.8% reached the intake (93–100%), 4% lost in corners. Bypass on as a control: 17% entered the bypass by chance, 78% reached the intake | reference | **REFERENCE** |
| **T07** relief pulse | Lifting one bay releases 34% of the bells on the face on average (0–91%). By bay: bay 1 (upstream) 0%, bay 2 2%, bay 3 54%, **bay 4 (downstream) 80%**. Lifting all bays releases more than were on the face, because bells upstream also pass | "small fraction" (we set ≤35%) | **PASS on average / FAIL for the downstream bay.** The load collects there, so staging limits the pulse only if the downstream bay is split |
| **T11** fish return | 1 cm rigid beads: **100% returned via bypass**, 0 stuck | report | **REPORTED.** The contrast with 5 cm bells points to jamming by size |
| **T14** extrusion | 0 of 540 fragments (1–2 cm; 3/5/8 mm mesh) extruded in the tank. At tank scale ΔP/E ≈ 1e-4. At prototype scale with 75% blinding and an assumed mesoglea E of 50–300 Pa, extrusion is predicted (`SIM_T14_cauchy_scaling.csv`) | report; sets the mesh opening | **REPORTED / SENSITIVE.** Gel surrogates cannot reproduce the prototype Cauchy number, so a "0 extruded" tank result does not transfer |

### The main design finding (to be confirmed physically)
In the virtual tank, the 11° screen never lets a bell through to the intake. Guidance fails instead through **jamming**: ~40% of the bells stay stuck at the face and at the bypass mouth. The cause is the combination of three tank-specific parameters, which the twin flags as the levers:
1. **Bypass flow.** At 10% of lane flow, the entrance velocity is only ~0.15 × the approach velocity. Fish-screen practice is a bypass velocity of at least the sweep velocity.
2. **Bell size relative to entrance width.** The bells are 4–6 cm and the entrance 6 cm, which is a granular-arching regime. Geometrically scaled bells would be 30 cm / 20 = 1.5 cm.
3. **Number of entrances.** Four entrances raised η_r to 0.71.

T11 (1 cm beads: 100% to bypass) and T13 (waves unjam bells) point the same way. See the sensitivity section below.

## Calibration and uncertainty
Runs for this section are 120 s long with 3 seeds each, so nominal η_r(11°) here is 0.42 rather than 0.50 at 180 s: some bells enter the bypass late. Compare the rows with each other, not with T03. Seed noise is about ±0.03–0.05 s.e. Charts: `charts/sensitivity_tornado.png` and `charts/eta_vs_bypass_flow.png`.

**Unknown physical parameters** (one at a time, plausible ranges fixed before running):

| Parameter (range) | η_r(11°) low → high | Comment |
|---|---|---|
| Bell–mesh friction μ (0.1 – 1.0) | 0.64 → 0.49 | Largest physical unknown; slippery bells guide better. **Measure it (tilted wet mesh).** |
| Tank turbulence (3% – 25%) | 0.40 → 0.53 | Agitation unjams bells (stuck 59% → 12%) |
| Density scatter (×0.1 – ×2) | 0.44 → 0.38 | Sinking and floating bells jam more |
| Drag coefficient (×0.6 – ×1.6) | 0.42 → 0.51 | |
| Screen resistance ℓ_s (0.01 – 0.3 m) | 0.54 → 0.47 | |
| Bell stiffness E (1 – 30 kPa) | 0.47 → 0.42 | Weak at tank scale; matters for T14 and T06 |
| Mucus adhesion (0 → 3 Pa) | 0.42 → 0.49 | Within noise |

Across all of these ranges, **η_r(11°) stays between 0.38 and 0.64, never reaching 0.7**. No plausible value of an unknown physical parameter rescues T03 on its own.

**Design levers** (these are choices, not uncertainties):

| Change | η_r(11°) | Stuck |
|---|---|---|
| Bypass 3% of lane flow (≈ the v3 lift) | **0.30** | 56% |
| Bypass 10% (nominal) | 0.43 | 39% |
| Bypass 20% | 0.59 | 32% |
| Bypass 35% (entrance velocity ≈ approach velocity) | **0.82** | 17% |
| Geometrically scaled 1.5–2.5 cm bells, 10% bypass | 0.63 | 37% |
| Same small bells, 3% bypass | 0.44 | 53% |
| 10 cm entrance (instead of 6 cm), 10% bypass | 0.61 | 31% |
| 10 cm entrance, 3% bypass | 0.52 | 38% |
| 4 entrances, 20% bypass | **0.73** | 27% |

**What this means.** In the twin, the pass/fail outcome of T03 is set mainly by **bypass flow** and by **bell size relative to entrance size**, not by the uncertain bell physics. The verdict is FAIL at the nominal tank settings, and η_r crosses 0.7 at roughly 25–30% bypass flow, or with 4 entrances. At the ~2–4% bypass that the v3 lift sizing implies, the twin predicts η_r ≈ 0.3–0.45. That is a prototype-relevant warning the physical tank should test directly. If it is confirmed, the design needs more bypass flow (recirculated) or wider, more frequent entrances.

## What the real tank must confirm (in priority order)
1. **T03 η_r with bypass flow measured.** Log the siphon/pump flow as a % of lane flow on the datasheet, and test a second bell size (1.5–2.5 cm) or a wider entrance (≥3 bell diameters). The twin says this decides pass or fail. It is also a warning for the prototype: the v3 lift of 2 m³/s per line is only ~2–4% of the lane flow.
2. **Where the bells jam.** Photograph the face and count bells per bay. This tests the twin's prediction that the bypass-mouth jam dominates and that bay 4 carries the load (T07).
3. **Bell-on-mesh friction and adhesion.** Use a tilted wet mesh: the slide angle gives μ. Measure the gel's E with a weight on a disc. These are the twin's unknowns.
4. **Surrogate density.** Degas the gel and tune salt in the **tank water**. Accept a "slow sinker" class, and report the measured settling velocities instead of "hover" (T01).
5. **T06:** lower the strip **before** releasing bells (the twin lets 4–12 bells slip under during lowering).
6. **T10:** the interlock detection rate needs ≥0.999. A door alone cannot tell a passive turtle model from bells at tank scale (mN forces). Turtles impinging on the face is a separate risk to measure.
7. **T05/T15:** ΔP is 0.3–5 mm and forces are 0.1–7 N. Use a manometer with ≤0.2 mm resolution and a load cell, not two clear tubes and a luggage scale.
8. **T14:** gel bells cannot answer the prototype question. Do a small test with real jellyfish tissue, or a much softer gel (E < 300 Pa).
9. **T16:** ≥20 counts per run, or report the discrepancy in bells, not %.

## Honesty notes
- Pass thresholds in T05 (≤1.5× ΔP), T07 (≤35%) and the T01 "hover" definition (≤5 mm/s) are **our operationalisations** of vague pre-registered wording. They were fixed before these results were seen.
- Nominal parameters were chosen before the runs, and none were tuned to reach a pass.
- T08 (η_g ≈ 1) is likely optimistic, and T09 is a parametric model.
- The machine was heavily shared while the sensitivity runs were made, so those runs were shortened (120 s, 3 seeds).
