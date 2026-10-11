# JAZR Gate v3: hydraulics and structures test suite (02)

This folder holds the engineering checks for `JAZR/JAZR_GATE_v3.md`, run against the site facts in `05_fact_check.md` and `agent_ps_oceanography.md`, the audit in `16_FLAW_AUDIT.md`, and the precedents in `15_jazr_gate_precedents.md`.

**Re-run everything:** `python3 run_all.py` (about 50 s). It rebuilds `out/` and `out/results_summary.csv`, which lists all 300 checks with value, criterion, source and verdict.

**Verdict totals: 180 PASS · 43 MARGINAL · 77 FAIL.** Many FAILs are deliberate stress cases, such as max flow at low tide or 2 ind/m³. The headline problems are listed in §0.

**Honesty rules used here:**
- Site numbers come from the project files.
- Coefficients come from named standards or texts.
- Anything else is labelled ASSUMPTION in the code (`common.py` holds all of them).
- **No data exist** for *Catostylus* friction on mesh, extrusion, or shear tolerance. Every blinding result depends on those assumed values (μ = 0.1–0.3), so they are tank-test items.
- the plant's intake geometry is not public. The 5–7 m lane depth is the brief's assumption.

---

## 0. Headline findings and recommended design changes

| # | Finding | Verdict | Change to v3 |
|---|---|---|---|
| 1 | **The "continuous bay cycling (≈30%)" mode leaks 35–42% of all arriving bells to the plant at every density.** A rolled-up curtain is an open hole with ~3× the conductance of a meshed bay, so the flow and the bells go through it (T03 case F). | **FAIL** | Never open a bay to clean it. Use a **duplex curtain** (a second curtain stays down while the front one cycles), or a travelling belt with fish-bucket lips. Cycle on demand, not continuously. With duplex + on-demand cycling, capture is 98–99% at 0.3 ind/m³ (T03 cases E and G). |
| 2 | **The "<1 t pulse" claim fails.** A 10 m × 7 m bay holds ~1.9 t in a single layer. At the 200 Pa trip the tripping bay is ≥67% covered, giving **≈2.1 t**. Dynamic runs give 2.1–2.5 t per relief pulse at ≥1 ind/m³. | **FAIL** | Use **≤4.8 m bays** (e.g. 4–5 m wide), or a trip at ≤100 Pa with 5 m bays. Alternatively accept and state "≈2 t per pulse". |
| 3 | **Bypass flow of 2 m³/s cannot feed NMFS-style entrances.** It needs ≥1.1 × channel velocity (0.58 m/s), full depth and ≥0.46 m width; v3's 2 m³/s allows only 0.10 m-wide slots. Compliant entrances need **9 m³/s** (0.46 m wide) or **18 m³/s** (0.9 m, sized for 45 cm bells), and up to 31 m³/s at 172.5 m³/s and low tide. | **FAIL** | Add a **secondary dewatering stage** (inclined screen or louvre, as at Tracy) that returns ~16 m³/s to the forebay and sends 2 m³/s to the screw. A ~9:1 ratio is normal fish-facility practice. Otherwise you need 9 screws per unit (T07). |
| 4 | **The weighted bottom bar lifts at ~63 Pa** (a 150 kg/m bar under the curtain's vertical membrane pull). That is before the 200 Pa trip, so bells pass under the bar. Staying seated needs 4.8 t per bay at 200 Pa and 24 t at 1 kPa. | **FAIL** | **Latch the bar into the floor rail.** Make the latch (shear pin or calibrated spring) the **passive gravity-independent relief** the audit asked for, set at the trip Δp. |
| 5 | **Approach velocity at low tide and max flow.** With v3 lengths, Va at LAT is 0.12–0.13 m/s at 100 m³/s and **0.21–0.22 m/s** at 172.5 m³/s. | **FAIL / MARGINAL** | Size at LAT: **L ≈ 171 m in a 7 m lane** (W ≈ 33 m), or 260 m in a 5 m lane. Even then Va = 0.17 at 172.5 m³/s, and full compliance at max flow and LAT needs ~295 m. Prefer the deeper 7 m lane and state the max-flow exceedance. |
| 6 | **The bay drop height is too short.** Bed seal + HAT + wave crest needs **9.7 m** (7 m lane) or 7.7 m (5 m lane). v3 says 5–7 m. | **FAIL** | Specify the drop as "bed to HAT + 1.2 m". |
| 7 | **A fixed 200 Pa trip is not tide- or flow-invariant.** It trips anywhere between 42% and 82% blockage depending on tide and flow. Waves rectify through the quadratic loss: a 60 s filter removes the noise but **not the mean bias**. The compensated blockage index reads 32–44% on a *clean* screen at Hs ≥ 0.58 m (normal incidence) or Hs 1.36 m (along the channel). | **FAIL / MARGINAL** | Trip on a **flow- and tide-compensated blockage index**: ζ_eff from measured Δp, plant flow and level, with a 60 s window. Add a **wave-bias correction** from a channel wave or ADV sensor, and inhibit trips when Hs > 0.5 m. Use load cells as the second channel. |
| 8 | **Wave loads on a blinded curtain hit normally.** These exceed the 1 kPa design load once Hs > **0.28 m** (606 kN per bay at Hs 1.36). Along-channel waves (11° screen) are fine up to Hs 3 m. | **FAIL (normal)** / PASS (along channel) | Orient the screen so no open fetch faces it. Add an **operational stow rule** (roll up when channel Hs from the screen-normal sector exceeds ~0.3 m). The bloom season (Oct–Nov) is the calmest period. |
| 9 | **Blinding capacity.** A static, sweep-cleaned face (Vs ≈ 0.51 m/s) passes to ≈0.4–0.6 ind/m³ and fails at **≈0.8 ind/m³ (μ = 0.3) to 1.5 ind/m³ (μ = 0.1)**. Bells stop sliding at **Δp ≈ 184 Pa (μ = 0.3)**, below the 200 Pa trip, so runaway sticking happens before relief. | **MARGINAL** | State the capacity as "**0.3 ind/m³ design, ~0.6 tested in model, fails ~1 ind/m³**". Make μ (friction) a tank measurement. Above ~0.6 ind/m³, add a second line or a higher sweep (Vs ≥ 0.6 m/s). |
| 10 | **Pump-driven pipe option.** A pump trip with fast check-valve closure gives a 38–45 m down-surge, so the column separates at the breakwater crest. SDR26 or SDR33 collapses under vacuum. | **FAIL** | Use the **gravity line from the head tank** (rigid-column run-down ~105–113 s, which is 3–5× 2L/a, so no Joukowsky). Drop the pump. Use **SDR17**. |
| 11 | **The pipe floats.** Water-filled it has −0.21 kN/m submerged weight; air-filled −11.6 kN/m. Nearshore stability (3–4 m depth, Hs 1.36 / max current) needs **≈20.6 kN/m**, i.e. **~1.5 m³ of concrete per m (~3.6 t/m)**. | **MARGINAL** | **Trench and backfill the 0–3 km nearshore section** (standard outfall practice), with concrete collars offshore. Add air separation at the head tank. |
| 12 | **Gravity head at 5 km** (aged pipe, 13.5% bells) is 10.6 m, so the head tank is at 11.6 m, just over v3's 11 m. 3 m³/s needs ID ≥ 1.45 m. HGL at the breakwater crest is marginal at 3 km (+0.7 m at a +5 m crest; negative at +7 m). | **MARGINAL** | Set the tank at ≥12 m for 5 km, or keep bell fraction ≤5%. Route the pipe *through* the breakwater (sleeve), not over it. Use a 1.4–1.5 m ID if 3 m³/s lines are wanted. |
| 13 | **Screw lift above 5.9 m is unproven.** An 11 m single-stage screw at 30° is 24 m long, with ~87 t rotating (rotating-tube variant). | **MARGINAL / FAIL** | Use **two stages of ~5.5 m**, or one D 3 m screw (27 rpm, tip speed 3.8 m/s ≤ Red Bluff's 4.2 m/s) plus a gravity line at 3 km (lift ~8 m). Fit duty + standby screws. |
| 14 | **Materials.** 316L fails (PREN 25). 2205 is marginal in crevices at 35.8 °C. | FAIL / MARGINAL | Use **2507 super duplex** (CCT 64 °C, 28 K margin) or titanium for rails, seats, shafts and fasteners. Use 90/10 CuNi mesh only if electrically isolated: coupled to stainless steel or cathodic protection it loses its antifouling. |

What passes:
- sweep ratio (cot 11° = 5.1), sweep 0.51–0.67 m/s, entrance spacing ≤60 s, exposure 278 s (so the 0.10 m/s criterion is the right one);
- clean head loss (0.2–4.5 mm);
- deploy time (~1 min per bay; all bays in parallel ≪ 10 min);
- mesh strength at ≤1 kPa for 2205 woven wire;
- pile sizes (OD 0.6–1.0 m S355; normal piling);
- bell volume fraction ≤5% up to 0.3 ind/m³;
- screw D 3 m;
- pipe shear (bulk strain ~150 1/s);
- energy: **0.30–0.46 MW per unit = 0.02–0.03% of 1,400 MWe; 1.8 MW for 4 units = 0.033%**.

---

## 1. Tests

### T01 Screen sizing (`t01_screen_sizing.py`)
**Purpose.** Check area, length, lane width, sweep, bypass spacing and exposure against NMFS 2022 §8.5 across tide and flow.

**Method.** Continuity for an angled screen in a training-walled lane: L = W/sinθ, Va = U sinθ, Vs = U cosθ. Tide is ±1.15 m (2.3 m spring range).

**Numbers:**
- Area is 1,000 m² at 100 m³/s and 1,725 m² at 172.5 m³/s.
- v3 L = 143 m (7 m lane) gives Va 0.100 at MSL, 0.120 at LAT and 0.21 at max flow + LAT.
- Recommended L = 171 m (7 m) or 260 m (5 m), with W = 33 m or 50 m.
- Travel between entrances is 26–58 s ✓.
- Bay drop must be 9.7 m (7 m lane).

**Outputs:** `out/T01_sizing_table.csv`, `out/T01_Va_vs_tide.png`.

**Verdict:** PASS at the design point; FAIL at LAT and max flow; FAIL on drop height.

### T02 Head loss and trigger filtering (`t02_headloss_trigger.py`)
**Method.**
- Loss coefficients: Idelchik perforated plate and woven wire; Kirschmer wedge-wire.
- Blinding model: Δp = ζρ(Va/(1−b))²/2.
- A 6 h synthetic signal: spring tide, a 25% pump trip, JONSWAP waves (Hs 0.22/0.58/1.36) at mid-depth, and 3 Pa sensor noise. It is filtered with a 60 s mean and with a flow- and tide-compensated blockage index.

**Numbers:**
- Clean loss is 2.2 mm (perforated, f = 0.5) to 0.15 mm (woven wire, f = 0.81).
- 200 Pa is reached at 53–91% blockage, depending on mesh.
- Raw wave spikes reach 1.7 kPa (Hs 1.36, normal incidence). The 60 s filter brings the clean-screen signal down to ≤125 Pa.
- A wave-rectified bias remains (index 32–73% at high seas).

**Outputs:** `T02_dp_vs_blinding.png`, `T02_trigger_noise.png`.

**Design implication:** compensated index plus a wave-bias correction plus a wave inhibit (finding 7).

### T03 Blinding dynamics (`t03_blinding_dynamics.py`)
**Method.** A per-bay time-stepping model of one unit (14 × 10 m bays, 7 m, 100 m³/s, Vs 0.51 m/s, 3 h runs):
- arrivals follow the flow;
- coverage is random-sequential;
- bells slide by Coulomb friction against sweep drag;
- cycling and relief run as state machines.

**Configurations:**
- A/B: static, μ = 0.3 / 0.1;
- C/D: on-demand cycling, with release or with a trough;
- E: duplex curtain;
- F: v3's continuous 30% cycling;
- G: duplex with 4 bays cycling.

**Results** (coverage % / capture % / leak t/h / max pulse t):

| Density (ind/m³) | A static μ0.3 | F v3 as written | E duplex | G duplex + 4 bays |
|---|---|---|---|---|
| 0.1 | 5 / 100 / 0 / 0 PASS | 3 / 65 / 38 / 0 FAIL | 5 / 100 / 0 PASS | 5 / 100 / 0 PASS |
| 0.3 | 14 / 100 / 0 / 0 PASS | 8 / 64 / 116 FAIL | 14 / 99 / 2 PASS | 13 / 98 / 6 PASS |
| 1.0 | 40 / 77 / 244 / 2.1 FAIL | 23 / 61 / 417 FAIL | 41 / 77 / 236 / 2.2 FAIL | 41 / 80 / 208 / 2.4 FAIL |
| 2.0 | 57 / 60 / 850 / 2.3 FAIL | 41 / 58 / 913 FAIL | 56 / 60 / 861 FAIL | 52 / 62 / 816 FAIL |

**Failure density** (first FAIL): A 0.79, B 1.5, C/D 1.5 (but these leak 12–17% from 0.3 ind/m³ up), E 0.79, G 1.1 ind/m³.

**Sticking threshold:** 184 Pa (μ = 0.3) and 553 Pa (μ = 0.1).

**Outputs:** `T03_density_table.csv`, `T03_failure_density.png`, `T03_timeseries.png`.

**Caveat:** friction, protrusion and drag coefficient are assumptions, so this is a ranking tool. The tank must measure μ and slide speed.

### T04 Structural loads (`t04_structural_loads.py`)
**Bay load** (10 m × 8.15 m wetted):

| Condition | Load per bay |
|---|---|
| Clean | 1.8 kN |
| 50% blinded | 7.3 kN |
| 90% blinded | 183 kN |
| 200 Pa trip | 16 kN |
| 1 kPa trip | 82 kN |
| Relief fails, 0.5 m drawdown | 410 kN |

**Mesh** (membrane, 5% sag):
- 2205 woven wire 2 mm/20 mm: SF 24 at 200 Pa, 4.8 at 1 kPa, 2.1 at 90% blinded, 0.95 at 0.5 m drawdown (FAIL).
- CuNi and UHMWPE net: SF ~1 at 90% blinded.

So mesh tearing is the backstop if relief fails, which is consistent with the Hanul 2021 net tear. Relief has to work.

**Bottom bar:** see finding 4.

**Drum** (r 0.4 m, 0.15 m/s):

| Condition | Torque | Motor |
|---|---|---|
| Clean | 8.6 kN·m | 3.8 kW |
| 200 Pa | 23.5 kN·m | 10 kW |
| 1 kPa | 91 kN·m | 40 kW |
| 90% blinded | 195 kN·m | 86 kW |

Rate the brake and gearbox for at least the 1 kPa case.

**Waves on the curtain:** see finding 8.

**Piles** (Morison, API RP 2A rough: Cd 1.05, Cm 1.2; lane current 0.6 m/s):
- D 1 m pile: 7 kN at operating waves, 15 kN at Hmax 2.45, 63 kN in a depth-limited storm (H = 6.4 m, T 7).
- Wind per bay (Cf 2, 30 m²): 14 / 53 / 74 kN at 19.6 / 38 / 45 m/s. The Dubai basic gust is 38 m/s (formerly 45); the Abu Dhabi Western Region value was not found.
- Pile OD needed (S355, D/t 40, fixity 5D, WSD): **0.6–1.0 m**, governed by "relief fails + 0.5 m drawdown".

**Training wall:** 8 / 25 / 82 kN/m for 0.1 / 0.3 / 1.0 m head difference between lanes.

**Seismic (illustrative):** Westergaard hydrodynamic force is 39 kN/m at 0.1 g and 117 kN/m at 0.3 g. That is larger than the curtain's operating load, so seismic loading (Cat II/I, no collapse onto safety equipment) governs the gantry and training walls. The site SSE is not public; the APR1400 standard design uses 0.3 g.

**Output:** `T04_bay_loads.png`.

### T05 Roll-up pulse (`t05_rollup_pulse.py`)
**Method.** N = −ln(1−φ)·A/a_b, with 3 kg per bell.

**Routine roll-up** (10 m bay): 0.09 / 0.30 / 0.98 / 1.6 t at 0.1 / 0.3 / 1 / 2 ind/m³.

**At trip:**

| Trip setpoint | 10 m bay | 5 m bay | 3 m bay |
|---|---|---|---|
| 100 Pa | 1.4 t | 0.7 t | 0.4 t |
| 200 Pa | 2.1 t | 1.04 t | 0.62 t |
| 500 Pa | 3.0 t | 1.5 t | 0.9 t |

The widest bay that keeps the pulse under 1 t at 200 Pa is **4.8 m**.

**Output:** `T05_pulse.png`.

**Verdict:** the v3 "<1 t" claim FAILS with 10 m bays.

### T06 Bypass hydraulics (`t06_bypass.py`)
- Entrance velocity needed is 0.58 m/s (1.1 × U), or 0.97–1.2 m/s at max flow.
- Required bypass flow is 9.3 m³/s (0.46 m slots) or 18.1 m³/s (0.9 m), up to 31 m³/s in the worst case.
- The collector is 0.9 m wide for 2 m³/s, or 6 m wide × 3 m deep for 18 m³/s at 1 m/s (no deceleration).
- Bell volume fraction in 2 m³/s: 1.35% / 4.1% / 13.5% / 27% at 0.1 / 0.3 / 1 / 2 ind/m³, so the lift line saturates above ~0.35 ind/m³. Add a line or dewater less.

**Output:** `T06_bypass_table.csv`.

### T07 Archimedes screw (`t07_archimedes_screw.py`)
**Method:**
- Nagel speed limit n ≤ 50/D^(2/3) (via Rorres 2000).
- Throughput calibrated on Red Bluff (3.05 m, 26.5 rpm, 2.45 m³/s; k = 0.196).
- Tip speed capped at 4.2 m/s (Red Bluff trout, ~100% survival).

**Numbers:**
- D 3.0 m at 27 rpm gives 2.1 m³/s (one duty screw), a tip speed of 3.8 m/s and a 0.75 m flight depth (≥1.5 bell diameters).
- D 2.5 m needs 2 screws and has a 0.63 m flight depth (marginal).
- Power at 2 m³/s: 134–144 kW (5 m lift), 188–201 kW (7 m), 295–316 kW (11 m).
- An 11 m single stage is beyond Red Bluff's proven 5.9 m.

**Outputs:** `T07_screw_table.csv`, `T07_screw_envelope.png`.

### T08 Pipe (`t08_pipe.py`)
**Friction head** (Colebrook, 1.2 m ID, SDR17 so OD 1.36 m; 2 m³/s, v 1.77 m/s):
- 3 km: 5.2 m new pipe, clean water; 6.8 m aged with 13.5% bells (Thomas viscosity).
- 5 km: 8.0 m and 10.6 m respectively.
- v3's 195 / 286 kW are conservative: 139 kW at 3 km with η 0.75 and a new pipe.

**Flow, speed and shear:**
- 3 m³/s exceeds 11 m (15–23 m head), so it needs ID ≥ 1.45 m.
- Transit time is 28 min (3 km) or 47 min (5 km).
- Deposit-limit ratio is 2–4 at 2 m³/s (PASS). At 1 m³/s it is 1.0 if damaged bells are heavy (s−1 = 0.02, from Lebrato 2013 sinking of 500–1,600 m/day).
- Bell-to-pipe ratio is 0.375 (marginal plug risk).
- Bulk strain rate is 152 1/s; wall shear is 4.8 Pa.

**Surge and collapse:**
- Joukowsky: a = 168–251 m/s; ΔH 30–45 m. Within PE100 occasional-surge limits for overpressure, but the down-surge causes column separation (finding 10).
- Ring buckling: SDR17 4.3 bar (short-term) or 1.2 bar (creep); SDR26 1.1 / 0.3 bar (FAIL).

**Stability and thermal:**
- Stability: see finding 11. Offshore at 7–9 m: 5.7–10.3 kN/m (PASS); the depth-limited storm needs 23 kN/m.
- Free thermal change is 9.5 m (3 km) or 15.8 m (5 km) for 15.8 K, so anchor blocks are needed at the breakwater.
- Restrained stress is ≤6.4 MPa (≤8 MPa allowable).

**Outputs:** `T08_pipe_table.csv`, `T08_stability.csv`, `T08_pipe_power.png`.

### T09 Energy (`t09_energy.py`)
Per unit, the load is the screw (gravity tank), plus dewatering return, drums at 30% duty, extra plant cooling-water pumping and controls:
- **301–349 kW (3 km)**;
- **380–457 kW (5 km)**.

That is 0.022–0.033% of 1,400 MWe. Four units in the worst case draw **1.83 MW (0.033% of 5,600 MWe)**. A 60-day season for 4 units uses ≈2.6 GWh, about 8% of one avoided unit-day (32 GWh).

**Verdict:** PASS.

### T10 Materials (`t10_materials.py`)
**Corrosion resistance (PREN / crevice data):**
- 316L: PREN 24.7, FAIL.
- 2205: PREN 35.4, MARGINAL (no seawater crevice-temperature value found).
- 2507: PREN 42.7, crevice temperature 64 °C (Alleima, natural seawater), so a 28 K margin: PASS.
- 6Mo: PREN 43.3, crevice temperature 61 °C: PASS.

**Selection:**
- Rails, seats, shafts and fasteners: 2507 or titanium Gr2, with GRP or UHMWPE rail liners.
- Mesh: 2205/2507 woven wire or UHMWPE. CuNi only if isolated.
- Piles: S355 with coating, cathodic protection and a splash-zone allowance.
- Pipe: PE100 SDR17, UV-stabilised; derated per ISO 13761 above 20 °C (table not retrieved).

**Fouling:** ≤60 days of deployment is fine with brush passes. Rails need a pre-season brush pig.

**Output:** `T10_materials.csv`.

---

## 2. Sources
- NMFS (2022) West Coast Region Anadromous Salmonid Passage Design Manual §8.5–8.6: https://repository.library.noaa.gov/view/noaa/43053 (read via `15_jazr_gate_precedents.md`)
- Rorres (2000), J. Hydraul. Eng., citing Nagel (1968) speed limit: https://math.nyu.edu/Archimedes/Screw/optimal/screw.pdf
- Red Bluff RPP and USBR Tracy vol. 25 (screw survival): see `15_jazr_gate_precedents.md` [22], [23]
- Fish strike-speed literature (~5 m/s "safe" for trout): Watson et al. 2020, doi:10.1080/24705357.2020.1768166 (reported via search)
- Alleima SAF 2507 datasheet (CCT 64 °C natural seawater): https://www.alleima.com/en/technical-center/material-datasheets/tube-and-pipe-seamless/saf-2507/
- L.J. Star, 2205 vs 316L: https://www.ljstar.com/wp-content/uploads/2019/11/duplex-2205-over-316L.pdf
- PE100+ / ISO 13761:2017 temperature de-rating: https://www.pe100plus.com/PE-Pipes/Technical-guidance/model/Design/Lifetime/factors-i243.html
- Dubai design wind speed (45 → 38 m/s): https://gulfconstructiononline.com/Article/6032/BMT_to_provide_advice_on_design_wind_speed_changes
- Lebrato et al. 2013, jelly-fall sinking 500–1,600 m/day: https://www.geomar.de/en/news/article/fast-sinking-jellyfish-could-boost-the-oceans-uptake-of-carbon-dioxide
- Standard references, not web-verified tonight:
  - Idelchik, *Handbook of Hydraulic Resistance*;
  - Kirschmer bar-rack formula;
  - API RP 2A-WSD Morison coefficients;
  - DNV-RP-F109 / RP-E305 on-bottom stability;
  - Thomas (1965) suspension viscosity;
  - Durand deposit velocity;
  - Westergaard (1933);
  - NORSOK M-001 PREN ≥ 40 rule;
  - Neitzel et al. (PNNL) fish shear threshold.
