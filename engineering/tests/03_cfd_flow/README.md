# 03 – CFD flow tests for JAZR Gate v3 (inner angled screen and outer guide line)

All numbers here come from the scripts in this folder. Python, numpy, scipy and matplotlib only. No CFD package was installed (no OpenFOAM), so I wrote a small solver for this work.

**Bottom line**
- **In 2D, sweeping bells to the bypass works at 11°, but only if there is an entrance at the apex.** With the apex entrance, 100% of bells reached an entrance in every one of the 300 runs (8–20°, 15/30/60 m spacing, 1–4% bypass, 0.30/0.45 m bells, 0/3.6/10 cm/s swimming). Without it, only 0–74% did; the rest drifted to the closed apex, where they would pile up.
- **The through-screen velocity is not uniform.** At 11° it rises from about 0.07 m/s at the upstream end to about 0.13–0.14 m/s at the apex end (fine-grid mean 0.10; max 0.13–0.14).
- **Passive 0.45 m bells mostly miss the flush intermediate entrances.** At 11° they ride the face to the apex. In practice the apex entrance and its lift have to be sized for most of the load.
- **The outer partial-depth curtain line did not reach the twin's eta_g of 0.4–0.6.** It got 0–14%. A full-depth mesh line with no gaps got 100%, and with turtle gaps 8–11%.

## Contents
| File | What it is |
|---|---|
| `jzcfd.py` | Solver core (2D depth-averaged incompressible Navier–Stokes, staggered MAC grid, projection method, porous-screen band, sinks) |
| `lane.py` | Geometry of one training-walled lane, flow solve with cache, face diagnostics |
| `particles.py` | Tracker for finite-size bells (contact, friction/impingement, swimming, capture at mouths) |
| `t1_verification.py` … `t5_outer_guide.py` | One script per test |
| `run_all.sh` | Reruns everything in order (uses the cache) |
| `data/` | JSON/CSV/NPZ results and logs. Cached flows are in `data/cache_v3`. `data/cache` and `data/cache_v2` are stale caches from buggy early model versions and can be deleted. |
| `figs/` | PNG figures |

**Model.** Plan view, depth-averaged (rigid lid). Each unit has a lane W = 28 m wide and h = 7 m deep, carrying Q = 100 m³/s, so U = 0.51 m/s.
- Eddy viscosity ν_t = 0.012 m²/s (Elder-type, about 0.07·u*·h). Bed friction Cf = 0.0025. Training walls are free-slip.
- The screen runs straight from wall to wall at angle θ, so its length is L = W/sinθ (147 m at 11°).
- The screen is a smeared porous jump:
  - normal loss k·ρVn²/2, with k from the wire-screen correlation k = 1.3(1−β) + (1/β−1)². β = 0.5 gives k = 1.65.
  - tangential "refraction" loss calibrated to α = 1.1/√(1+k) (Schubauer et al. / Laws & Livesey).
- Bypass entrances are 2 m mouths. Each is a sink with a solid back wall, at s = L − b/2 − n·spacing. The n = 0 mouth is the apex entrance.
- Production grid: dx = 0.5 m (24k cells). Each flow takes 50–150 s on an idle core.

## Run-time note (please read)
The machine was heavily shared during this work (load average 140–230 on 10 cores), so wall times are 10–60× longer than on an idle machine.
- On an idle machine each single flow takes under about 3 min (T1 timings).
- Batches took 15–80 min because of the contention.
- Unsteady runs that hit the wall-time cap before time-averaging were detected (`lane.status`) and re-solved warm-started (`flows W`).
- To save time, 8° and 20° use bypass 2% and 4% only. 11° and 15° use the full 1–4% set.
- T4 used dx = 1.0 m.
- The `baffle100` case in T2 never finished averaging (an unconverged snapshot), so it is **excluded** from conclusions.

---

## T1 – Verification (`t1_verification.py`, `data/t1_verification.json`, `figs/t1_grid_convergence.png`)
**Purpose.** Show that the solver reproduces the screen physics it was given, conserves mass, and converges with grid refinement.

