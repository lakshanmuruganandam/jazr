# JAZR v5: final design (locked)
### *"The world has the warning. JAZR is the response: one button, no boats, every live animal released alive, where the sea won't bring it back."*
*Status: FINAL design for the 11 Oct 2026 submission. Built from 11 test streams in `TESTS/` (≈600 computational checks, 112+ automated tests) + real Gulf data + biology literature. **Everything is model-based or literature-based. No physical prototype exists yet.** Species: Blue Blubber jellyfish, *Catostylus* sp. (Gulf records mostly *C. perezi*); Oct–Nov bells 6.5–12 cm, mean 0.33 kg.*

---

## 1. The system in one picture
```
ALERT (ENEC early warning) → Bloom Incident OS → auto-deploy (operator veto) in ~10 min
 INTAKE BASIN · 4 training-walled lanes (one per unit, independent controls & power)
  ① MOVING-BELT ANGLED SCREEN (11°, ≈171 m/lane, bays ≤4.8 m): the mesh belt runs ALONG the face toward the apex
     at 0.5–1.0× sweep → pinned bells ride it, nothing sticks. Silicone non-stick coating. Stored raised and dry out of season.
  ② APEX ENTRANCE (mandatory) + flared intermediate entrances: draw 15–20% of lane flow; velocity always increasing, no dead zones
  ③ FLAT-PLATE DEWATERING: returns surplus water to the lane; bells ride over a smooth plate (no wedge-wire edges)
  ④ TURTLE-EXCLUDER GRID (~15 cm bars): small bells pass; turtles AND large bells (≤1.7 kg) slide alive to an open escape chute
     (camera + sonar 2-of-3 backup → lock hold)
  ②b LAYER 2 (second level): HYDRO-JET CURTAIN, no air — low-velocity floor/wall jets lift any leaker to a SURFACE SKIMMER
     INTAKE on the lane wall, which feeds the same collector. Bubble curtain rejected: air under the bell kills jellyfish (AZA)
  ⑤ HYDROLIFT (water-only float chambers) (2–3 open chambers ~6×6 m): animals float up with the water; nothing touches them; only screened water is pumped
  ⑥ HEAD TANK → gravity pipe, 1.6 m ID, NMFS bypass-pipe rules (R/D ≥5, no valves, no free fall, always full, never sub-atmospheric),
     through the breakwater, trenched. OXYGEN DISSOLVED in a side-stream (no bubbles), dosed by biomass
  ⑦ OUTLETS chosen by the 10-day drift forecast: NEAR (5 km offshore) or FAR (~10 km alongshore down-drift, away from Ruwais,
     other intakes, reefs and beaches). Submerged diffuser ≤1 m/s; temperature and salinity matched
 PLANT'S OWN SCREENS: untouched. Passive shear-pin relief + staged powered relief → any failure = today's plant, never worse
 CONTROL: Bloom Incident OS · twin + ML forecast · edge-AI camera counts (advisory closed loop) · hard-wired interlocks · air gap
```

## 2. Why each element is there (test → decision)
| Element | Decided by |
|---|---|
| Moving belt along the face (+ 35% entrance flow, half to the apex; baffles; light wall jet; low-friction mesh) | Virtual tank: v4.1 layout 0.77, + coating 0.85, **belt 1.00 in every case** (upper bound); precedent Bates 1970 (USFWS Leaflet 633): **97–100%** of juvenile salmonids diverted at up to 28 m³/s (10_mechanisms) |
| Apex entrance + 15–20% entrance flow | CFD: apex entrance → 100% reach an entrance (2D) vs 0–74% without (03); virtual tank 3% → 0.30, 20% → 0.73 (07); entrances need 9–18 m³/s (02) |
| Flat-plate dewatering, HydroLift, no air, dissolved O₂ | Screw blade contact 13–24% per pass for real bell sizes; bubbles under the bell kill (AZA manual); 3 h at 1 bell/m³ uses ≈3.2 mg/L O₂ (09, 10) |
| Excluder grid | Camera only = kill in the virtual tank (07); 1 camera ≈85% detection (04); real Gulf bells are 6.5–12 cm (00) |
| Gravity pipe through the breakwater, trenched | Pump trip pulls a vacuum at the crest; the pipe floats in shallow water (02) |
| Near/Far live release, no killing | Typical onshore drift is 2.5 cm/s (00): near-only gives 50% in a 10-day bloom; **far alongshore gives 10–13%, equal to a lethal option** (twin v5_far, v5_noharm) |
| Bays ≤4.8 m, low-tide sizing, shear-pin relief, compensated blockage index, 2-of-3 voting, staggered slots + hard-wired interlock | 02, 04, 08 (pulse 2.1 t at 10 m; 0.22 m/s at low tide; comms-loss pulse; motor-only fail-open fails) |
| Titanium / Cu-Ni / polymer wetted parts; cooled electronics | 02, 08 (duplex fails at 36–39 °C) |
| Auto-deploy with veto | 04 (late alerts: 5% in time with two approvals vs 59% auto) |
| Outer guide line → **dropped** (research option only) | CFD: 0–14% with turtle gaps (03) |
| No light guidance; dark at night | No phototaxis evidence; Blue Blubber carries no zooxanthellae (09) |
| Polyp mitigation: dry storage, no overhangs, settlement plates | Floating pier in Japan raised ephyra output 4.3× (09) |

