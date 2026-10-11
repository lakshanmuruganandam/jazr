# 04 · Biology, wildlife, safety and operations tests: JAZR Gate v3

*Run on 11 Oct 2026. To reproduce: `python3 run_all.py`. It runs T1–T8, then pytest on T9 and the analysis sanity checks (16 tests pass), and writes `results/verdicts.md` and `results/summary.json`.*

**Honesty rules used here.** Every number carries a tag:
- **[SRC n]**: from the literature listed in `params.py` (`SOURCES`).
- **[DESIGN]**: from `JAZR_GATE_v3.md`.
- **[ASSUME]**: our own placeholder. It is not data.
- **[DERIVED]**: computed from the tagged numbers above.

No study anywhere has tested a scyphozoan passing through a screw, pump or km-scale pipe. Every jellyfish-survival verdict is therefore UNKNOWN unless the stressor is trivially small. Fish thresholds are used only as analogues.

**Verdict counts (41 checks):** 12 PASS (incl. 1 conditional, 1 model-only, 1 software-only) · 11 MARGINAL · 9 UNKNOWN · 8 FAIL (incl. 1 vs-claim, 1 as-specified) · 1 REQUIREMENT. The full table is in `results/verdicts.md`.

| File | What it is |
|---|---|
| `params.py` | Shared parameters, source list, DO-saturation function (Garcia & Gordon 1992) |
| `t1_jelly_transport.py` | T1: damage screening along the chain; thermal and O₂ in transit; spawning; breakwater siphon |
| `t2_wildlife.py` | T2: turtle, dugong and dolphin speeds vs device velocities; breath-hold; camera requirement; stop distance |
| `t3_fish_bycatch.py` | T3: fish bycatch and survival chain |
| `t4_release_ecology.py` | T4: decay O₂ demand, benthic loading, **stranding**, exclusion zones, EAD |
| `t5_fmea_fta.py` | T5: 32-row FMEA (`results/t5_fmea.md`/`.csv`), two fault trees, common-mode (β-factor) |
| `t6_ops_des.py` | T6: discrete-event simulation of a bloom season (custom heap-based engine; simpy is not installed) |
| `t7_reliability.py` | T7: bay k-out-of-n, fail-open on demand, load-cell voting |
| `t8_retention.py` | T8: **closed-floor vs open-skirt retention** (Monte Carlo on analogues) |
| `bloom_os.py`, `test_bloom_os.py` | T9: **Bloom Incident OS state machine** plus a pytest smoke test (distant and close alert end to end) |
| `test_analyses.py` | Physics and arithmetic sanity tests on the outputs |
| `charts/` | 6 PNG charts |

---

## T1: Jellyfish (and fish) damage along the chain
**Purpose.** Screen each stage (screen sweep → bypass → screw → head tank → pump → 5 km pipe) against the available thresholds.

**Method.**
- Pipe: v = 1.77 m/s and residence 47 min [DERIVED]. Smooth and 2.5×-fouled friction. From these we get wall shear, viscous-sublayer thickness, the Kolmogorov strain rate and the strain rate at bell scale.
- Screw: Red Bluff analogue, 3.05 m at 26.5 rpm [SRC 7]. Contact probability with the leading edge, using the blade-strike geometry P = N·n·L/(60·V_ax).
- Thermal rise from pump heat.
- O₂ drawdown, using rhizostome respiration of 0.05 mL O₂ h⁻¹ g⁻¹ WW (active, 30 °C) [SRC 9], against DO saturation at 35.8 °C and S = 40 (5.56 mg/L).
- Hydraulic grade line where the pipe crosses the breakwater.

