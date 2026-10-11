# JAZR · Bloom Incident OS: operator control dashboard

This is the control-room HMI for **JAZR v4.1 / v5**, which protects the the plant intakes from jellyfish blooms. It is a student entry in the ATRC ATP 2026 ENEC track. Species: Blue Blubber jellyfish, *Catostylus* sp. (Gulf records are mostly *C. perezi*).

> **SIMULATED DATA, illustrative.** Every live value comes from a simulated data generator (`js/sim.js`). Nothing here is plant data. JAZR is model-based only and no physical prototype exists. The Evidence and Compliance tabs show **real results** taken from `TESTS/` and `twin/out/`, and each one cites its source file.

## Open
Double-click `index.html`. It works over `file://` with no server. The first load needs internet for one pinned library: **Apache ECharts 5.5.0** from cdnjs (`https://cdnjs.cloudflare.com/ajax/libs/echarts/5.5.0/echarts.min.js`). There are no other network assets. The *3D tour* tab embeds `../sim3d/index.html`, which loads three.js r128 by itself.

URL parameters: `?scenario=severe&tab=main&theme=dark&speed=300&pause=1&t=21600&wall=1`
- `t` = pre-run seconds of simulated time.
- `wall=1` = large type for the wall screen.

## Design
- **ISA-101 high-performance HMI.**
  - Calm greys. Colour is used only for abnormal states and alarm priorities.
  - Normal equipment is shown by fill and outline, never by red/green.
  - Bad-quality (stale) data is flagged during comms loss.
- **ISA-18.2 alarm management.**
  - Four priorities, each with a redundant shape: 1 square, 2 triangle, 3 diamond, 4 circle.
  - States: UNACK, ACKED, RTN-UNACK, SHELVED and SUPPRESSED.
  - Shelving needs a reason, expires after 30 min, and is never offered for P1 alarms.
  - State-based suppression and flood grouping (more than 10 alarms per 10 min).
  - A deadband on analog alarms to stop chatter.
  - Each alarm is rationalised with cause, consequence, response and time to respond.
  - The page also shows the alarm-rate KPI, priority distribution, bad actors and the journal.
- **Light and dark** modes (auto, light or dark). **Wall** mode enlarges type.
- The Main Dashboard fits **1920×1080 with no scrolling**. Other pages reflow down to phone width.