## 3. Performance (model-based, honest)
**Guidance (TESTS/11, 30 seeds).** The best combination adds 35% entrance flow with dewatering (half to the apex), the moving belt at ≥0.25–0.5× sweep, flared mouths, graded baffles, a light wall jet and a low-friction mesh. Result: **900/900 bells guided, η_r = 1.000 (95% lower bound 0.996)**, against 0.773 for the v4.1 layout.
- It held under every stress case: rheotactic 10 cm/s swimmers, μ 0.4, a fouled bay, 1/m³, and **a stopped belt** (the other levers alone stack 0.82 → 0.97 → 0.992).
- Neither model has 3-D leak paths (seals, bay joints), so **we claim η_r ≈ 0.95–0.99 for design** and let the tank decide.

**Share of the swarm reaching the plant screens (twin, far release, typical drift 2.5 cm/s; 72 h / 240 h):**

| Configuration | 72 h | 240 h |
|---|---|---|
| Today | 97% | 100% |
| v4.1 layout (η_r ≈ 0.77) | 22.4% | 23.5% |
| Two screens in series | 4.9% | 5.1% |
| η_r = 0.99 | 1.1% | 1.15% |
| **v5 best combination (η_r lower bound 0.996)** | **0.36%** | **0.39%** |
| v5 + Layer 2 hydro-jet curtain (η2 0.5–0.9, illustrative, untested), with the simulated best η1 | ≈0.04–0.18% | ≈0.04–0.2% |
| Conservative design case: η1 0.97 + Layer 2 η2 0.7 (used in the dashboard) | ≈0.9% | ≈0.9% |

**Real-current hindcast:** 292 alert windows, Today 71% vs v3 6.2%. The ordering holds in 99% of windows.

**End-to-end survival of guided animals.** Two independent estimates disagree, and we show both:
- **Engineering budget (TESTS/10):** ≈ **0.978** (plausible 0.87–0.99).
- **Conservative Monte Carlo from literature analogues (TESTS/11):** HydroLift + dissolved O₂ **0.76 (5–95%: 0.68–0.85)**; screw + O₂ 0.74; without O₂ only 0.40–0.56.
- Both agree that dewatering and the 3 h pipe dominate the uncertainty, and that **O₂ control is essential**.
- **Design target ≥0.95.** The decisive experiment is a 3 h recirculating pipe loop with 96 h scoring. If it misses the target, the fallback is a shorter near route (when the forecast allows) and a longer, gentler dewatering ramp.

**Other results:** crew-hours −60% to −90% per bloom · energy ≈0.03% of plant output · structure, 60-year fatigue and 0.3 g seismic pass · control logic deadlock-free (26,633 states) · alarms ≈1/h. The AI closed loop adds value mainly as a backup (η_r 0.81 vs 0.76 if the belt fails).

**Release alive is the main path:** every guided live animal is released, and dead-on-arrival animals are a small secondary stream.

## 4. No-harm charter (non-negotiable)
No live animal killed · no nets · no acoustics · no electric fields · no bubbles in the animal path · O₂ 75–99% saturation, no supersaturation · temperature and salinity matched at release · turtles and large bells always have an air-reachable exit · outlets away from reefs, beaches and other intakes · dead-on-arrival animals only go to beneficial reuse · fish in the bypass released alive with the jellyfish.

## 5. AI (advisory, inside nuclear rules)
Edge-AI camera counts + closed-loop tuning suggestions (operator accepts) · Bayesian design optimisation of the apex/baffles · camera+sonar turtle backup · fast ML drift-forecast ensembles · predictive maintenance · operator copilot. **AI never takes a safety action; hard-wired interlocks are independent; air-gapped per FANR-REG-08 / IEC 62443.**

## 6. Practical path and economics
- **JAZR Core first:** OS + twin + forecast + **one-lane pilot**, with release by the shorter route first. This cuts the downside about 4×.
- **Expand** only if pilot data + ENEC's event records clear the **break-even ≈0.9 unit-days per unit-year**. Payback probability ≈87% at Hanul's historical rate, ≈99.9% at Gravelines' recent rate.
- Cost order: AED 30–80 M per unit (bottom-up higher, ~USD 51 M); the far pipe is the largest single item.
- **Regulatory:** FANR/Nawah modification review + seismic + cyber; **EAD permit amendment for live release (highest risk)**; marine-works permit; no autonomous craft.

## 7. What only real tests can settle
η_r of the moving belt at scale · live-animal survival through the lock and pipe (96 h) · excluder with real turtles · drift-back at sea (drifters) · Gulf depth distribution, O₂ and heat limits · the plant's event rate.
