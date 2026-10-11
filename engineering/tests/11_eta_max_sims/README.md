# 11: Raising the inner-screen guidance efficiency η_r toward 0.99, plus the end-to-end survival chain

> **Everything in this folder is SIMULATED or model-based.** These are virtual-tank runs, 2D CFD particle tracking, a replayed controller, a Monte Carlo built on literature analogues, and the reduced-order twin. Nothing here is a measurement. Suggested slide wording: *"Simulated (virtual tank 1:20 + 2D lane CFD), N seeded runs; not a physical test."*
>
> Folders `03_cfd_flow`, `07_virtual_tank` and `twin/` were **not edited**. Their code was copied into `src/` (`vtank.py`, `jzcfd.py`, `lane.py`, `particles.py`), with the CFD cache redirected to `results/cfd_cache`, or imported read-only (`twin/jazr_twin.py`).

## Bottom line
1. **Best combination:**
   - 35% entrance flow with dewatering, **50% of it sent to the apex entrance**;
   - a **conveyor (travelling-belt) screen moving toward the apex at 0.5× the sweep speed**;
   - flared intermediate mouths (1.6× capture width);
   - graded baffles behind the downstream 40% of the face;
   - a wall jet at 0.25× sweep;
   - a low-friction mesh coating (μ 0.1).

   **Simulated η_r in the virtual tank: 900/900 bells guided over 30 seeds, η_r = 1.000, 95% lower bound 0.996** (Clopper–Pearson). The v4.1 tank analogue is **0.773 [0.759–0.787]**.
2. **The conveyor alone does almost all the work in the tank.** A belt at 0.25× sweep or faster takes η_r from 0.76 to 1.00, because it carries jammed bells to the apex entrance.
   - **Without the belt**, the other levers stack to the same result: 0.82 → 0.90 (flared) → 0.97 (baffles) → 0.992 (wall jet) → 1.000 (μ 0.1; lower bound 0.996).
   - So the design has **redundancy**: the "belt stopped" stress case still gives 1.000 (300/300).
3. **At prototype scale (2D CFD, real 6.5–12 cm bells, 2–6 m scoops), η_r is about 1.0 whenever there is an apex entrance.** Without one it is 0.76.
   - The tank's jamming comes from a bell-to-mouth ratio of about 1.2. At full scale the ratio is ≥17 (2 m scoop, 12 cm bell), so mouth jamming should not occur.
   - **The tank is therefore the conservative bound and the CFD the optimistic bound.**
   - The real remaining loss paths are 3D leak paths that neither model has: seals, bay joints, bottom bar. The physical tank must find them.
4. **Plant-scale twin, using the given settings:** **% of the swarm reaching the plant screens**:
   - v4.1 (η 0.773): 22.4% in a 72 h bloom, 23.5% in 240 h;
   - two screens in series (η 0.953): 4.9% / 5.1%;
   - **best combination at its 95% lower bound (η 0.996): 0.36% / 0.39%**;
   - the sweep gives 1.1% / 1.15% at η 0.99;
   - today, with no JAZR: 97% / 100%.
5. **End-to-end survival of guided bells, best screen, Monte Carlo median (5–95%):**
   - screw + O₂ pipe: **0.74 (0.66–0.83)**;
   - fish lock + O₂: 0.76 (0.68–0.85);
   - vacuum pump + O₂: 0.56 (0.40–0.74);
   - **without O₂ at 0.3 /m³, about 0.54 (0.34–0.75)** for the screw. O₂ injection is worth about 20 percentage points.

   **Dewatering and the 3 h pipe dominate the uncertainty** (each accounts for about 37% of the variance). The screen stage is only about 1–3% of losses once jams are gone. **No scyphomedusa has ever been tested through any of these stages**, so every stage range is a labelled analogue or assumption.