**Results.**
- Bulk strain is 176–278 s⁻¹. That is below the 500 s⁻¹ no-injury level for juvenile fish [SRC 2] and the 400–600 s⁻¹ larval guideline [SRC 3]. Wall strain is 5,200 s⁻¹, but only within a 59 µm sublayer. At bell scale the strain is ~0.6 s⁻¹.
- Screw tip speed is 4.2 m/s. A 30–45 cm bell has a **0.61–0.91** chance of contacting the leading edge on each pass.
- The pump adds less than 0.04 °C.
- O₂: the pilot load (35 t/h) ends at 5.3 mg/L. At **0.3/m³ on one line**, DO ends at **3.0 mg/L**, close to the 2.61 sublethal mean [SRC 10]. At **1/m³ on one line**, the water goes anoxic.
- With a breakwater crest at +6 m [ASSUME] and a clean pipe, the pressure head at the crest is only 0.3 m at 5 km. At 3 km it is negative, so air comes out of solution (gas under the bell is harmful [SRC 22]).

**Verdicts.**
- PASS: pipe shear for fish, pressure, thermal, bypass acceleration (0.067 s⁻¹ vs NMFS 0.2).
- MARGINAL: O₂ in the line, the pump, the breakwater siphon.
- UNKNOWN: jellyfish in the pipe, the screw leading edge, screen contact and the drum, stress spawning [SRC 23].

**Design implications.**
1. **Delete the pump.** Lift to a gravity head tank with two screws in series, so no animal ever passes an impeller.
2. Fit a rubber or rounded leading edge on the screw and run at low rpm.
3. Split flow into **≥3 lines at 0.3/m³**, or inject O₂ (the Huon live-fish pipe precedent), and put a DO sensor at the outlet.
4. Route the pipe **through** the breakwater, or set the head tank at least 2 m above the crest.
5. Interlock: a bay may not roll up until its face is clear, otherwise bells are wound into the drum.

## T2: Turtles, dugongs and dolphins
**Purpose.** Can each species escape every device velocity? How long would an air-breather be submerged in the enclosed path? What camera performance and stopping distance are needed?

**Method.**
- Measured speeds:
  - Turtle cruising 0.27–0.50 m/s (loggerhead and green, speed loggers) [SRC 4].
  - Juvenile hawksbill 0.125–0.16 m/s net, juvenile green 0.17 m/s net [SRC 5].
  - Dugong cruising 0.6–1.1 m/s [SRC 6].
  - No verified humpback-dolphin speed; mean dive 20 s [SRC 19].