**Method and results**
- **(a) Porous-jump calibration.** A 90° (normal) screen at U = 0.51 m/s. Measured Δp / (k·U²/2) = **1.000** for k = 0.57, 1.65 and 6.35. (The fractional-step bias found during development is corrected in `Flow2D._c`.)
- **(b) Refraction.** A 45° screen. The share of tangential velocity kept across the screen was 0.71 against a target of 0.68 (k = 1.65), and 0.52 against 0.41 (k = 6.35). So the CFD removes slightly *less* sweep momentum than the gauze law → INFO.
- **(c) Mass balance.** Inflow = outflow + bypass sinks to |imbalance| < 1e-13 in every run. Every cell's divergence is below 1e-12. A connectivity check confirms the screen is **watertight** (no leak path around it) in every run.
- **(d) Grid convergence.** Baseline 11°, dx = 1.0 / 0.5 / 0.25 m (6k / 24k / 96k cells). The 0.25 m run took 442 s.

| Quantity | 1.0 m | 0.5 m | 0.25 m | Richardson extrapolation | GCI (fine grid) |
|---|---|---|---|---|---|
| Vn, upstream 5–15% of the face | 0.056 | 0.067 | 0.072 | 0.076 | 7% |
| Vn, 60–75% | 0.134 | 0.123 | 0.116 | 0.102 | 15% |
| Vn, 85–97% | 0.150 | 0.133 | 0.126 | 0.119 | 6% |
| Vn max (core) | 0.156 | 0.142 | 0.132 | 0.114 | 17% |
| Vt, upstream (1 m off the face) | 0.48 | 0.51 | 0.51 | 0.51 | 0.04% |

All quantities converge monotonically. The observed order is 0.6–1.1 for Vn and about 2–4 for Vt.

**Verdict: PASS**, with a stated error band. Production dx = 0.5 m **overstates the non-uniformity of Vn by about 10–20%**. Vt is grid-converged. The overall inlet-to-outlet head loss is *not* grid-converged (GCI 93%), so I make no head-loss claims.

## T2 – Through-screen and sweep velocity along the face (`t2_face_velocity.py`, `figs/t2_*.png`, `data/t2_results.json`)
**Purpose.** Is the through-screen velocity 0.10 m/s uniform, where are the hot spots, and how do angle, porosity, bypass flow and spacing change it?

**Method.** 19 steady (or time-averaged) flows at dx = 0.5 m. Vn is sampled on the screen centre line; Vt is sampled 1 m upstream of the face. The lane width is held at 28 m, so the screen area changes with angle.

**Results** (Vn in m/s; Vt/Vn uses the core 5–95% of the face)

| Case | Area (m²) | Vn mean | Vn p95 | Vn max | CV | Face share >0.12 | Vt mean | Vt/Vn mean (min) |
|---|---|---|---|---|---|---|---|---|
| 8° | 1408 | 0.074 | 0.108 | 0.114 | 0.43 | 0% | 0.62 | 8.4 (5.9) |
| **11° (v3)** | 1027 | 0.100 | 0.137 | 0.142 | 0.31 | 35% | 0.59 | 6.0 (4.6) |
| 15° | 757 | 0.135 | 0.177 | 0.181 | 0.26 | 77% | 0.58 | 4.3 (3.2) |
| 20° | 573 | 0.179 | 0.225 | 0.230 | 0.21 | 97% | 0.55 | 3.1 (2.3) |
| 11°, no entrances | 1027 | 0.096 | 0.120 | 0.124 | 0.16 | 5% | 0.57 | 6.0 (5.2) |
| 11°, entrances every 15 m | 1027 | 0.105 | 0.162 | 0.166 | 0.46 | 46% | 0.64 | 6.1 (4.3) |
| 11°, every 60 m | 1027 | 0.097 | 0.124 | 0.129 | 0.21 | 13% | 0.57 | 5.9 (4.7) |
| 11°, back-baffle k = 30 | 1027 | 0.092 | 0.129 | 0.146 | 0.29 | 18% | 0.62 | 6.7 (4.4) |
| 20°, back-baffle k = 30 | 573 | 0.163 | 0.191 | 0.208 | 0.15 | 92% | 0.55 | 3.3 (2.4) |

- Porosity barely matters: β of 0.3 / 0.7 gives max 0.148 / 0.138.
- Bypass fraction barely matters: 0 to 4% moves the max between 0.144 and 0.140.
- ν_t from 0.006 to 0.05 changes the max by less than 1%.
- The screen loss (k·Vn²/2 ≈ 1 mm of head) is tiny compared with the approach dynamic head (about 13 mm). So **porosity cannot control the distribution**.