## Files
| File | What it is |
|---|---|
| `src/vt_ext.py` | Virtual-tank extensions: conveyor (moving-wall friction in the belt frame), graded baffles (iterated resistance), wall jet, apex on/off and apex share, flared mouths, fouled bay, rheotactic and HYPOTHETICAL cue swimming, contact and time-on-face counters, two screens in series |
| `src/run_vt.py` | Tank lever study (groups L1–L9, COMBO, NOBELT, STRESS, CUE) → `results/vt_runs.jsonl`, `results/vt_levers.csv` |
| `src/proto_flows.py`, `src/proto_track.py`, `src/run_proto.py` | Prototype 28 m lane: 24 CFD flows (entrance flow 3–50%, scoops 2/4/6 m, apex off, apex share, graded baffle k-profiles), and a tracker extended with belt, jet, clogging feedback, rheotactic and cue swimming, low flow → `results/proto_levers.csv` |
| `src/controller.py` | AI closed-loop controller (27-arm pool + replayed bandits) → `results/controller.json`, `controller_summary.csv` |
| `src/survival.py` | Survival-chain Monte Carlo → `results/survival_stages.csv`, `survival_chain.csv` |
| `src/run_twin.py` | Plant twin with the new η_r values → `results/twin_eta.csv` |
| `src/charts.py`, `src/make_gif.py` | `charts/01–08_*.png`, `charts/before_after_v41_vs_best.gif` |

Re-run in this order: `cd src; python3 run_vt.py; python3 proto_flows.py; python3 run_proto.py; python3 controller.py pool; python3 survival.py; python3 run_twin.py; python3 charts.py; python3 make_gif.py`. Seeds are fixed. Every batch took 1–4 min on 10 cores.

## Models (what each one can and cannot say)
- **Virtual tank (1:20 Froude, a copy of 07):** 2D potential flow, DEM soft bells with Coulomb friction, finite entrance throughput.
  - This is the **jam-limited, conservative** model, and the only one in which bells jam.
  - v4.1 analogue: 4 entrances, 20% entrance flow, μ 0.4, 30 bells of 4–6 cm released as a batch, 180 s.
  - η_r = bells guided ÷ bells that reached the lane. Bells that swam back out of the inlet are excluded.
  - "Jam" means the bell is still on the face or at a mouth at the end. In practice those bells go to the plant through relief or cycling, so the leak is 1 − η_r.
  - Conveyor: Coulomb friction acts on the bell's velocity *relative to the belt*. The belt is assumed to discharge into the apex entrance.
  - Wall jet: added tangential velocity jet × V_sw × exp(−d/3 cm) in front of the face.
- **Prototype tracker (a copy of 03, extended):** time-averaged 2D CFD lane (28 m × 7 m, 100 m³/s, 11°).
  - Real bell sizes; pinning versus sweep drag; belt; jet; coverage feedback at 0.3 and 1 /m³.
  - No bell–bell jamming and no 3D leak paths, so this is the **upper bound**.
  - Swimming is modelled as random, rheotactic (heading into the local flow, the worst case) or HYPOTHETICAL cue-directed. There is also a half-plant-flow case.
- Confidence intervals:
  - "[a–b]" = 95% t-interval over seeds.
  - "lower bound" = pooled Clopper–Pearson 95% lower bound. With 900 bells and none lost, this is 0.996, so **the tank cannot resolve η_r above about 0.996**.