## Tabs
| Tab | Content |
|---|---|
| **Main Dashboard** | One-screen DCS view. **Command bar:** Watch → Ready → Deploy → Operate → Stand-down (+ SAFE), Trigger alert, Approve deploy, Veto, Stand-down, Emergency raise-all, auto-deploy countdown, alert source and severity, time since deploy. **Status:** hard-wired interlock and comms/cyber lamps, tide clock. **Live SVG mimic:** 4 lanes × 42 belt bays shaded by blockage index → entrances and split → **Layer 2 hydro-jet curtain** (water only, between the belt screen and the plant's own screens, feeding a surface skimmer into the same collector; faceplate shows jet header pressure, jet flow, skimmer flow, caught count) → flat-plate dewatering → excluder + 3-channel vote → 3-chamber HydroLift cycling → head tank → side-stream O₂ → pipe with O₂ sensors → near/far outlets. Click any element to open its **faceplate** with setpoints and interlock-checked commands. **Right column:** ISA-18.2 alarm list and AI advisory (Accept/Reject). **Bottom strip:** *released alive* is the prominent tile (DOA → reuse is a small secondary line), then mini-trends (got past JAZR, diverted t/h, released alive, η_r estimate, O₂ min, BI max, turtles, crew on shift, Today vs JAZR) |
| Simulation | Embeds `sim/index.html`, the live JS twin built by a separate agent and validated against the Python twin (worst difference 1.4 pp). See `sim/README.md` |
| Screens | BI heatmap (4×42), selected bay (ΔP A/B/load-cell, 2oo3 vote), belt speed vs sweep per lane, motor current, wave filter (raw vs τ 30 s + 20 s persistence, with an Hs slider), trends |
| Bypass & Lift | Entrance split (design band 15–20 %), HydroLift chamber cycle, O₂ along the pipe, head tank, O₂ dose, throughput, per-lane table |
| Release | Schematic map (intake, near/far outlets, illustrative exclusion zones, ensemble tracks), 10-day distance fan (P10–P90), cumulative return risk, documented response when O₂ is low, decision log with operator approval, twin reference |
| Wildlife | No-acoustics / no-nets / no-lethal badges, live 3-channel votes, excluder events, lock auto-holds, fish routed, sighting log (operators can add entries) |
| Biology | O₂ budget by biomass (09 `o2_budget.csv`), velocity rule along the path, release ΔT/ΔS, settlement plates (polyp habitat, simulated), 20 biology rules with live status |
| Alarms | Full ISA-18.2 page (described above), with CSV export |
| Trends & Analytics | η_r estimate from camera counts with 90 % CI, leak %, throughput, both survival estimates, what-if, AI closed-loop tuning (advisory), copilot and AI decision log |
| Evidence | Real results: scoreboard, v5 FINAL table, η_r levers (TESTS/11), twin v4.1, hindcast, release location, no-harm alternatives, mechanisms, virtual tank, Morris/Sobol, hydraulics verdicts, economics payback curve, crew-hours, survival budget and Monte Carlo, AI controller, FEA/seismic/climate, controls model checking, data checks |
| Compliance | Permit checklist (05), cyber checklist IEC 62443 / FANR-REG-08 (08), live no-harm charter, AI governance |
| Maintenance | Belt/drum health heatmap, asset list by RUL (winches, lock gates, dewatering, O₂ dissolver, diffusers), trend + forecast, work orders |
| Reports | Bloom summary, ledger (routed alive / DOA → reuse / transit mortality model), EAD release log, OS event log. CSV exports carry a SIMULATED header. Print |

## Scenarios (selector in the app bar)
- **Calm:** Watch state, quiet screen.
- **Typical bloom 0.3/m³:** Release-Near.
- **Severe 1/m³:** beyond design density. 8 entrances, Release-Far, and pipe O₂ reaches LOW-LOW. The documented response is: near route if the forecast allows, extra O₂ lines, throttle entrance flow.
- **Late alert (24 min):** auto-deploy after a 120 s veto window.
- **Bay fault:** belt seizes → overcurrent trip → winch jams → stuck-drive FAULT → passive shear-pin flap. A stuck ΔP transmitter is masked by 2oo3.
- **Turtle event:** 3/3 vote and lock hold, a 1oo3 sonar ghost (fail-safe hold), and a dugong sighting.
- **Comms loss:** local TDMA + hard-wired busy loop, lowering inhibited, stale values.
- **Long onshore-drift bloom (10 d):** Release-Far.

A **training autopilot** (on by default; it can be unticked) stands in for a simulated operator. It approves routine steps after a delay so that unattended demos keep moving. Every action it takes is logged as "Training autopilot (SIM)".

## How the numbers tie to the design (illustrative model)
- **Flow and mass:** lane flow 101 m³/s nominal (172.5 m³/s design max) and 0.33 kg per animal. That gives about 12 t/h per unit at 0.1/m³ and about 36 t/h at 0.3/m³.
- **Bays:** 42 bays per lane. Belts run at 0.5–1.0× sweep toward the apex.
- **Control logic** mirrors `TESTS/08…/D_controls/controller.py` and `bloom_os.py`:
  - deploy ≈ 573 s, with L = 6 bays lowering at once and K = 1 bay raising (pulse rule);
  - BI H 35 % / HH 55 %, 20 s persistence, 2oo3 voting;
  - passive shear-pin relief at 450 Pa;
  - close RED alert (< 1 h) auto-deploys and the operator can veto;
  - Recover mode is removed (v4.1).
- **η_r:** simulated truth is about 0.95–0.97 with the default setpoints. It is estimated from camera counts with a Kalman filter. With Layer 2, leak to plant = (1 − η₁)(1 − η₂); η₂ 0.5–0.9 is illustrative (default jet pressure 2 bar → η₂ 0.7). With η₁ ≈ 0.97 the plant sees ≈ 0.9 %; at η₁ 0.99–0.996 it would be ≈ 0.04–0.5 %. Without Layer 2, leak ≈ 1 − η_r (far release). The v5 FINAL claim is η_r 0.95–0.99 for design (simulation best 1.000, 95 % lower bound 0.996).
- **Lift, pipe and O₂:**
  - HydroLift with 3 chambers, cycle 220 s, 6 m head;
  - gravity pipe 1.6 m at ≈ 1 m/s, transit ≈ 1.5 h (near) / 2.9 h (far);
  - side-stream dissolved O₂ with an outlet setpoint of 5.5 mg/L;
  - respiration 0.05 mL O₂/h/g (04 T1);
  - diffuser exit ≤ 1 m/s.
- **Survival:** two ESTIMATES, both shown:
  - engineering budget 0.978 (0.87–0.99) (`TESTS/10_mechanisms/survival_budget.csv`);
  - conservative Monte Carlo 0.76 (0.68–0.85) (`TESTS/11…/survival_chain.csv`);
  - the design target is ≥ 0.95.
- **What-if** is a closed-form approximation, **not the twin**: leak = (1 − η)/(1 − η·R). Checked against twin rows:

| Case (far release, 2.5 cm/s, 10 d) | Twin | What-if |
|---|---|---|
| η_r 0.9 | 10.4 % | 11 % |
| η_r 0.77 (v4.1) | 23.5 % | 24.6 % |
| η_r 0.99 | 1.15 % | 1.1 % |
| η_r 0.996 | 0.39 % | 0.46 % |
| Near-only, η_r 0.9 | 49.9 % | 49 % |

The particle twin port and its 16-case validation table are in `sim/README.md` (all within ±3 pp, worst 1.4 pp).

## AI
- The copilot and closed-loop tuning are **advisory only**. They suggest entrance split, belt speed, maintenance, outlet approval and alarm shelving. They **never** take safety actions: no deploy/veto, no bay motion, no interlocks, no HydroLift hold/restart, and no outlet change without operator confirmation.
- In this demo, rule-based logic stands in for the model. There are no network calls, consistent with the air-gap requirement.
- TESTS/11 finds that the AI closed loop adds value mainly as a backup: η_r 0.81 vs 0.76 when the belt fails.

## Files
```
index.html            app shell (header, tabs, faceplate drawer)
css/hmi.css           ISA-101 tokens, light/dark, wall mode
js/sim.js             simulated plant + control logic + drift ensemble + what-if
js/alarms.js          ISA-18.2 alarm manager, predictive maintenance, advisory copilot
js/ui.js              helpers, ECharts theming, faceplates, CSV export
js/main.js            Main Dashboard (mimic, command bar, alarms, advisory, strip)
js/pages.js           Screens, Bypass & Lift, Release, Wildlife, Biology, Alarms, Trends, Maintenance, Reports
js/evidence.js        Evidence, Compliance, Simulation/3D embeds
js/evidence_data.js   real results extracted from TESTS/ and twin/out (with source paths)
js/evidence11.js      TESTS/11_eta_max_sims results + v5 FINAL table
tools/shoot.cjs       headless Chrome check (console errors) + screenshots → shots/
sim/                  live Simulation module (separate agent)
```

## Verify
```
NODE_PATH=$(npm root -g) node tools/shoot.cjs          # all tabs, 0 console errors expected
```
Screenshots are in `shots/`, named `<tab>_<scenario>_<theme>.png` at 1920×1080. The last run had 0 console errors.

## Honesty notes
- No bubble curtain anywhere: air under the bell kills jellyfish (AZA). Layer 2 uses water jets only.
- The map is schematic, not to scale and not for navigation. Exclusion zones are illustrative.
- Settlement plates, maintenance health and fish counts are simulated.
- Jellyfish survival through the lift and pipe is **unmeasured**. The decisive test is a 3 h recirculating pipe loop with 96 h scoring (T09/P02).
- The Severe 1/m³ scenario intentionally shows the design limit: pipe O₂ falls below target beyond the design density.
