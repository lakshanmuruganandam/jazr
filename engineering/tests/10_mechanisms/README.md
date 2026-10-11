# 10 · Mechanisms to raise η_r toward 0.99 and survival toward 99% (JAZR v4.1)

*11 Oct 2026. This is a literature, patent and calculation review, plus a small virtual-tank scan. **Nothing here is a physical test.***

**Tags used throughout:**
- **VERIFIED**: I read the primary text.
- **REPORTED**: the number comes from an abstract or secondary page.
- **CALC**: my arithmetic.
- **SIMULATED**: from the virtual tank.
- **ESTIMATE**: engineering judgement, not data.

| File | What it is |
|---|---|
| `mechanisms.csv` | 26 mechanisms (11 guidance, 11 survival, 4 AI support). Each row gives how it works, precedent and source, evidence status, expected effect, harm risks, cost, TRL, how to test, and a verdict |
| `survival_budget.csv` | Stage-by-stage survival: target and plausible range |
| `sim/mech_vtank.py` | Adds a **moving-belt** option to `../07_virtual_tank/vtank.py` (one patched line: friction acts on the bell's velocity *relative to the belt*), then scans belt speed, coating μ, agitation, bypass and bell size |
| `results/sim_mechanisms.json`, `results/sim_mechanisms_runs.csv` | Scan output (SIMULATED; 4 seeds × 30 bells × 150 s). To re-run: `python3 sim/mech_vtank.py` (~25 s) |

---

## 1. Bottom line
**Guidance.** The leak is set by bells that **stall on the face and at the mouth**, not by bells going through the mesh. In every virtual-tank run, 0 bells reached the intake; the bells that were not guided were stuck. A screen whose **belt moves along the face toward the apex** removes the stall mechanism directly. It has a real precedent: Bates (1970), USFWS Fishery Leaflet 633 (VERIFIED). That design was a vertically hung endless belt travelling horizontally. It diverted 97–100% of juvenile steelhead and coho, and it was scaled to 28 m³/s at up to 0.9 m/s. Its stated advantage was that the "travel of the screen can be matched to the velocity of the water" and that non-swimming eggs "can be ... safely carried ... into the bypass".

| Virtual tank (SIMULATED, 11°, 4–6 cm bells) | η_r | stuck |
|---|---|---|
| Baseline, 10% bypass, 2 entrances | 0.42 | 0.51 |
| v4.1 layout: 4 entrances, 20% bypass | 0.77 | 0.23 |
| Static mesh with low-friction coating, μ 0.4 → 0.05 (v4 layout) | 0.85 | 0.15 |
| Agitation 10 → 25% (a crude proxy for wall jets) | 0.53 | 0.20 |
| **Belt along the face at 0.25–1.2 × sweep** (any layout; also with μ = 1.0 + 3 Pa adhesion, with only 3% bypass, and at 15°) | **1.00** | 0.00 |

The 1.00 values are an **upper bound**, for three reasons:
1. The model is 2.5-D.
2. The model belt runs right into the entrance pocket.
3. It has no end-turn gap, no under/over leakage and no seal gaps.

**Prototype ESTIMATE:** face guidance of **0.95–0.99**. The remaining losses are at the belt end-turn hand-off, the bottom/top seals and through extrusion.

**Survival.** The two weakest links in v4.1 are the screw (blade contact) and the 3 h pipe. The best chain:
- **removes every moving part from the animal path**, using a water-only hydraulic fish lock instead of screws;
- dewaters over a **horizontal flat plate** (bells ride over it; they are not pressed onto edges);
- runs the pipe under NMFS bypass-conduit rules with **bubble-free side-stream oxygenation**;
- releases through a submerged low-velocity diffuser.

## 2. Recommended combination for η_r (ranked)
1. **Conveyor belt screen along the face** at 0.5–1.0 × sweep (G1). It replaces v4's belt bays (same cassettes, belt turned 90°). Build it as 3–4 belt segments, each ending at an entrance with a smooth hand-off lip and gaps ≤1.75 mm. The belt must fail to a *static meshed* state, never to an opening.
2. **Keep v4's apex entrance, 4 entrances and 20% entrance flow**, with flared mouths at least 4–5 bell diameters wide (G2). Real bells are 6.5–12 cm and the mouths 0.46–0.9 m, so mouth arching should be far rarer than in the 4–6 cm tank (ESTIMATE).
3. **Silicone foul-release coating on the belt or mesh** (G4). It costs little, and it is the fallback if the belt is stopped: on a static face it raised η_r by about 0.08 in the scan. **No oil-infused SLIPS**: lubricant would leach into a protected site.
4. **Self-learning screen in advisory mode** (G9): edge cameras count bells at each entrance and in a leak-zone window, and a safe Bayesian optimiser tunes the entrance-flow split and belt speed inside hard limits. The main value is a **continuous measurement of η_r**.
5. **Conditional:** a short second catch screen (G3), added only if the pilot measures η_r < 0.95.
6. **Optional plant modification:** a Ristroph-type live return at the plant's own screens (G11), for leakers.
7. **Rejected:**
   - light guidance: no evidence for *Catostylus*, and bells cannot out-swim the flow;
   - surface-only entrances: no measured depth data yet, so this is research only.

**Expected η_r (ESTIMATE):**
- Items 1–4: **0.95–0.99**, i.e. a leak of 1–5%.
- With item 5: **0.97–0.995**. This is less than the product of the two screens, because their failures are correlated.
- v4.1 today: 0.73–0.82 (virtual tank).

**0.99 is reachable on paper but unproven.** It depends on the belt end-turn and the seals, which only a tank can show.

## 3. Recommended survival chain and budget (all ESTIMATES)
| # | Stage | Target | Plausible |
|---|---|---|---|
| 1 | Belt screen face (no relative shear) | 0.998 | 0.990–0.999 |
| 2 | Entrance and flared transition (≤0.2 ft/s per ft, NMFS 8.6.2.8) | 0.999 | 0.995–1.000 |
| 3 | Horizontal flat-plate dewatering (≥0.3 m depth, sweep ≥20 × approach) | 0.997 | 0.985–0.999 |
| 4 | Turtle excluder, round bars at 30–55° | 0.998 | 0.990–0.999 |
| 5 | **Water-only fish lock** | 0.998 | 0.990–0.999 |
| 6 | Head tank and down-leg (no free fall, no air) | 0.999 | 0.995–1.000 |
| 7 | 10.5 km gravity pipe, 2.9 h, O₂ held | 0.995 | 0.970–0.998 |
| 8 | Submerged diffuser (≤1 m/s) | 0.999 | 0.995–1.000 |
| 9 | Delayed mortality, 24–96 h | 0.995 | 0.950–0.998 |
| | **End-to-end (CALC product)** | **0.978** | **0.87–0.99** |
| | Same chain with the v4 two-stage screw (stage 5 = 0.96, range 0.85–0.99) | 0.941 | 0.74–0.98 |

**Reaching 99% end to end** needs stages 7 and 9 at ≥0.998. **No data exist for gelatinous animals in either stage**, so the honest design target is about 98% with 99% as a stretch. The pipe loop test and the 96 h holding test decide it.

## 4. Key engineering numbers (CALC, from the project values)
**Pipe.** Q = 2 m³/s with a 1.6 m inside diameter gives:
- v = 0.99 m/s;
- transit 2.9 h over 10.5 km;
- dissipation of about 0.004 W/kg, so a Kolmogorov strain of about 60 s⁻¹ and eddies of about 130 µm, far smaller than a bell.

Against NMFS 2022 §8.6.3 (VERIFIED):
- **Velocity** is above the 2 ft/s minimum but below the 6–12 ft/s preferred band. That band exists to stop sediment, so the fix is pipe access and flushing ports, not more speed.
- **Bends** need R/D ≥ 5, i.e. R ≥ 8 m.
- **Mitred joints** must be ≤15°.
- **Excluded from the bypass:** valves, hydraulic jumps, free fall and pumping.
- **Pressure** must stay at or above atmospheric (vented).

**Oxygen demand.** Using 0.05 mL O₂ h⁻¹ g⁻¹ (from 04) and 0.33 kg bells:

| Bloom density | DO drop over 3 h | If stressed (×2) |
|---|---|---|
| 0.1 /m³ | 0.32 mg/L | 0.64 mg/L |
| 0.3 /m³ | 0.96 mg/L | 1.9 mg/L |
| 1 /m³ | 3.2 mg/L | 6.4 mg/L, above the 5.56 mg/L saturation at 35.8 °C |

So oxygen is needed above about 0.3 /m³. Dissolve it in a **screened water-only side-stream** (Speece cone or U-tube) and blend it in, so **no bubble ever meets a bell** (Raskoff et al. 2003). Cap total dissolved gas at about 110% (BC guideline, REPORTED), and trim with DO probes along the line (Huon-style manifolds).

**Screw contact with real bells.** This uses the same model as 04, at 26.5 rpm with 3 flights. The contact probability is **0.13–0.24 per pass** for 6.5–12 cm bells, against 0.61–0.91 for the 30–45 cm bells assumed earlier. Across two stages, about 25–42% of bells are touched.

**Fish-lock sizing** (at 0.3 /m³):
- 27 bells/s, which is 5.2 m³ of bells per 10 min;
- at ≤5% bell volume fraction, about 104 m³ of water per cycle;
- so 2–3 alternating chambers of about 6 × 6 m, filled at about 0.5 m³/s with water-only pumps (about 50 kW).

The pipe's 2 m³/s is made up at the head tank from screened, oxygenated water, so the animals travel in a small water volume until they reach the pipe. Above about 1 /m³, add chambers.

**Dewatering area** for 16 m³/s of surplus water: 533 m² at 0.03 m/s, or 267 m² at 0.06 m/s. NMFS 8.8.4 requires:
- approach < 0.25 ft/s, or < 0.4 ft/s with cleaning;
- sweep ≥ 2.5 ft/s;
- ≥ 1 ft of depth over the end;
- an automatic open-bypass response on low level, because stranding on a horizontal plate is the known failure.

## 5. AI-enabled mechanisms (coordinator request)
**Grounding rules for every AI item:**
- It runs on-site on air-gapped edge compute (FANR-REG-08, IEC 62443), with no remote control.
- It may **propose or tune within hard limits** that the PLC checks.
- It may **never** take or block a safety action. Hard-wired interlocks (excluder, screw or lock stop, shear-pin relief) act independently of it.

| Rank | Item | Precedent | Gain (ESTIMATE) | Main risk | Test | Verdict |
|---|---|---|---|---|---|---|
| 1 | Self-learning screen: camera counts at the entrances and leak zone, safe Bayesian optimisation of the flow split, belt speed and jet pulses | Jellytoring: jellyfish detection and counting F1 95.2% (PMC7146330). DeepMind/Google cooling: AI proposes, the local controller verifies, about 30% saving under operator supervision | +0.02–0.05 η_r; above all a **live η_r measurement** | Turbid-water miscounts | Webcam + YOLO in the T03 tank; optimiser wrapped around `mech_vtank.py` | Adopt (advisory first) |
| 2 | Bayesian/generative design of the apex scoop, baffle grading, angle and belt speed on a CFD surrogate | Bayesian optimisation + CFD for a Kaplan draft tube (Daniels 2021); under 90 CFD runs for up to 8 parameters (KTH) | +0.01–0.05; faster design | Over-fitting the 2-D model | BO on `03_cfd_flow`; check the top 3 designs in the tank | Adopt |
| 3 | Fused camera + sonar turtle/dolphin detector, as **backup** to the grid | Turtle YOLO P/R ≈ 0.85; sonar Bio-YOLOv7 at nuclear intakes P 0.85 / R 0.83 (REPORTED) | Protection reaches about 0.9997 only *with* the grid (04) | Night and turbid false negatives | 300 turtle-proxy trials | Adopt (backup only) |
| 4 | ML drift surrogate with drifter assimilation | DriftNet; Drift Field Net, 7-day error ~60 km, ~20 km better than Mercator (REPORTED) | Larger, faster ensembles, fewer wrong-outlet releases; no change to 1−η_r | Extrapolating beyond its training data | Hindcast the 292 alert windows; pilot drifters | Adopt |
| 5 | Predictive maintenance from motor current and ΔP | Motor-current analysis detects conveyor mis-tracking and looseness (Sensors 2023) | Keeps belt MTBF above the 1,000–2,900 h that 04 requires | None (advisory) | Seeded-fault bench | Adopt |
| 6 | Operator copilot: alarm rationalisation, procedures drafted for approval | Argonne PRO-AID; KAERI LLM interface on an SMR simulator (REPORTED) | Faster close-alert handling | Hallucinated advice, so a human approves everything | Tabletop drills | Optional |

## 6. Overall ranking (both goals)
1. G1 conveyor belt screen
2. S1 water-only fish lock (S2 screw is the fallback)
3. S6 horizontal flat-plate dewatering
4. S7 + S8 + S11: NMFS pipe rules, bubble-free O₂, no air anywhere
5. G2 apex and 4 entrances (keep)
6. G9 AI closed loop and η_r metering
7. G4 silicone coating
8. S9 diffuser outlet and S10 round-bar excluder
9. G10 Bayesian design optimisation
10. A1 fused turtle detector (backup)
11. A2 drift surrogate and A3 predictive maintenance
12. G3 series catch screen (conditional)
13. G5 wall jets (unjam pulses only)
14. G6 graded baffles
15. G11 Ristroph retrofit (plant option)
16. A4 copilot
17. G7 surface entrance (research)

Rejected: G8 light, S3 Hidrostal (held in reserve only), S4 vacuum pump, S5 airlift.

## 7. Tests that decide it (add to `06_physical_protocols`)
1. **Belt-on-face tank test.** Drive a nylon-mesh loop on a chain along the T03 face at 0, 0.5 and 1.0 × sweep. Record η_r, stuck bells, and a video of the end-turn hand-off.
2. **Bell–mesh slide test.** Tilt bare, silicone-coated and belt mesh, and use real tissue where possible, to measure μ.
3. **Lock column.** Fill a 2 m acrylic column from below with bells inside, and score damage as in T09.
4. **Flat-plate dewatering tray.** Vary the depth; count stranding and edge damage.
5. **Pipe loop.** Run for 3 h at 1 m/s and 1–15 kg/m³, logging DO and TDG. Score bells at 0, 24 and 96 h. This is the decisive survival test.
6. **Edge-AI counting.** Run it on T03 video and report recall with a 95% confidence interval.

## 8. Limits and honesty
- The virtual tank scan uses 4–6 cm gel bells in a 6 cm mouth (a jamming-prone regime) and a 2.5-D flow. The belt result is an upper bound.
- No gelatinous-animal data were found for any lift, pump, dewatering screen or km-scale pipe. Every survival figure is an ESTIMATE built from fish analogues and physics.
- The Bates belt screen was never commercialised as far as I could find. Mechanical reliability of a long horizontal belt in warm seawater is the main engineering risk.
- the plant's own screen type is not public, so G11 is conditional.
- The NMFS criteria are for salmonids. Here they are used as a conservative design analogy, not as a compliance claim.

## Sources (main)
- Bates, D.W. (1970) *Diversion and Collection of Juvenile Fish with Traveling Screens*. USFWS BCF Fishery Leaflet 633. https://spo.nmfs.noaa.gov/sites/default/files/legacy-pdfs/leaflet633.pdf (text read)
- NMFS (2022) *Anadromous Salmonid Passage Design Manual*, §8.6.2–8.6.4 and §8.8. https://repository.library.noaa.gov/view/noaa/43053 (text read). NMFS (2008) §11.6.1.7 and §11.9.1. https://efotg.sc.egov.usda.gov/references/Public/ME/NMFS_2008_Fish_Screen_Criteria.pdf
- USGS horizontal flat-plate screen evaluations. https://pubs.usgs.gov/publication/70033099 ; Farmers Screen. https://farmerscreen.org/
- EPRI Modular Inclined Screen (OSTI 220108): >99% passage survival at ≤1.8 m/s, lab. https://www.osti.gov/biblio/220108
- Ristroph screens: EPA technology fact sheets. https://www.waterboards.ca.gov/rwqcb3/water_issues/programs/duke_energy/docs/usepa_technology_factsheets.pdf
- White et al. (2023), NAJFM 43(3), doi:10.1002/nafm.10901 (Hidrostal, eggs and larvae ≥99%)
- Matís, vacuum pump vs ValuePump. https://matis.is/en/?p=46851 ; Nofima. https://thefishsite.com/articles/vacuum-pumping-does-not-injure-salmon-1
- Huon 1 km smolt pipe. https://www.fishfarmingexpert.com/article/going-the-distance-smolts-successfully-transferred-to-boat-through-1km-pipe
- Speece cone. https://www.globalseafood.org/advocate/speece-cones-saturate-water-with-oxygen-ozone/ ; TDG guideline (BC). https://projects.eao.gov.bc.ca/api/document/595fb0973fdcd0001d9f46fa/fetch
- Scyphomedusa hypoxia, J Exp Biol 208:2475. https://cob.silverchair.com/jeb/article/208/13/2475/15656/Intragel-oxygen-promotes-hypoxia-tolerance-of
- Raskoff et al. (2003), Biol. Bull. 204:68–80. https://archive.org/download/biostor-11146/biostor-11146.pdf
- Coatings: PMC11643888 (superhydrophobic surfaces vs *Nemopilema* nematocysts); PMC11595577 (SLIPS stability)
- Fish lifts and locks. https://wetlandinfo.detsi.qld.gov.au/wetlands/management/fish-passage/technologies/fishway-options/mechanical/
- Light: https://scyphozoan.ucmerced.edu/wiki/Behavior ; Catostylus depth (estimate). https://www.sealifebase.ca/Summary/SpeciesSummary.php?id=44751
- AI:
  - Jellytoring. https://pmc.ncbi.nlm.nih.gov/articles/PMC7146330
  - DeepMind cooling. https://deepmind.google/blog/safety-first-ai-for-autonomous-data-centre-cooling-and-industrial-control/
  - Bio-YOLOv7 at intakes. https://mdpi-res.com/d_attachment/jmse/jmse-14-00347/article_deploy/jmse-14-00347.pdf
  - DriftNet. https://arxiv.org/abs/2211.09818 ; Drift Field Net. https://arxiv.org/pdf/2609.16288
  - Motor-current analysis on conveyors. https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10099345/
  - Argonne PRO-AID. https://www.power-eng.com/nuclear/how-generative-ai-could-help-nuclear-plant-operators/
- Project files: `../02_hydraulics_structures`, `../03_cfd_flow`, `../04_biology_wildlife_ops`, `../07_virtual_tank`, `../../../15_jazr_gate_precedents.md`