## Results by mechanism (tank: 10 seeds × 30 bells; v4.1 reference 0.760 in this batch; full table in `results/vt_levers.csv`)
| # | Mechanism | Tank η_r (95% CI) | Jam rate | Time on face (prototype-equivalent, s) | Prototype 2D (upper bound) |
|---|---|---|---|---|---|
| 1 | Entrance flow 3% (no dewatering) / 10 / 20 / 35 / 50% | 0.70 / 0.73 / 0.76 / 0.82 / **0.90 [0.88–0.93]** | 0.29 → 0.10 | 123 → 14 | 1.000 at all; time on face 16 → 12 s |
| 2 | Apex mouth 6 / 10 / 13 cm (≈1.2 / 2 / 2.6 m); flared mid mouths ×1.6 / ×2; apex share 50 / 80% | 0.76 / **0.85** / 0.84; 0.82 / **0.86**; 0.75 / 0.77 | 0.24 → 0.14 | 52 → 13 | 2/4/6 m scoops: 1.000; **no apex entrance: 0.76**; at half flow with rheotactic 10 cm/s swimmers, apex share 50% gives 0.999 vs 0.972 for an equal split |
| 3 | **Conveyor 0 / 0.25 / 0.5 / 1.0 × sweep** | 0.76 / **1.00 / 1.00 / 1.00** (300/300) | 0.24 → 0 | 52 → 4 | 1.000 (no bells held at prototype scale) |
| 4 | **Two screens in series** | **0.953 [0.930–0.976]** (stage 2 catches about 80% of what stage 1 leaves) | 0.05 | 55 | — |
| 5 | Friction μ 0.05 / 0.1 / 0.2 / 0.4 | 0.83 / 0.81 / 0.81 / 0.76 | 0.17–0.24 | 41–54 | 1.000 even at μ 4 (sweep/through ≥4.6) |
| 6 | Graded baffles (downstream 40%) | 0.83 [0.77–0.88] | 0.17 | 32 | 1.000 |
| 7 | Wall jet 0.1 / 0.25 / 0.5 × sweep | 0.78 / 0.77 / 0.81 | 0.19–0.23 | 60–64 | 1.000; time on face for rheotactic swimmers at half flow 35 → 24 s |
| 8 | Bells 4–6 / 2–3 cm / geometric 6.5–12 cm (0.3–0.6 cm tank); swimming 3.6 and 10 cm/s, random or rheotactic | 0.76 / 0.70 / **1.00**; 0.77 / 0.78 / 0.77 / **0.74** | — | — | 1.000 at full flow; **0.998 for rheotactic 10 cm/s at half plant flow** |
| 9 | Density 0.3 / 1 /m³ (continuous feed, clogging feedback) | 0.90 / 0.96 | 0.10 / 0.04 | 78 / 51 | 1.000; face cover max 2% / 7% (90% with the old 30–45 cm bell assumption, still 1.000) |

Notes:
- **Single levers other than the belt reach 0.82–0.90.** Two screens in series reach 0.95.
- Continuous feed gives a *higher* η_r than a batch: arriving bells push jammed bells through. That is the same unjamming effect as waves in 07 T13. The batch protocol is the conservative case.
- Geometric-size bells need a mesh smaller than the bell. At 1:20 with a 5 mm mesh they pass through (extrusion), so that case was run with a 1 mm mesh.

### Combinations (30 seeds × 30 bells each; `charts/02_stacking_combinations.png`)
| Stack | η_r | Lower bound | Contacts per bell | Time on face (prototype-equivalent) |
|---|---|---|---|---|
| v4.1 | 0.773 [0.759–0.787] | 0.745 | 1.75 | 53 s |
| + 35% entrance flow | 0.819 | 0.792 | 1.24 | 33 s |
| + belt 0.5× (alone with 20% flow: also 1.000) | 1.000 | 0.996 | 0.97 | 3 s |
| **BEST** (+ flared, baffles, jet 0.25, μ 0.1, apex share 50%) | **1.000** | **0.996** | 0.90 | 2 s |
| No belt: 35% + flared / + baffles / + jet / + μ 0.1 | 0.899 / 0.971 / 0.992 / 1.000 | 0.877 / 0.958 / 0.984 / 0.996 | 0.72–0.81 | 2–13 s |

**Stress tests on BEST (10 seeds):**
- rheotactic 10 cm/s, μ 0.4 (worn coating), fouled downstream bay, 1 /m³ feed, 2–3 cm bells, belt stopped: **all 1.000** (lower bounds 0.985–0.997);
- v4.1 with a fouled bay: 0.747.

**Prototype stress test (half plant flow + rheotactic 10 cm/s + 1 /m³ + μ 0.4):**
- v4.1: 0.998; BEST: 0.995.
- Graded baffles slow the flow near the apex, which lets strong counter-swimmers hold station. That matches the biology rule "no decelerating zones" (09 R10/R11). Baffles should therefore be **tuned for uniform through-velocity without lowering the apex-end sweep**.

### Damage proxies (`charts/04_damage_proxies.png`, `03_prototype_scale.png`)
- **Tank:** BEST cuts the prototype-equivalent time on the face from 53 s to about 2 s per bell, face contacts from 1.75 to 0.9, and the jam rate from 0.23 to 0.
- **Prototype:** 0.8–0.9 contacts and 11–12 s on the face at full flow. Rheotactic swimmers at half flow make 25–30 contacts (repeated touch-and-go). The wall jet reduces that time on face by about 30%.