**Findings**
1. Vn is **not uniform**. It rises in steps along the face, from about 0.07 m/s at the upstream end to 0.13–0.14 m/s near the apex (about 0.12 after grid-error correction, T1).
2. Each bypass-entrance structure (its solid back wall) leaves a wake on the downstream side. The section just downstream of each entrance then carries more flow. Closer entrances (15 m) create more hot spots: max 0.166.
3. The sweep velocity is 0.5–0.7 m/s and *increases* toward the apex. Vt/Vn stays at 4.6 or above everywhere at 11°, so the "sweep/through ≈ 5" assumption holds on average.

**Verdict vs v3 assumptions**
- **11° sweep/through ≈ 5 → PASS.**
- **"0.10 m/s through-velocity" → FAIL as a uniform value.** The mean is 0.10, but about 35% of the face runs above 0.12 and peaks are about 0.13–0.14 (fine grid / extrapolated about 0.12–0.13).
- 15° and 20° in a 28 m lane fail the 0.10 m/s criterion outright (mean 0.135 / 0.179).

**Design implications**
- Keep 11° or less, or widen the lane if the angle is increased.
- Add **adjustable porosity/baffles behind the downstream ~40% of the face**, as on fish screens. In the model, a uniform k = 30 back baffle cut the 11° share above 0.12 from 35% to 18% but did not remove the peak. Graded (not uniform) baffling is needed; I did not test it.
- Streamline the entrance structures so their wakes don't create hot spots.

## T3 – Bell tracking and guidance efficiency (`t3_particles.py`, `particles.py`, `data/t3_table.csv`, `figs/t3_*.png`)
**Purpose.** Estimate guidance efficiency to the bypass entrances against angle, spacing, bypass fraction, bell size and swimming.

**Method**
- 300 runs × 1000 bells.
- Bells have D = 0.30 / 0.45 m and swim at 0, 3.6 or 10 cm/s with a random heading (persistence 10 s). They are advected with RK2.
- A bell contacts the face when its centre is within D/2 of it.
- On the face it slides at the local sweep velocity if tangential drag exceeds μ × the pinning force (k+1)ρVn²A/2. μ = 0.5 by default; I also tested 1, 2 and 4.
- A bell is captured when its centre crosses the face plane inside a mouth it fits through.
- Flows: dx = 0.5 m, 8/11/15/20° × 15/30/60 m × bypass 1–4%. Extras at 11° and 20°: no apex entrance; 50% of the bypass flow to the apex; 1 m or 4 m mouths.
- **Grid check** (11°, 30 m, 2%):
  - With the apex entrance, total capture is 100% on all three grids.
  - The split between intermediate and apex entrances depends on the grid for *passive* bells. On the 0.25 m grid every passive bell went to the apex.
  - So shares caught by intermediate entrances are reported as ranges, not point values.

**Results**

| Angle / spacing | Captured (with apex entrance) | Share caught by intermediate entrances, mean (range) | Median time on face to capture (s) | p90 (s) |
|---|---|---|---|---|
| 8° / 30 m | 100% | 0.18 (0.00–0.55) | 24–70 | 160 |
| **11° / 30 m** | **100%** | **0.42 (0.00–0.74)** | **20–51** | **124** |
| 11° / 15 m | 100% | 0.61 (0.00–0.85) | 10–47 | 110 |
| 11° / 60 m | 100% | 0.14 (0.00–0.30) | 40–57 | 125 |
| 15° / 30 m | 100% | 0.53 (0.36–0.64) | 18–24 | 76 |
| 20° / 30 m | 100% | 0.51 (0.40–0.55) | 16–20 | 50 |
| 20° / 60 m | 100% | 0.00 | 34–35 | 72 |

- **Impingement.** No bell was held on the face at any angle up to 20°, even with μ = 4. The lowest Vt/Vn is 2.3, which is above the sliding threshold.
- **No apex entrance** (11°, 2% or 4% bypass): only 0–74% are captured. Passive 0.45 m bells: 0%. The rest are delivered to the apex corner, where in reality they pile up. The tracker logs them as "leaked" because the corner is not modelled as a trap, so read that number as *apex pile-up*, not a real leak. At 20° the figure is 40–55%.
- **Mouth width.** A 1 m mouth (bypass mouth width about 2D) catches nothing at the intermediate entrances (0–10%), so everything goes to the apex. A 4 m mouth raises the intermediate share (11°, passive 0.30 m: 0.71).
- **Bypass fraction.** Going from 1% to 4% only nudges the intermediate share (0.39 → 0.43 at 11° and 15°). The capture width of a flush slot is about q_e/(h·Vt), roughly 0.1–0.2 m, which is smaller than a bell radius.
- **Swimming.** Swimming *helps* intermediate capture: mean share 0.31 passive, 0.37 at 3.6 cm/s, 0.45 at 10 cm/s.