- Breath-hold vs the NMFS 55/75 min tow-time limit and 2 h forced-submergence failure [SRC 18].
- Detection requirement: target ≤0.01 turtle harmed per site-year [ASSUME criterion]; 1–50 turtles reaching a bypass per unit-season [ASSUME: the plant has no intake-capture data, and ENEC's 70 turtles/yr were stranded or distressed animals].
- Camera recall 0.83–0.85 from published turtle detectors [SRC 17].

**Results.**
- The 0.10 m/s approach is below EPA 316(b)'s 0.15 m/s [SRC 16].
- The 0.5 m/s lane equals the top of turtle cruising speed, so juveniles will be carried to the bypass.
- The 0.4–0.7 m/s bypass mouth exceeds what a juvenile turtle can sustain.
- The pipe is 47 min full-bore.
- Required system protection is **≥0.99975** at 10 turtles per unit-season. One camera achieves 0.955. Three independent cameras achieve 0.9989. Two cameras plus a physical "deformable-pass" grid achieve 0.99966, which tolerates only about 7 passages per unit-season.
- **Stopping distance** at 0.7 m/s, with the turtle swimming with the flow, 0.42 s detection latency and a 1.5 safety factor:
  - camera **≥10 m** upstream for the diverter (2–5 s actuation [ASSUME]);
  - **≥37 m** for a screw stop (5–20 s spin-down [ASSUME]).

**Verdicts.**
- PASS: approach velocity.
- MARGINAL: lane velocity; dugongs and dolphins in the lane.
- **FAIL:** bypass mouth, breath-hold (if entry is possible), camera-only protection.
- REQUIREMENT: stop distance.

**Design implications.**
1. Treat turtle exclusion as **safety-critical, not a backup**.
2. Use two diverse sensors (optical + imaging sonar, which works in turbid water and at night).
3. Add a **physical deformable-pass grid** in front of the screw (soft bells squeeze through, rigid shells don't). This is an untested idea and needs a tank test.
4. Put a final camera gate at least 37 m before the screw entrance, or make the diverter the primary barrier.
5. Fit a large-animal bar rack at the lane entrance, about 0.5 m clear (passes 45 cm bells), and stop work when a dugong or dolphin is sighted.

## T3: Fish bycatch and return
**Method.** Monte Carlo over the survival chain, using stage survivals from analogues:
- GCID screen 0.85–1.0;
- Archimedes screw 0.98–1.0;
- Hidrostal 96 h 0.87–0.99 [SRC 7];
- pipe slurry and release, which are **[ASSUME]** (no data).

Bycatch volume is given for channel fish densities of 0.1–10 per 1,000 m³ [ASSUME].

**Results.**
- Chain survival median 48% (5–95%: 32–70%); 52% without the pump.
- The Hudson full-scale angled screen shows how delayed mortality can dominate: 90% initial survival, 35% at 96 h.
- The lane could send 173 to 69,000 fish per unit-day into the bypass.

**Verdicts.**
- UNKNOWN: survival, volume.
- MARGINAL: the "fish-return benefit" claim. the plant's own plant-screen baseline survival is not public.

**Implications.** Do not claim a fish benefit. Say "fish survival is measured in the pilot". Get an EAD baseline fish survey of the channel.

## T4: Release ecology, stranding and EAD
**Method.**
- Decomposition O₂ demand of 15.7 µmol g⁻¹ WW d⁻¹ [DERIVED from SRC 8; a lower bound, since the cores ran out of O₂]. Decay takes about 5 days [SRC 24].
- A box-flushing O₂ supply at the outlet (0.08 m/s × 4 m × 1 km [ASSUME]).
- Benthic carcass loading, compared with the ~1.3 kg/m² *Rhopilema* stock that caused hypoxia within 24 h [SRC 8].
- Straight-line time to shore under 3 cm/s residual drift and 4–17 cm/s wind drift. Keesing found >90% of catostylid strandings came 2 days after onshore wind [SRC 13].

**Results.**
- Live release: O₂ is fine.
- Dead biomass at design density: 7,000 t/d per unit. The water-column demand is 0.6× the assumed flushing supply. Carcasses would need **~350 km²** to stay below 0.1 kg/m².
- **Stranding:** from 5 km, the drift reaches shore in 46 h (3 cm/s) or 14 h (10 cm/s wind). Both are inside the 72 h forecast window.
- ENEC's artificial reef 3.8 km offshore and the EAD/ENEC coral nurseries lie close to a 5 km outlet.
- EAD regulates liquid discharges to the sea through its marine water-quality executive regulation, but the numeric limits were not retrieved.

**Verdicts.**
- PASS: live-release O₂.
- **FAIL:** dead release.
- MARGINAL: stranding, reef exclusion.
- UNKNOWN: EAD numbers.

**Stranding criterion (new test).**
1. Use a wind-forced ensemble forecast: fewer than 5% of particles may beach within 72 h of release.
2. Run beach count transects at 0, 24, 48 and 72 h along the nearest 20 km of shore.
3. Release GPS drifters with each pilot release.
4. If strandings exceed 2× baseline, switch automatically to "recover".

**Implications.**
1. Fit a damage-scoring camera at the head tank. The dead or damaged fraction always goes to "recover".
2. Fit a DO/turbidity buoy at each outlet.
3. Keep outlets at least 2 km from reefs and coral nurseries.
4. Pre-consult EAD.

## T5: FMEA, fault trees, common mode
**FMEA.** 32 failure modes; the full table is in `results/t5_fmea.md`. The top RPNs are:

| Failure mode | RPN |
|---|---|
| Camera misses turtle | 360 |
| Pump impeller damage | 252 |
| Screw leading-edge damage | 245 |
| Late or absent alert | 224 |
| Low DO in line | 210 |
| Wrong outlet | 180 |
| Dead biomass released | 168 |
| Bottom bar not seated | 150 |
| Load cell failed low | 144 |

Ratings are engineering judgement.

**Fault tree: "intake blockage despite JAZR"** (basic events [ASSUME]). P = 0.089 per bloom per unit, against 0.30 today, a 70% reduction. The dominant term is **"not deployed in time"** (0.050).
- Verdict: PASS (conditional).

**Fault tree: "wildlife harm".** P = 0.20 per bloom per unit. The main terms are stranding 0.10, dead release 0.05 and turtle into screw 0.023.
- Verdict: **FAIL** against a 0.01 target.

**Common mode.** The alert, bloom density, water clarity, site power and software are shared across all 4 units (β 0.5–1.0). That makes P(all 4 units affected) ~10²–10⁵× higher than if the units were independent.
- Verdict: **FAIL vs claim.** v3's "no common-mode failure across units" must be reworded.
- **Implications:** independent local PLC and panel per unit; diverse software; fail-open on loss of power.

## T6: Operations DES (bloom season)
**Method.**
- One unit, Oct–Nov, 3,000 seasons (about 9,000 blooms).
- Blooms: Poisson with mean 3 per season [ASSUME]; duration lognormal, median 72 h, clipped to 12–240 h (Shin Hanul 4 d, Hanbit 10 d).
- Alerts: 85% arrive 4–6 h ahead (brief); 15% are close alerts of 0–0.5 h [ASSUME].
- Two human approvals, each lognormal with median 8 min by day and 20 min by night [ASSUME].
- 18 bays: MTBF 2,000–8,000 h, MTTR median 8 h. Two lift lines: MTBF 1,500–6,000 h, MTTR 24 h. All [ASSUME].
- Crew today: Hanbit gate crew rose from 7–8 to 20; Gravelines ran 7 boats 24/7 (3 crew per boat [ASSUME]) [SRC 20].

**Results.**
- Far alerts: 99.99% deployed before arrival. Approval latency p90 is 65 min.
- **Close alerts: only 5% deployed before arrival** and 0.51 h unprotected. With pre-authorised auto-deploy this rises to 59% and 0.04 h.
- Bloom-hour availability (≥ n−1 bays and ≥1 line) is 0.994.
- Crew: **423 person-h per bloom vs 1,097–3,459 today** (−61% to −88% at 13% leakage). At 28% leakage the reduction is 38–80%. Pre-season work adds 160 person-h per unit.

**Verdicts.** PASS: far response, availability, crew-hours. **FAIL:** close alert.

**Implication.** On a RED close alert, the OS must auto-deploy under pre-authorisation, as implemented in T9. "No crew" is false: say "~60–90% fewer crew-hours".

## T7: Reliability
**Results.**
- A 10-day bloom sees 0.5–2.2 bay failures per unit.
- To keep P(≥2 of 18 bays down) ≤1%, bays need MTBF ≥1,000 h at 8 h MTTR, or ≥2,900 h at 24 h MTTR.
- Motor-only roll-up has a PFD of 0.01–0.05 per demand [ASSUME], so it is **not fail-open**.
- Single load cell: PFD 1.7×10⁻³ and 0.44 spurious roll-ups per drum per year (about 32 per year across 72 drums). With 2oo3 voting (two cells plus lane dP): PFD 9×10⁻⁵ and 0.02 per drum per year.

**Verdicts.** MARGINAL: bays, load cells. **FAIL as specified:** fail-open.

**Implications.**
1. Fit an independent gravity or shear-pin release on every bottom bar.
2. Use 2oo3 sensing.
3. Keep spare drive cassettes on the gantry so MTTR stays ≤8 h.
4. Required availability:
   - screen ≥0.95 per bloom;
   - lift ≥0.99;
   - the wildlife-protection function at PFD ≤10⁻³ (SIL-2-like).

## T8: Retention, closed floor vs open skirt
**Method.** Monte Carlo over three vertical distributions of bells:
- surface layer (C. mosaicus is mostly in the top 1 m);
- uniform;
- ebb-sinking.

Water depth is 5.5–11.8 m and relative velocity 0.1–0.6 m/s. For the open skirt, underflow loss above 0.35 m/s follows oil-boom practice [SRC 14]. The closed floor loses bells only by extrusion through a 0–10 cm seal gap near the bed [ASSUME].

**Results.**
- Open 2 m skirt: 4–79% retained. Open 5 m skirt: 45–90%.
- JAZR closed floor: **≥97.7%**, even with an unseated bar.

**Verdicts.** PASS (model only): closed vs open. UNKNOWN: floor seal with sand and fouling, mesh extrusion.

**Implications.** Fit a seat sensor on the bottom bar and jet the rail before deployment. Tank test with sand in the rail and bells near the bed.

## T9: Bloom Incident OS smoke test (pytest)
`bloom_os.py` implements IDLE → READY → DEPLOYING → OPERATING → STANDDOWN → IDLE. The 9 tests in `test_bloom_os.py` all pass:
- a distant alert runs end to end with human approvals;
- a close RED alert auto-deploys within 15 min;
- without pre-authorisation, a close alert waits;
- invalid transitions are rejected;
- the relief bay never deploys;
- a 10 s dP spike is filtered out;
- 4 bays blinding together roll up **one at a time**;
- a turtle detection stops the screw and moves the diverter to ESCAPE, then restarts after 60 s clear;
- no safe outlet switches to RECOVER;
- the dashboard state is complete and JSON-serialisable.

**Verdict.** PASS. It is software logic only; there is no hardware in the loop.

---

## Physical tests still needed (all UNKNOWN items)
1. **Live C. mosaicus** (EAD permit) through the screw at 2 rpm settings, with a rubber leading edge: % intact at 0 h and 24 h.
2. 47 min recirculating pipe loop at 1.8 m/s and 5–40 kg/m³: integrity, DO and planula/gamete counts.
3. Screen contact and roll-up: bells on the mesh during a drum cycle.
4. Floor-rail seal with sand, and bells at the bed.
5. Mesh extrusion at 10–200 Pa.
6. Turtle-proxy and bell sorting on a deformable-pass grid, plus camera and sonar recall in turbid water at night. Pass criterion: 0 failures in ≥300 trials, which gives a 95% upper bound of 1%.
7. Drifter and beach-survey stranding protocol (T4).
8. Channel fish survey.

## Key sources (full list with URLs in `params.py`)
- NMFS 2022 passage manual.
- Neitzel et al. 2004.
- Kinoshita et al. (J Exp Biol, jeb236216) on turtle cruising speeds.
- JCU sirenian movement review.
- USBR Red Bluff/Tracy vol. 25.
- Guy-Haim et al. 2020, Biogeosciences 17:5489.
- Purcell et al. 2010, Hydrobiologia.
- Vaquer-Sunyer & Duarte 2008, PNAS.
- Cassiopea thermal tolerance, Front. Mar. Sci. 2020.
- Aravind et al. 2023 (UAEU).
- Keesing et al. 2016.
- UVM Sea Grant oil-boom guide.
- EPA 316(b) 2014.
- NMFS tow-time rule (FR 1998).
- Xiamen Sousa dive study 2025.
- St. Lucie NRC records.
- AZA jellyfish manual.

**Not found:**
- any scyphozoan survival data for screws, pumps or pipes;
- a humpback-dolphin swim speed;
- C. mosaicus thermal limits;
- EAD numeric discharge limits;
- turtle push force;
- turtle encounter rates at the plant's intake.