## (a) AI closed-loop controller (`src/controller.py`, `charts/05_ai_controller.png`)
**Setup:**
- 27 settings: apex share {equal, 50, 80%} × belt {0, 0.25, 0.5} × jet {0, 0.25, 0.5}, at 20% total entrance flow.
- Each setting was simulated in 3 conditions × 6 seeds (486 tank runs).
- The controller sees only the counts per entrance and the bells not guided.
- 120 epochs: nominal → density rising to 1 /m³ → fouled bay → fouled bay plus belt-drive fault. 200 replays.

| Controller | Nominal | Density → 1 /m³ | Fouled bay | Fouled + belt fault | Overall |
|---|---|---|---|---|---|
| **AI: factored discounted Thompson sampling** | 0.993 | 1.000 | 0.999 | **0.808** | **0.950** |
| Per-arm discounted Thompson | 0.989 | 1.000 | 0.998 | 0.786 | 0.943 |
| Best fixed (commissioning choice: belt 0.25, equal split, no jet) | 1.000 | 1.000 | 1.000 | 0.755 | 0.939 |
| v4.1 fixed | 0.783 | 0.949 | 0.756 | 0.756 | 0.811 |
| Oracle (hindsight) | 1.000 | 1.000 | 1.000 | 0.866 | 0.966 |

**Reading:**
- While the belt runs, a fixed belt setting is already optimal, and the controller costs about 0.7 percentage points of exploration in the first phase.
- Its value is **fault adaptation**. When the belt fails it moves to an apex-biased split plus a strong jet and recovers about a third of the gap to the oracle (0.81 vs 0.76).
- Sharing evidence across knobs (the factored version) adapts faster than per-arm sampling. The result was insensitive to the discount (γ 0.6–0.97).
- Recommendation: use the controller as a **supervisory fallback**, not as the primary guidance mechanism.

## (b) Behavioural-cue sensitivity: HYPOTHETICAL (`charts/06_behaviour_cue_hypothetical.png`)
We added a directed swim of ±1–3 cm/s toward (+) or away from (−) a cue at the apex. **No rhizostome phototaxis evidence was found** (09 S1/R15: default dark at night). This is a what-if.
- **Prototype, full flow:** no effect (η_r = 1.000 from −3 to +3 cm/s); the sweep is 0.5–0.7 m/s.
- **Prototype, half plant flow, rheotactic 10 cm/s:**
  - a cue **away** from the apex costs: −1 / −2 / −3 cm/s → 0.979 / 0.959 / 0.932, against 0.998 without a cue;
  - a cue toward it gives 1.000.
  - So a light that *repels* (or that raises counter-current activity, the concern in 09) is a real downside in slack conditions. The upside is small.
- **Tank v4.1 (jam-limited):** any directed motion relieves jams. With a cue toward the apex, +1 / +2 / +3 cm/s → 0.89 / 0.95 / 0.97 (from 0.76). Away from it, about 0.88, which is an artefact of unjamming.
- **BEST:** 1.000 at every cue strength, so the hydraulic design makes behaviour irrelevant.

## Survival chain (`src/survival.py`, `results/survival_*.csv`, `charts/08_survival_chain.png`)
Each stage is drawn uniformly from the range below. Screen stage: S = exp(−h_c·contacts − h_t·time on face), using the contacts and time on face from the simulations.

| Stage | Range | Basis |
|---|---|---|
| Screen hazard per contact / per s on face | 0.002–0.02 / 1e-4–1e-3 | ASSUME (AZA: mesh abrades tissue; no rate data) |
| Entrance | 0.95–0.995 | ANALOGUE (fish bypass) |
| Dewatering (wedge-wire) | 0.85–0.99 | ANALOGUE (fish); jellyfish UNKNOWN |
| Excluder grid 15 cm | 0.97–1.0 | ASSUME |
| Lift: screw / fish lock / vacuum pump | 0.90–0.995 / 0.95–1.0 / 0.50–0.95 | Red Bluff screw trout 98–100%; 07 T09 gel 100%; vacuum pump lowered for degassing bubbles (09 R01/R02) |
| Pipe 3 h with dissolved O₂ / without O₂ at 0.3 /m³ | 0.85–0.99 / 0.40–0.95 | 09 R03–R06: about 7.6 kg/m³ in the pipe at 0.3 /m³, above the 6.6 kg/m³ no-O₂ limit; rhizostome Pc UNKNOWN |
| Outlet | 0.95–1.0 | ASSUME (09 R17) |