**Verdict.** Sweep-to-bypass at 11° → **PASS (2D, conditional)**.
- Guidance efficiency is **100% in 2D** whenever an apex (terminal) entrance exists.
- The "entrances every ~30 m, each ~60 s of travel" picture → **FAIL as stated.** Flush intermediate entrances catch 0–74% (0% for passive 0.45 m bells on the fine grid). Most bells travel to the apex: median 20–51 s, p90 about 2 min, which exceeds the 60 s exposure target.
- These 2D numbers are an **upper bound**. 3D leakage (bottom bar, bay joints, vertical flow) and turbulence are not modelled.

**Design implications**
- Make the **apex entrance mandatory** and size it, and its screw line, for 50–100% of the bell flux.
- Bias the bypass flow to the apex. With a 50% apex split, delivery stays at 100%.
- Use mouths of 4 m or more, or protruding scoops / en-échelon screen steps, if intermediate entrances are meant to share the load.
- 15° captures faster (p90 76 s) but breaks the 0.10 m/s criterion unless the lane is widened.

## T4 – Clogging feedback (`t4_clogging.py`, `data/t4_results.json`, `figs/t4_clogging.png`)
**Purpose.** Bells sitting on the face block mesh. Does that redistribute the flow into hot spots or blind the screen?

**Method**
- Track 2000 bells (D = 0.35 m, swimming 3.6 cm/s) to get the bell-seconds spent on each 2 m of face.
- Convert to coverage: c(s) = bell-seconds × (density·Q / N) × πD²/4 / (2 m · h), capped at 0.6.
- Update the screen: β_eff = 0.5(1−c), k(s) from the correlation, and the pinning force uses the local k. Under-relax and iterate 4 times with warm-started flow.
- 11°, 30 m spacing, 2% bypass. dx = 1.0 m, chosen because of machine load (T1 shows about 15–20% Vn error at this grid).

**Results**

| Density | Face coverage, mean / max | Vn max: clean → clogged | Max screen Δp | Captured |
|---|---|---|---|---|
| 0.1 /m³ | 3% / 7% | 0.156 → 0.156 | 2.1 → 2.3 mm | 100% |
| **0.3 /m³ (design)** | **8% / 18%** | 0.156 → 0.157 | 2.1 → 3.0 mm | 100% |
| 1.0 /m³ | 23% / 51% | 0.156 → 0.166 | 2.1 → 9.1 mm | 100% |
| 0.3 /m³, no apex entrance | 8% / 28% (apex pile-up not counted) | 0.153 → 0.155 | 2.0 → 3.0 mm | 46–47% |

- Coverage peaks toward the downstream half of the face.
- The v3 text quotes "≈18% at 0.3/m³". In the CFD that is the *peak*; the mean is 8%.

**Verdict → PASS** at 0.1–1.0 /m³ with bells flowing freely to an apex entrance. The flow redistributes only modestly: about +6% hot-spot Vn at 1/m³, and coverage up to 51% locally. Blinding is not triggered because bells keep moving.

**Design implications**
- The real blinding risk is **stalled bells**: no apex entrance, an entrance that is full or stopped (camera/turtle auto-stop), or 3D corners.
- The load-cell Δp signal at 1/m³ is only about 9 mm of head. Trip thresholds must be set around that scale and filtered against waves, as in v3.

## T5 – Outer guide line (`t5_outer_guide.py`, `data/t5_*.json`, `figs/t5_slice.png`, `figs/t5_planview_eta.png`)
**Purpose.** Can partial-depth curtains at 15–25° to the tide achieve the twin's eta_g of 0.4–0.6?

**Method**

