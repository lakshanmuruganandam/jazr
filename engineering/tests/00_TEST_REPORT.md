# JAZR test programme: master report
*11 Oct 2026. Everything here is **computational or model-based** (simulation, engineering calculation, real public data, literature). **No physical prototype has been tested yet.** Simulated "physical" tests are labelled SIMULATED. Every number traces to the folder named in brackets.*

## Scoreboard
| # | Stream | Checks | PASS | MARGINAL | FAIL | UNKNOWN / INFO | Automated tests |
|---|---|---|---|---|---|---|---|
| 00 | Real data: currents, waves, SST, wind, jellyfish, turtles | 10 assumptions | 6 OK | — | 4 CHANGE | — | — |
| 01 | Twin verification & validation | 10 test families | analytic within 0.7%; converged; 23/23 rows reproduced | — | dt ≥ 300 s skips the capture zone | no field validation | **pytest 54/54** |
| 02 | Hydraulics & structures | 300 | 180 | 43 | 77 (many deliberate stress cases) | — | `run_all.py` (~50 s) |
| 03 | CFD of the angled screen and outer line | 5 tests | screen sweep at 11° ✔, mass ~1e-13 | through-velocity uneven | outer line 0–14% | 2D only | — |
| 04 | Biology, wildlife, FMEA, operations | 41 | 12 | 11 | 8 | 9 | **pytest 16/16** |
| 05 | Economics, risk, regulatory, compliance | 19 tests + 14 permit items | 19 tests pass; 2 permits PASS | — | — | 11 permit RISK | **pytest 19/19** |
| 06 | Physical test protocols (pre-registered) | 16 tank + 8 flume + 5 pilot | — | — | — | to run | data sheets ready |
| 07 | Virtual tank (SIMULATED T01–T16) | 16 protocols × ≥3 runs | 7 | — | 5 (+1 kill: turtle, camera only) | 3 report-only | — |
| 08 | FEA, seismic, extremes, controls, human factors, LCA, climate | 81 | 48 | 12 | 15 (4 are rejected alternatives) | 6 | **pytest 23/23** |


Alert-arrival timing ✔ · wind drift ✔ · release-point ranking ✔ · stranding/beaching ✔ · real-data hindcast ✔ (292 windows) · retention (closed vs open) ✔ · sizing regression ✔ · cost and emissions tables ✔ · dashboard/OS smoke test ✔.

**Also covered:** CFD, FEA and modal analysis, fatigue, seismic, extreme events and 2085 climate, model-checked control logic (26,633 states), cyber, human factors, LCA, Sobol/Morris sensitivity, Monte Carlo, FMEA/FTA, operations DES, economics Monte Carlo, regulatory checklist, virtual tank, pre-registered physical protocols.

## What the tests changed (v3 → v4)
| Finding | Source | v4 change |
|---|---|---|
| Roll-up cleaning lets 18–29% through; drum wrap overstresses the mesh | 08, 07 | Angled **travelling-belt** screens (1.2% leak; 9.5% with all faults) |
| Guidance depends on entrance flow (3% → 0.30; 20% → 0.73; 35% → 0.82) | 07, 02 | Entrances draw 15–20% of lane flow + **dewatering** |
| Apex entrance decides guidance (100% with it vs 0–74% without, 2D) | 03 | **Mandatory apex entrance**, wider mouths, graded baffles |
| Outer line only 0–14% effective with turtle gaps | 03 | Outer line → **optional** |
| Typical onshore drift is 2.5 cm/s (stress 5–6) | 00 | **Release-or-Recover** policy → intake share ≈ 1 − η_r (~10% at η_r = 0.9, flat with bloom length) |
| Real bells 0.33 kg, 6.5–12 cm; Gulf species mostly *C. perezi* | 00 | Loads 2–9× smaller; **turtle-excluder grid** now possible; species wording fixed |
| Camera-only turtle protection = kill; bypass mouth faster than juvenile turtles swim | 07, 04 | Excluder grid + camera/sonar 2-of-3 + screw auto-stop + escape chute |
| Pump trip pulls a vacuum; pipe floats; screws >5.9 m unproven | 02 | Two-stage screws → **gravity** head tank → pipe through the breakwater, trenched |
| 10 m bays release 2.1 t pulses; low-tide velocity 0.22 m/s | 02, 08 | Bays ≤4.8 m; sized at low tide and max flow |
| Fixed 200 Pa trip unreliable; comms-loss and motor-only fail-open fail | 02, 08, 04 | Compensated blockage index, wave filter, shear-pin passive relief, staggered slots + hard-wired interlock, 2-of-3 voting |
| Duplex corrodes at 36–39 °C | 02, 08 | Titanium / Cu-Ni / polymer wetted parts |
| Late alerts: 5% deploy in time with two approvals | 04 | Auto-deploy on close red alerts (operator veto) |
| Payback depends on the unknown the plant event rate (break-even ≈0.9 unit-days per unit-year) | 05 | **JAZR Core first** (software + one-unit pilot) |
| Cyber unspecified (9/13 items) | 08, 05 | FANR-REG-08 / IEC 62443 plan, air gap |

## Headline numbers that survived testing (all model-based)
- **Real-current hindcast (292 alerts):** Today 71% reaches the intake; v3 6.2%. The ordering holds in 99% of windows.
- **v4, typical drift:** ~10% (η_r 0.9), 30% (η_r 0.7), 51% (η_r 0.5), against 97–100% today. **η_r is the number to measure.**
- **Crew-hours −60% to −90%; energy 0.033% of plant output; structure, fatigue and seismic pass; control logic deadlock-free.**

## Still unknown (needs physical tests or field data)
η_r at prototype scale (T03/T04, F01) · bell survival through screw and pipe (T09, P02) · excluder grid with real turtles (F06) · bell–mesh friction and stiffness (T05, T14) · drift-back at sea (P01) · the plant event rate (ENEC data).

## Housekeeping
`03_cfd_flow/data/cache` and `cache_v2` are leftovers from early model versions. Delete them yourself if you want; they don't affect results.