Results (median, 5–95%), guided bells, BEST screen:

| Lift | With O₂ | Without O₂ |
|---|---|---|
| Screw | **0.74 (0.66–0.83)** | 0.54 (0.34–0.75) |
| Fish lock | **0.76 (0.68–0.85)** | 0.56 (0.35–0.77) |
| Vacuum pump | 0.56 (0.40–0.74) | 0.40 (0.23–0.65) |

- The v4.1 screen is 1–2 points lower (screen stage 0.969 vs 0.988).
- **Swarm level** (η_r × chain):
  - v4.1 + screw + O₂ → 0.56 of the arriving swarm released alive;
  - BEST + screw + O₂ → about 0.74.
  - The rest of the v4.1 losses are bells that reach the plant screens.
- **Variance drivers:** dewatering (Spearman ρ² ≈ 0.37), pipe (0.37), lift (0.15); the screen (<0.01) no longer matters once jams are gone.
- **Implication:** after the conveyor, the survival work belongs in **dewatering design and pipe O₂**, plus the T09/P02 survival tests. Delayed (96 h) mortality is not included; the Hudson fish case dropped from 90% to 35% at 96 h (04 T3).

## Plant twin (`results/twin_eta.csv`, `charts/07_twin_reaching_plant.png`)
Settings: `system=True, ring=False, policy="immediate", gate_x=10000, gate_y=3000, vr=-0.025`, 4 tide phases × 2 seeds, N = 1500.

| Case | η_r | 72 h | 240 h |
|---|---|---|---|
| Today (no JAZR) | — | 97.0% | 100% |
| v4.1 tank analogue / published 0.73 / published 0.82 | 0.773 / 0.73 / 0.82 | 22.4 / 26.3 / 17.7% | 23.5 / 27.7 / 18.7% |
| Two screens in series | 0.953 | 4.9% | 5.1% |
| η_r = 0.99 (sweep) | 0.99 | 1.1% | 1.15% |
| **BEST, 95% lower bound** | **0.996** | **0.36% (0.13–0.8)** | **0.39%** |
| BEST point estimate | 1.000 | 0% (no other path in the twin) | 0% |

The share reaching the plant is **≈ 1 − η_r**, which confirms v4.1. Getting from 23% to below 1% needs η_r ≥ 0.99.

## Honest limits
- **The two models bracket the answer; neither is the answer.**
  - The tank's jamming is driven by a bell-to-mouth ratio of 1.2. At prototype scale the ratio is ≥17, and the 2D CFD has no 3D leak paths.
  - Real prototype η_r will be set by bottom-bar, seal and bay-joint leakage, belt-to-frame seals (a new leak path the conveyor adds), and stalled bells in 3D corners. None of these is modelled.
- **Conveyor assumptions:**
  - bells in contact move with the belt (Coulomb friction in the belt frame);
  - the belt end discharges into the apex entrance without a pinch point.
  - Belt-seal leakage, carry-over to the back side, and abrasion from belt motion are **not modelled**. Measure them in T03/T05 with a slow belt.
- The wall jet in the tank is a kinematic velocity added in front of the face. Its supply flow and any shear damage are not modelled.
- Twin outputs depend on η_r only through 1 − η_r. Outer-line, drift and forecast effects are as in v4.1.
- The survival chain is the weakest link: **every stage is an analogue or assumption**. Delayed mortality is not included.

## What the physical tank should test next (priority)
1. **T03 with a slow belt** (0.25–0.5× sweep) against a static mesh. The twin predicts η_r of 0.76 → 1.0 at tank scale. Count belt-seal leaks.
2. **T03 without a belt**, at 35% flow with flared mouths, graded baffles and a low-friction mesh. The twin predicts 0.99 or higher; this is the fallback.
3. **Bell-to-mouth ratio:** repeat with mouth/bell ≥5. The twin says jamming vanishes. If it does, the 0.73–0.82 v4.1 numbers are a tank artefact.
4. **Flume with rheotactic live animals at half flow**, to measure the apex-end velocity needed (stop baffles from creating slow zones).
5. **T09/P02 survival:** dewatering and a 3 h O₂-controlled loop decide end-to-end survival more than the screen does.