*(A) Vertical slice normal to the line (2.5D)*
- Water depth H = 3.5 m (twin offshore depth). Approach normal velocity U·sin20° with U = 0.117 m/s (twin's M2 amplitude).
- Curtains: mesh (k = 1.65) or solid, at d_c/H = 0.5 or 0.75.
- Grids dz = 0.2 and 0.1 m. They agree within 5% for mesh, and k_eff for the solid 0.75 curtain differs by 20%.

*(B) Plan view*
- A 1000 m line at 15/20/25°. Grid dx = 10 m, all runs converged, mass imbalance < 1e-15.
- The line is a porous line with k_eff taken from (A). Variants: no gaps, or 10 m turtle gaps every 100 m.
- 3000 bells with a depth coordinate:
  - Bells deeper than the curtain tip pass under.
  - Bells that meet the face slide along it and sink with the face downdraft from (A) until they clear the tip.
- **eta_g = bells delivered to the end of the line ÷ bells that met it.**

**Results**

Slice:

| Curtain | Share of flow through the curtain | k_eff | Downdraft at mid-curtain |
|---|---|---|---|
| Mesh, d_c/H 0.5 | 41% | 0.68 | 0.09·Un |
| Mesh, d_c/H 0.75 | 68% | 1.11 | 0.06·Un |
| Solid, d_c/H 0.5 | 0% (all flow dives under) | 7.9 | 0.46·Un |
| Solid, d_c/H 0.75 | 0% | 33 | 0.57·Un |

How far a passive bell slides sideways before it is carried under the tip:
- Mesh: **5–110 m**.
- Solid: **1–11 m**.

These distances are set only by geometry (≈ d_c·cotα × a factor), not by current speed.

Plan view, eta_g (range over swimming 0 / 3.6 cm/s and uniform vs upper-half depth):

| Curtain | No gaps | With gaps |
|---|---|---|
| Mesh, d_c/H 0.5 | 0.01–0.03 | 0.01–0.04 |
| Mesh, d_c/H 0.75 | 0.04–0.14 | 0.03–0.10 |
| Solid, 0.5 or 0.75 | 0.00–0.01 | 0.00–0.02 |
| Full-depth mesh | 1.00 (2D ideal) | 0.08–0.11 |

**Verdict → FAIL** against the twin's eta_g of 0.4–0.6 for a passive or weak-swimming bell with partial-depth, gapped curtains. A line 1000 m long cannot carry bells to its end when they escape under the tip within about 1–110 m.

**Design implications**
- In the twin, use **eta_g of about 0–0.15** for the outer line until a tank or field test says otherwise. v3 itself says the outer line is Stage 2.
- Making it work would need some combination of:
  - (near) full-depth mesh;
  - overlapping baffles or short line segments, each ending in its own collection pocket, instead of straight gaps;
  - or proof that bells actively hold position near the surface. Upward swimming is **not** modelled here and could change the result.

---

## Limitations (all tests)
- **2D depth-averaged, rigid lid.**
  - No vertical structure in the lane: no bottom-bar leakage, no vertical sweep, no surface or bed boundary layers.
  - T5's 3D effect comes only through a 2.5D slice; the coupling is a correction, not a 3D solution.
  - The 100% guidance figures are therefore an *upper bound*.
- **Turbulence.**
  - A constant depth-averaged eddy viscosity of 0.012 m²/s, so model Reynolds number U·W/ν_t ≈ 1.2e3, versus about 1.4e7 in reality.
  - There are no turbulent fluctuations acting on the bells beyond their swimming noise.
  - Vortex shedding behind entrance structures is resolved only coarsely and time-averaged. Bells are tracked in the *mean* field.
- **Screen law.**
  - Uses Idelchik-type k(β) and the Schubauer refraction law. The refraction check matched to about 5–30%.
  - The pinning and friction model (μ, the areas, and the (k+1) factor) is assumed. The impingement conclusion holds up to μ = 4.
- **Bells.**
  - Rigid discs with no deformation, extrusion or damage.
  - No bell–bell interaction except the coverage feedback in T4.
  - Swimming is random-heading only, with no rheotaxis or vertical behaviour.
- **Grid.**
  - The production grid overstates Vn non-uniformity by about 10–20%.
  - Intermediate-entrance shares for passive bells depend on the grid.
  - T4 ran on a 1 m grid.
  - T5 plan view ran at 10 m: the 10 m gaps are geometric in the tracker and not resolved in the flow.
- **Inputs.**
  - Site values (H = 3.5 m, U = 0.117 m/s) are taken from the project twin, not from measurements.
  - Turtle-gap layout (10 m every 100 m) and the 2 m mouth width are my assumptions, because the design does not specify them.
