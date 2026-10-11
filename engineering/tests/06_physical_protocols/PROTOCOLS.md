# JAZR Gate v3: physical test programme (pre-registered)
*Written **before** testing on 11 Oct 2026. Pass criteria are fixed now and must not be changed after seeing results. Every result, good or bad, is reported. The blank data sheets are in `datasheets/`.*

## Ground rules (apply to every test)
- **Repeats:** at least 3 runs per condition. Report the mean, min and max.
- **Filming:** top-down with a ruler in frame, continuous; keep the files raw. Name files `T##_condition_run.mp4`.
- **Counting:** two people count independently, and video counts break ties (T16).
- **Randomise:** run conditions in random order, not best-first.
- **Kill criteria:** if a design fails its kill threshold, say so in the pitch and show what changed.
- **Scaling:** the tank is about 1:8 to 1:20 geometric scale. Velocities scale by √scale (Froude): 1:20 → ÷4.47, so 0.5 m/s → 11 cm/s and 0.10 m/s → 2.2 cm/s. Surrogate bells don't swim; say so.
- **Honesty line for every slide:** "Tank surrogate test, scale ~1:X, N runs; not field-validated."

## Tier 0: kitchen tank (tonight)
| ID | Test | Method | Measures | Pass (pre-registered) | Kill |
|---|---|---|---|---|---|
| T01 | **Surrogate characterisation** | Agar/gelatin domes 4–6 cm; tune salt until they hover | Diameter, mass, buoyancy class | ≥80% of bells hover (near-neutral) | — |
| T02 | **Baseline intake capture** | No screen; release 30 bells upstream; run 3 min | % reaching "intake" pump mesh | — (reference) | — |
| T03 | **Inner screen guidance η_r** | Roll-down mesh at 11° (also 8°, 15°, 20°), training-card walls, 2 bypass slots | % to bypass, % to intake, % stuck | **η_r ≥ 0.7 at 11°** | η_r < 0.4 at every angle → redesign |
| T04 | **Entrance spacing** | 2 vs 4 bypass slots along the face | η_r, stuck count | More entrances → fewer stuck | — |
| T05 | **Clogging / blinding** | Feed bells continuously at rising rates; with/without "bay cycling" (lift the strip briefly); water-level difference as ΔP (two clear tubes) | ΔP over time, % face covered (photo), leaks | Cycling keeps ΔP stable at the design rate | Face >50% covered in <1 min at the design rate |
| T06 | **Roll-down deployment and seal** | Lower the strip by string into slots; time it; check the bottom bar seats | Deploy time, bottom gap, bells passing under | Gap ≈0; **0 bells under** | Bells pass under in >10% of runs |
| T07 | **Staged relief pulse** | With bells on the face, lift one bay only | Bells released per lift, % reaching intake | Pulse is a small fraction of bells on the face | — |
| T08 | **Outer guide line η_g** | Card curtain line at 15/20/25°; flow both directions (reverse the pump) | % deflected | η_g ≥ 0.4 in both directions | — |
| T09 | **Passage damage** | Bells through hand screw / siphon / small pump / long tube (1–5 m) | Intact %, damage score 0–3 | ≥90% intact via screw/siphon | <50% intact → change the lift method |
| T10 | **Turtle model** | Weighted clay turtle (rigid); camera-trigger mock = a person lifts the diverter on sight; also the spring door with a spring scale | Diverted %, door force, time | **100% of turtle passes diverted or exit** | Any turtle reaching the screw path |
| T11 | **Fish return** | Small rigid "fish" beads | % returned via bypass | Report (no target) | — |
| T12 | **Drift-back vs distance** | Reversing flow (swap the pump end every 60 s); release bells at 3 distances from the intake | Returns after k cycles | Returns fall with distance | — |
| T13 | **Waves** | Hand paddle at one end, small waves | η_r change, leaks over/under | η_r drops <20% | — |
| T14 | **Fragment extrusion** | Cut bells into 1–2 cm pieces; push into the mesh at flow | % extruded, ΔP | Report; sets the mesh opening | — |
| T15 | **Bay load** | Luggage/spring scale on the strip at clean / half-blinded | Force (N) | Scales with blinding; compare with calc | — |
| T16 | **Repeatability** | Two counters + video for 3 random runs | Count discrepancy | ≤5% discrepancy | — |

**Minimum set if time is short tonight:** T01 → T02 → T03 (11° only) → T06 → T09 → T10. That is enough for the slides.

## Tier 1: flume (shortlist → Demo Day 10–13 Nov)
| ID | Test | Adds |
|---|---|---|
| F01 | T03–T05 in a 2 m flume at Froude-scaled 0.5 / 0.10 m/s, 3D-printed screen at 11° | Proper velocities, ADV/float velocity profile |
| F02 | **Roll-down motor + load cell (HX711) + auto roll-up on ΔP threshold**, logged | Fail-safe demonstrated in hardware |
| F03 | **Twin-in-the-loop**: servo outlet valve switched by the Ebb Window code from a tide clock | Software–hardware integration |
| F04 | 3D-printed rotating-tube Archimedes screw model, motorised; damage vs rpm | Lift survival curve |
| F05 | OpenCV bell counter vs human counts | Automated counting accuracy |
| F06 | Camera turtle detection (YOLO-class model on turtle-model images) → diverter servo; latency and detection rate | Wildlife interlock performance |
| F07 | Tidal reversal + outer line + inner screen together, 20 cycles | System-level %-to-intake vs the twin's prediction |
| F08 | Endurance: 500 roll-down cycles | Mechanism wear |

## Tier 2: field pilot (Season 1, with permits)
| ID | Test | Purpose |
|---|---|---|
| P01 | GPS drifters + dye released at the candidate outlets, 72 h tracking | **Validates the drift-back curve** (nobody has measured this) |
| P02 | Post-release survival of real *Catostylus* after screw/pipe passage (holding tanks, 24–96 h) | First scyphozoan survival data (none exist) |
| P03 | One 250 m outer-line string, deflection measured by drone-free methods (shore camera, ADCP) | Real η_g |
| P04 | One screen bay prototype in a non-intake lane | Real η_r, fouling, load |
| P05 | Turtle and dugong observation protocol (observers + passive acoustics, no active sonar) | Wildlife safety evidence for EAD |

## Reporting template (per test)
`Test ID · date · scale · N runs · conditions · result (mean, range) · pass/fail vs pre-registered criterion · video files · notes/anomalies`. The results feed straight into the twin as η_r and η_g (`TESTS/01_twin_VV`).
