# 09: Jellyfish biology and behaviour for JAZR (guidance + alive release)
*11 Oct 2026. This stream is a literature review plus one derived calculation (`o2_budget.py` → `o2_budget.csv`). No animals were tested. Species: Blue Blubber jellyfish, *Catostylus* sp. (Gulf records mostly *C. perezi*). Oct–Nov UAE bells 6.5–11.8 cm; Oman Sea mean 0.33 kg (range 0.18–1.7 kg) (see `00_data`).*

**Tags.** **[DERIVED]** = my calculation from cited numbers. **[INFERENCE]** = reasoning, not a published finding. **UNKNOWN** = no data found. "Analogue" = data from another species or another taxon (usually fish).

**Bottom line.**
1. **No behavioural lever is strong enough to steer the animals by itself.** Rhizostomes sense flow and swim against it, but at only ~4–15 cm/s. Guidance must stay **hydraulic**. Biology gives *constraints*: no dead zones, no shear layers to hold station in, velocities several times the swim speed, and entrances covering the surface layer and ideally full depth.
2. **For survival, the three hard rules are no air, no contact and enough oxygen.** Air and bubbles under the bell kill jellies (aquarium consensus). The pipe needs O₂ control once the jellyfish biomass exceeds **~6.6 kg/m³ over 3 h** (conservative case) **[DERIVED]**. Any O₂ added must be **fully dissolved, never as bubbles**, because supersaturation itself makes bubbles.
3. **The biggest unknowns** are rhizostome survival after pumping, lifting or piping (no published data for any scyphomedusa), and the Gulf species' depth distribution, thermal ceiling (CTmax), critical oxygen level (Pc) and shear tolerance.

Files: `README.md` (this file) · `biology_design_rules.csv` (20 rules, thresholds, confidence, sources, tank test) · `o2_budget.py` / `o2_budget.csv` (oxygen budget for the 3 h pipe).

---

## A. Behaviour that could be exploited for guidance

### A1. Swimming speed vs size
| Animal | Bell | Speed | Source |
|---|---|---|---|
| *C. mosaicus* (lab, 25 °C, 33 ppt) | 2.3–4.6 cm | **3.6 cm/s** (36.2 ± 1.2 mm/s), 2.18 Hz | Neil & Askew 2018 JEB (fact-checked in `05_fact_check.md`) |
| *Rhizostoma pulmo* (flume, 28–31 °C) | 10–20 cm | **8.7 cm/s** mean; 9.1 against a 4.5 cm/s flow, 7.7 with it; 1.22 Hz | Malul et al. 2019 Sci Rep 9:20337 (PMC6937341) |
| *Rhopilema nomadica* | 10–14 cm | **6.7 cm/s** mean; 8.25 against the flow, 4.4 with it | same |
| *Stomolophus meleagris* | up to ~25 cm | **up to 15 cm/s** continuous. Speed rises with wet weight up to 70 g, then levels off | Larson 1987 Can J Zool 65:2690 (abstract) |
| *C. mosaicus* adults, field | — | 43 mm/s, and ~80 mm/s attributed to Pitt & Kingsford 2000 | unverified secondary figure (agent_enec_science.md); **do not cite** |

**Reading [INFERENCE].** Gulf Oct–Nov bells (6.5–12 cm) probably swim at ~4–9 cm/s. That is 2–5× slower than the 0.22 m/s low-tide approach velocity and far slower than any entrance velocity. Animals cannot swim out of a well-designed flow field. They **can** hold station wherever local velocity drops below ~10 cm/s.

### A2. Rheotaxis / counter-current swimming
- *Rhizostoma octopus* orients to currents and **swims against the drift** (accelerometers on free-ranging animals). This keeps blooms together and reduces stranding. The mechanism is unknown: possibly shear sensing across the body, or magnetic or infrasound cues (Fossette et al. 2015 Curr Biol 25:342, abstract via Europe PMC).
- *R. pulmo* and *R. nomadica* swim faster against the flow than with it in currents up to 4.5 cm/s (the highest tested). Pulse rate does not change with flow, so the animals change **heading**, not effort (Malul 2019).
- **Effect on screen sweep [INFERENCE].** Along the 11° screen the sweep component is about 5× the approach velocity, ≫ swim speed, so rheotaxis barely changes the sweep. It matters in three places: (i) **low-velocity pockets** (behind baffles, lane corners, tide-low zones), where animals can hold station and accumulate; (ii) **entrance mouths** that are too gentle, where animals facing upstream can stall at the lip; (iii) the **dewatering stage**, where velocities fall. *Rule R10/R11:* no decelerating zones; velocity ≥ 3× swim speed everywhere on the guided path.
- *Evidence quality:* field (Fossette) and lab (Malul) on other rhizostomes. No *Catostylus* data. MEDIUM.
- *Non-harmful lever:* none to "use". The lever is **denying station-holding** through geometry.

### A3. Vertical distribution and vertical migration
- *C. mosaicus* "mostly within 1 m of the surface" (Lake Illawarra; Australian Museum). **The quality is weak.** The JCU record found is a biomass paper (Pitt & Kingsford 2003, Fish Res 63:303), and SeaLifeBase labels "<1 m" as an *estimate based on ecology*.
- Other rhizostomes use the whole water column. *R. octopus* averaged **619 m/day of vertical movement, >60× the water depth** (Hays et al. 2015, Proc R Soc B, abstract only). *Nemopilema nomurai* (0.8–1.6 m bells) ranged 0–176 m, with most mean depths <40 m and **deeper at night** (Honda et al. 2009 Fish Sci).
- Tidal vertical migration is documented in other scyphozoans. Wadden Sea medusae rise on the flood and descend on the ebb (Helgoland Mar Res, doi 10.1007/BF02367045). *Aurelia labiata* drops below the turbulent ebb stream to avoid being flushed (Albert 2007, J Sea Res). For *Catostylus*, sinking on the ebb is only a **hypothesis** (agent_enec_science.md row 2b).
- Medusae aggregate in **shear layers** at density discontinuities and hold position there by pulsing asymmetrically (*Aurelia*, lab shear 0.10–0.34 s⁻¹) (Rakow & Graham 2006 L&O 51:1097).
- Wind does not obviously push rhizostomes down. A Bora wind event **brought *R. pulmo* up** and concentrated them on the coast (Gulf of Trieste 2022, via search).
- **Design reading.** The surface layer probably holds most animals by day, but depth use can change with tide, time of day and turbulence. **Entrances should take the top 1–2 m preferentially and still span the full lane depth** (the 7 m lanes are shallow). A depth-selective (surface-only) entrance is **not** justified by current evidence.

### A4. Light
- *Catostylus mosaicus* is **non-zooxanthellate** (used as the non-symbiotic contrast to *Phyllorhiza punctata*; West et al. 2009 L&O 54:2058). Its blue colour is a rhizostome-specific UV-absorbing pigment ("rhizostomins", AMSA 2022 abstract), not symbiont-related. **So there is no reason to expect *Mastigias*-style sun-tracking.** (*Mastigias* in Palau migrates horizontally following the sun and avoids shadows to keep its zooxanthellae lit; Hamner & Hauri 1981 L&O 26:414.) Whether Gulf *C. perezi* has zooxanthellae is **UNKNOWN** but unlikely; a fluorescence check is cheap.
- Scyphozoan rhopalia carry ocelli plus a statocyst. In *Aurelia*, illumination **raises pulse rate**, and this is lost when the pigment-cup ocelli are removed (Horstmann 1934, via the 2009 developmental review PMC search result). Juvenile *Aurelia coerulea* spent more time in lit areas (2026 Behavioural Processes, search result only, not read).
- Image-forming vision with **visually guided obstacle avoidance** exists in box jellyfish (Garm et al. 2007 JEB 210:3616), **not in scyphozoans**.
- In the aquarium, light changes trigger spawning. After 24 h of darkness in shipping, planulae and gametes are found in bag water (AZA). *Nemopilema* oocytes mature on light exposure, with mass spawning 80–100 min later (search result).
- **Lever and risk [INFERENCE].** A light at the apex is as likely to *raise swimming activity* (more counter-current station-holding) as to attract. Lights also attract fish (the basis of light-fishing), which would raise bycatch. **Default: dark at night (R15).** Test before using.

### A5. Turbulence, shear, contact
- *Aurelia* senses shear of 0.1–0.34 s⁻¹ and holds position against it (Rakow & Graham 2006).
- AZA: flows that are "too high or too low" cause eversion, inversion ("balling"), abrasion, bell deformity and loss of oral arms. The husbandry mantra is "how low can you go". **No numeric damage threshold exists for any medusa** (searched; none found).
- Contact: scyphozoans have no visually guided avoidance, so contact with mesh is purely mechanical (hydraulics decide).
- No evidence was found that turbulence makes rhizostomes dive.

### A6. Sound, electric and magnetic fields
- Low-frequency sound **damages rhizostome statocysts**. A 50–400 Hz sweep at a received level of 157 ± 5 dB re 1 µPa (peaks to 175 dB) for 2 h caused hair-cell extrusion and loss in *Cotylorhiza tuberculata* and *R. pulmo*, worse at 96 h than at 48 h (Solé et al. 2016 Sci Rep 6:37979, full text PMC5175278). The no-effect level is UNKNOWN. **Rule R13:** no acoustic deterrents; measure screw and pipe noise.
- Electric fields: the only report is a trade-press claim that pulses neutralise *Apolemia* stingers at salmon farms (Harbor/Nofima). There is no peer-reviewed scyphozoan behavioural evidence, and the risk to turtles and fish is unassessed. Magnetic: Fossette lists magnetic cues only as a hypothesis. **Do not use (R14).**

### A7. Salinity and temperature gradients, chemical cues, aggregation
- *C. mosaicus* disappeared after **every one of ~16 major freshwater flows** in 20 years (Loveridge et al. 2021). Avoiding low salinity is real, but making a freshwater or brine "fence" would harm other marine life and is impractical. **Rejected.**
- Medusae are osmoconformers. A salinity mismatch changes buoyancy: positive at higher salinity, negative at lower (AZA acclimation notes).
- Chemical cues: no usable attractant or repellent known for rhizostomes (none found). Stressed jellies release **copious mucus** (AZA). In the bypass this means extra oxygen demand (BOD) and wedge-wire clogging, not a cue.
- Aggregation: blooms reach "hundreds to millions" kept together by current-oriented swimming (Fossette 2015). The Gulf of Kutch *C. perezi* reached >4 m⁻², max 9 m⁻², stranded (Behera et al. 2022 IJMS 51:536). Bubble plumes lift jellyfish to the surface (Lo 1996 lab), but **bubbles under the bell are lethal** (AZA), so bubbles are **excluded** anywhere animals are inside JAZR.

### A8. Sensory deep-dive (coordinator request): evidence → harmless lever → tank test
| # | Sense / cue | Evidence (quality) | Harmless design lever | Tank test (real Gulf animals, or surrogates: *Aurelia*/*Cassiopea* from aquaria; agar-gel bells for passive controls) |
|---|---|---|---|---|
| S1 | **Rhopalial ocelli, light / shadow** | Light raises *Aurelia* pulse rate (Horstmann 1934). Sun-tracking and shadow avoidance only in zooxanthellate *Mastigias* (Hamner & Hauri 1981). Visually guided avoidance only in cubozoans (Garm et al. 2007). *Catostylus* non-zooxanthellate (West et al. 2009). **No rhizostome phototaxis study found.** LOW | Candidates only: (a) keep screens and entrances **dark at night** (default); (b) test **dim red vs white LED** at the apex mouth to see whether activity rises or falls; (c) shading over the head tank (also a thermal benefit) | Two-arm choice flume (lit vs dark arm, flow 5 cm/s): proportion choosing each arm, pulse rate, n ≥ 30 per treatment; repeat day/night. Passive agar bells as the null (they must split 50/50) |
| S2 | **Statocyst / gravity; dive vs surface** | Tidal vertical migration in other scyphozoans (Wadden Sea; *A. labiata*). *Nemopilema* deeper at night. No turbulence-dive evidence. *Catostylus* depth evidence weak. LOW–MEDIUM | Entrances skim the surface preferentially but span full depth; size the apex entrance for the full water column | 3 m-deep column tank: depth histogram (camera) by light phase, with and without surface turbulence (wave paddle) and a 2 ppt halocline |
| S3 | **Rheotaxis** | Field + lab (Fossette 2015; Malul 2019). MEDIUM | Velocity ≥ 3× swim speed on the guided path; no eddies or dead zones; monotonic acceleration into the entrance (R10, R11) | Flume at 5, 10, 20, 30, 45 cm/s: % station-holding, heading vs flow, time-to-entrance at a model apex; compare with passive agar bells to isolate behaviour |
| S4 | **Mechanical / chemical**: shear sensing, contact, mucus | Shear 0.1–0.34 s⁻¹ is sensed and resisted (*Aurelia*, Rakow & Graham 2006). Stress mucus (AZA). No repellent known. LOW–MEDIUM | Smooth bellmouths; CFD-check entrance lips and baffles for persistent shear layers; plan wedge-wire cleaning for mucus | Map residence time around a 1:5 apex and baffle model with live animals; mucus mass and DO drop after 1–3 h of handling |
| S5 | **Noise, EMF (what to avoid)** | Statocyst trauma at 157 dB RL, 50–400 Hz, 2 h (Solé 2016). MEDIUM for harm; threshold UNKNOWN. EMF: no evidence | Low-rpm screws, resilient mounts, no acoustic or electric deterrents | Hydrophone at the screw and pipe; optional statocyst SEM after a 3 h exposure at measured JAZR noise vs controls |
| S6 | **Zooxanthellae** | *C. mosaicus* non-zooxanthellate (West et al. 2009). Gulf *C. perezi* UNKNOWN | If absent: no light lever, and **no light needed in transit** (3 h dark is fine). If present: avoid long dark holds | Chlorophyll fluorescence / microscopy of oral-arm tissue from 10 Gulf animals (1 day) |

---

## B. Physiology and handling tolerance (survival)

### B1. Mechanical damage, fragmentation, regeneration
- **No numeric shear, pressure or abrasion thresholds exist for medusae** (searched). AZA lists the effects of bad flow qualitatively and warns that even fine-mesh nets abrade tissue. Jellies "can be easily injured if lifted out of the water"; move them with bowls, not hands or nets.
- Fish analogues used only as a provisional ceiling: larval fish protected below 400–600 s⁻¹ strain (MF18116). Juvenile fish injury rises above ~495 s⁻¹ (search result). **Jellyfish: UNKNOWN.**
- Pressure: medusae are ~95–98% water with no gas spaces (Purcell 2010 discussion), so hydrostatic changes in a 6 m-head gravity line are unlikely to matter **[INFERENCE]**. The danger is **gas coming out of solution** (B2).
- Repair: young *Aurelia* close wounds within hours and **re-symmetrise** within 12 h to 4 days, but do not regrow arms. This was also seen in *Mastigias* and *Cotylorhiza* (Abrams, Goentoro et al. 2015 PNAS). Large-medusa regeneration: UNKNOWN. Fragments of some gelatinous taxa survive (EPRI), so **damaged animals are not "dead"**. Count them separately.

### B2. Air exposure and bubbles (AZA Jellyfish Care Manual, 3rd ed.)
- "Bubbles that become trapped in a jelly bell will work their way through it, causing serious damage and even death". Bubbles also make jellies float and clog screens and overflows.
- Air diffusers are prohibited in jelly systems. Supply lines must stay submerged and air-free. Use standpipes, Hartford loops and check valves so a power cut does not flush air in.
- **Supersaturation** (warm-up of cold water, air drawn in on a pump's suction side) produces micro-bubbles that end up under bells.
- After **any** air exposure, inspect bells for trapped air. Removing air from hundreds of jellies is impractical, so **prevention is the only option at JAZR scale**.
- **JAZR implications:**
  - The rotating-tube screws must lift water-filled pockets that never drain above the waterline, with submerged entry and exit.
  - The head tank must be fed below its surface.
  - The pipe must run **full-bore** (no partially-full gravity reaches, no hydraulic jumps).
  - O₂ must go in as a **pre-dissolved side-stream**, not a diffuser in the main flow.
  - Air-release valves must sit where vented gas cannot meet animals.
  - DO and total dissolved gas must stay ≤100% saturation at the outlet's pressure.

### B3. Oxygen for a 3 h, 10.5 km transit (`o2_budget.py`, `o2_budget.csv`) [DERIVED]
- **Respiration inputs.**
  - Purcell et al. 2010 scyphomedusan regression: RR (ml O₂ d⁻¹) = 83.37·(g C)^0.94, CV 72%. Temperature 7–30 °C was not significant. The authors call it *conservative* (an underestimate) for vigorous rhizostomes.
  - Carbon content for *Catostylus* is UNKNOWN. Rhizostome values are 0.34% WW (*R. pulmo*) to 0.6% WW (*N. nomurai*).
  - Active *Stomolophus*: **0.05 ml O₂ h⁻¹ g WW⁻¹ at 30 °C**; inactive is 50% less (Larson 1987).
  - Per 0.33 kg animal: **5.5–9.4 mg O₂/h (regression) to 23 mg O₂/h (active *Stomolophus*)**, i.e. **0.017–0.071 mg O₂ g⁻¹ h⁻¹**.
- **Saturation** at 34 °C and 42 ppt is **5.66 mg/L** (Garcia & Gordon 1992).

| Pipe density (animals/m³), 0.33 kg each | ΔDO in 3 h, low (regression) | ΔDO, high (active *Stomolophus*) | ΔDO, high ×2 (assumed handling stress) |
|---|---|---|---|
| 1 | 0.02 mg/L | 0.07 | 0.14 |
| 10 | 0.16 | 0.70 | 1.41 |
| 20 | 0.33 | 1.41 | 2.81 |
| 50 | 0.82 | **3.51** (DO ends at 38% sat) | **7.03 (anoxic)** |
| 50 animals of 1.7 kg | 3.85 | 18.1 | 36.2 |

- **Pipe density is not intake density.** One unit's 172.5 m³/s, guided at η = 0.9 into a 2.0 m³/s pipe (1.6 m ID at 1.0 m/s), concentrates animals ~78×. Intake 0.1 → **7.7/m³**, 0.3 → **23/m³**, 1 → **77/m³** in the pipe. So **1–50/m³ is the realistic pipe range, and 50+ is reachable** in a bloom.
- **Rule R04.** Without injection, keep wet biomass ≤ **~6.6 kg/m³** (≈20 animals/m³ at 0.33 kg) for a 3 h transit under the conservative rate. This holds DO ≥75% sat (AZA ideal range 75–99%). Above that, inject pre-dissolved O₂.
- **Example [DERIVED].** At 50/m³ × 0.33 kg the pipe holds ~1.06 million animals (pipe volume 21,100 m³), consuming roughly 6–25 kg O₂/h. That is an ordinary aquaculture oxygenation scale.
- **Floor.** Scyphomedusae (*Aurelia*, *Cyanea*, *Phacellophora*, *Chrysaora*) oxyregulate down to **<10% air saturation** (Thuesen et al. 2005 JEB 208:2475). The rhizostome critical oxygen level (Pc) is **UNKNOWN**. Fish bycatch in the same water sets the real floor: mean sublethal 2.61 mg/L and lethal 2.05 mg/L across taxa (Vaquer-Sunyer & Duarte 2008).
- **Add** BOD from stress mucus and dead tissue (UNKNOWN, measure). Ammonia excretion by non-zooxanthellate *C. mosaicus* is significant in mesocosms (West et al. 2009). Jellies tolerate ammonia better than fish (AZA), so **fish set the ammonia limit too**.

### B4. Thermal limits (32–36 °C)
- Field occurrence: UAE *Catostylus* is present year-round, with a temperature range of 20–35 °C (Aravind et al. 2023). the plant SST reaches 34.9 °C in August (Open-Meteo reproduction, `05_fact_check.md`). The animals already live near this ceiling.
- Rhizostome analogues:
  - *Cassiopea andromeda* medusae: **>34 °C lethal**, behaviour changes from 33 °C (Marine Biology Research 2022, doi 10.1080/17451000.2022.2066132).
  - *C. xamachana*: medusae erratic at 39 °C, lethal at 40 °C; larvae and polyps ~100% mortality at 36 °C (Oceans 2025, 6:6).
- AZA: tropical jellies 22–28 °C. Changes <5 °C per 24 h are tolerated in transport. Warm exposure is more stressful than cool.
- **Catostylus CTmax: UNKNOWN.**
- **Rules:** no heat added (head tank shaded, pipe trenched). Never take or release water in the plant's thermal discharge. Treat intake ambient >35 °C as a high-risk window for transit survival.

### B5. Osmotic and salinity tolerance
- Osmoconformers. Freshwater flows wiped out *C. mosaicus* medusae (Loveridge 2021). *C. perezi* also appears in low-salinity Shatt al-Arab and Hammar marsh waters (Iraqi reports, search), so tolerance may be wide.
- No numeric limits found: **UNKNOWN**.
- **Rules:** seawater-only screen wash. Release away from desalination brine and from freshwater. Post-transport salinity differences should be minimal (AZA acclimation: 20% water changes every 30–60 min when salinity differs).

### B6. Stress-induced spawning and planula release
- AZA: stressed jellies "produce copious amounts of slime, release gametes into the water". Planulae and gametes are found in shipping bags after 24 h of darkness.
- UAE *Catostylus* reproduces **year-round** (Aravind 2024 PhD, UAEU).
- Brooding in *C. mosaicus* (Pitt 2000) could not be confirmed at source (`05_fact_check.md` #12).
- **Assume every batch releases gametes and planulae.** Manage this through release siting (R17) and polyp-proof surfaces (R19). It is not avoidable.

### B7. Post-handling survival from fisheries and aquaria
- **Fisheries** (NSW *Catostylus*, Chinese *Rhopilema*) process animals dead. They give **no live-survival data**.
- *R. esculentum* stock enhancement releases large numbers into Liaodong Bay. Survival relates to cold years and release timing (Dong et al. 2018 IntechOpen). Transport-survival figures were not found.
- **Aquaria** (AZA manual, which lists *C. mosaicus* as a kept species):
  - Fast animals 24 h before transport.
  - Use bags with **no air pocket** and double-bag them.
  - Ship overnight (>24 h is routine).
  - Bag medusivores >7.5 cm individually.
  - Release only when animals are "belling nicely and evenly".
  - Kreisels use laminar, low, bubble-free flow.
  - Densities per bag: not given (UNKNOWN).
- **Gap:** no published survival for any scyphomedusa after pumping, screw lift or km-scale piping (`TESTS/04` and agent_enec_science.md). The fish lesson (Hudson angled screen: 90% initial survival, 35% at 96 h) means **delayed mortality must be measured (R20)**.

---

## C. Polyp and ephyra ecology near hard structures
- **Evidence that structures seed blooms.**
  - A new 48 × 6 m floating pier in Japan was colonised on its **undersurface** within ~4 months. Ephyra export rose **4.3-fold (5.7 → 25 million)** while a control port fell (Makabe et al. 2014 J Oceanogr 70:447).
  - Scyphozoan polyps "attach selectively to the overhanging surfaces" (same).
  - *Aurelia labiata* planulae and polyps **prefer plastics** (polystyrene, LDPE, HDPE) over rubber and treated wood (Hoover & Purcell 2009 Hydrobiologia 616:259). JAZR uses polymer belts, HDPE pipe and polymer wetted parts.
  - Duarte et al. 2013 (Front Ecol Environ 11:91) put forward the "ocean sprawl" hypothesis.
- ***Catostylus* polyps.** Settlement substrates were reported in Pitt 2000 (wood, sandstone, shell, glass, per secondary sources; not read). **Gulf *Catostylus* polyps have never been found: UNKNOWN.**
- **Specific JAZR risks [INFERENCE]:**
  - Shaded, permanently wet undersides: training-wall soffits, baffle backs, entrance hoods, head-tank and dewatering covers, the outlet diffuser.
  - The **dark pipe interior when idle**.
  - The **outlet**: released animals and planulae meet a hard structure there.
- **Mitigations (all non-lethal to other life):**
  1. Store screen cassettes **raised and dry** (already in v4). Drying is lethal to polyps but harms nothing else.
  2. Design out overhangs: vertical faces, open soffits, lit surfaces where possible.
  3. Use **non-biocidal fouling-release** (silicone) surfaces rather than copper paint. Copper harms other life, and one study found Cu at ambient levels did not stress *A. coerulea* early stages.
  4. Run a spring polyp inspection with **settlement plates of JAZR materials** at the plant for 6–12 months (cheap, decisive).
  5. Site the outlet over soft sediment and keep it free of overhangs.
  6. Flush the pipe with full-bore seawater during idle periods. **[INFERENCE]: flushing's effect on polyps is UNKNOWN.**
- **Honest tension.** Removing polyps (the Korean water-jet approach) kills jellyfish polyps. Under a strict no-harm brief, prefer **prevention by design and dry storage** over removal.

---

## D. Biology design rules (full table in `biology_design_rules.csv`)
| # | Rule | Threshold | Confidence |
|---|---|---|---|
| R01 | No air, no free bubbles in the animal path | zero; inspect after any air exposure | HIGH (qualitative) |
| R02 | O₂ only pre-dissolved; no supersaturation | DO 75–99% sat; TDG ≤100% at the lowest-pressure point | HIGH (that it matters) |
| R03 | DO floor through transit | ≥75% sat (~4.2 mg/L at 34 °C/42 ppt); never <2.6 mg/L (fish) | MEDIUM |
| R04 | Biomass cap without O₂ injection | ≤6.6 kg/m³ for 3 h (≈20/m³ at 0.33 kg) | MEDIUM |
| R05 | Size O₂ to *pipe* density | ≈78× intake density at η = 0.9 | MEDIUM |
| R06 | Transit time | ≤3 h acceptable only with R01–R04 and R08; survival curve UNKNOWN | LOW–MEDIUM |
| R07 | No contact: no nets, hands or mesh lifting | zero intended contacts | HIGH (qualitative) |
| R08 | No heating; avoid >35 °C; ΔT ≤1 °C target | *Catostylus* CTmax UNKNOWN | MEDIUM |
| R09 | Seawater-only wash; release away from brine and fresh water | ΔS target ≤1–2 ppt [INFERENCE] | MEDIUM / UNKNOWN |
| R10 | Velocity ≥3× swim speed, monotonic acceleration | ≥0.3–0.45 m/s on the guided path [INFERENCE]; acceleration ≤ fish-screen analogue | MEDIUM |
| R11 | No eddies, dead zones or persistent shear layers | avoid v < swim speed; avoid 0.1–0.34 s⁻¹ holding layers | MEDIUM |
| R12 | Strain rate in screws, pipe and fittings | UNKNOWN; provisional <400–600 s⁻¹ (fish analogue) | LOW |
| R13 | Noise well below 157 dB re 1 µPa (50–400 Hz); no acoustic deterrents | no-effect level UNKNOWN | MEDIUM |
| R14 | No electric or magnetic guidance | — | decision |
| R15 | Dark at night by default; light only after a tank test | — | LOW |
| R16 | Oversize bells (to 1.7 kg) must clear the 15 cm excluder to the escape chute | geometry | HIGH |
| R17 | Release at ambient T/S, submerged and gentle, over soft sediment, away from structures and plumes; dark or matched light | — | MEDIUM |
| R18 | Assume spawning in the system; no shaded hard overhangs | — | MEDIUM |
| R19 | Don't create polyp habitat (dry storage, no overhangs, fouling-release, plates) | — | MEDIUM |
| R20 | Measure 96 h delayed survival, not just initial | UNKNOWN today | HIGH (gap) |

---

## E. Rankings

### Top 5 biology ideas to raise guidance efficiency (η_r)
1. **Deny station-holding (R10 + R11).** The guided path must be ≥3× swim speed everywhere, accelerating, with no eddies behind baffles and no lip shear layers. This turns rheotaxis from a risk into irrelevance. *Evidence: Fossette 2015, Malul 2019, Rakow & Graham 2006. Confidence MEDIUM. Test: flume station-holding vs velocity (S3).*
2. **Surface-weighted, full-depth apex entrance.** Take the top 1–2 m preferentially, where *Catostylus* probably sits, without relying on it: depth use in rhizostomes is dynamic. *Test: depth histograms day/night/tide in a column tank (S2), and a camera/ROV depth survey in the the plant channel during a bloom.*
3. **Validate η with LIVE animals against passive surrogates.** Agar bells measure hydraulics alone. Live minus passive gives the behavioural effect, which tells you whether biology helps or hurts η at each velocity. (Cheap, and it makes the tank results credible.)
4. **Dark-by-default, then test dim red vs white light at the apex (S1).** Light is the only plausible attractive cue, but *Catostylus* is non-zooxanthellate, so expect weak or no effect. Lights also attract fish. *Confidence LOW. Adopt only if the choice test shows >60:40 attraction with no rise in station-holding [threshold is a proposed test criterion].*
5. **Size-class-aware operation.** October animals (6.5 cm) are weak, nearly passive swimmers. November–December animals (12–18 cm) swim ~2× faster. Use more entrance flow (the 20–35% setting) when bells are larger. *Basis: speed scales with mass to ~70 g, then levels off (Larson 1987); UAE monthly bell sizes (Aravind 2023).*

### Top 5 biology ideas to raise survival
1. **Zero-air path (R01, R02).** Flooded screw pockets, submerged transfers, full-bore pipe, no free-fall at the outlet, seawater-only wash, dissolved-only O₂ and TDG ≤100%. This is the main aquarium killer and is fully controllable.
2. **Oxygen by biomass, not by headcount (R03–R05).** Monitor DO along the line. Inject pre-dissolved O₂ above ~6.6 kg/m³. Remember that the pipe concentrates intake density ~78×.
3. **Contact-free, low-shear conveyance (R07, R12, R16).** Water-to-water transfer, large radii, low-rpm screws. The excluder must be self-clearing so oversize bells go out alive through the turtle chute, not pinned.
4. **Thermal and salinity match plus release siting (R08, R09, R17).** Shade the head tank, never use thermal or brine plume water, and release at ambient conditions over soft sediment away from structures. Match light at release (night release after a dark transit) to avoid a light-triggered spawning pulse.
5. **Measure delayed survival with a pulsation-recovery score (R20).** Hold a sub-sample in a kreisel for 24–96 h and score "belling nicely and evenly" (AZA), pulse rate, bell damage and trapped gas. Use the results to tune transit time and density. This is a genuine first: no published data exist.

---

## Key unknowns (in order of what they decide)
1. Survival of any scyphomedusa after screw lift and km-scale piping (initial and 96 h).
2. *Catostylus* (Gulf) depth distribution by day, night and tide; whether it really is in the top 1 m.
3. Respiration rate and critical oxygen level (Pc) of Gulf *Catostylus* at 30–35 °C; mucus BOD under handling stress.
4. Shear and strain damage threshold for medusae.
5. Thermal ceiling (CTmax) and salinity limits of Gulf *Catostylus*.
6. Whether light or shade changes rhizostome heading or activity in flow.
7. Zooxanthellae status of Gulf *C. perezi* (expected absent).
8. Where Gulf *Catostylus* polyps live; whether JAZR materials get colonised.
9. Noise level at the bell from the screws; the no-effect level for statocysts.

---

## Sources
**Opened at source (full text or abstract) in this stream**
- AZA Aquatic Invertebrate TAG, *Jellyfish (Cnidaria & Ctenophora) Care Manual*, 3rd ed. (temperature p.18; light/spawning p.18; flow p.20; water quality and bubbles pp.21–22; transport pp.32–34; capture p.43). https://assets.speakcdn.com/assets/2332/aza_jellyfish_care_manual.pdf
- Purcell J.E. et al. 2010. Use of respiration rates of scyphozoan jellyfish to estimate their effects on the food web. *Hydrobiologia* 645:135–152. https://doi.org/10.1007/s10750-010-0240-9 (PDF: https://www.vliz.be/imisdocs/publications/ocrd/213918.pdf)
- Malul D. et al. 2019. *Rhopilema nomadica* and *Rhizostoma pulmo* swim faster against the flow than with the flow. *Sci Rep* 9:20337. https://pmc.ncbi.nlm.nih.gov/articles/PMC6937341/
- Fossette S. et al. 2015. Current-oriented swimming by jellyfish and its role in bloom maintenance. *Curr Biol* 25:342–347. https://doi.org/10.1016/j.cub.2014.11.050 (abstract via Europe PMC)
- Solé M. et al. 2016. Evidence of cnidarians sensitivity to sound after exposure to low frequency noise underwater sources. *Sci Rep* 6:37979. https://pmc.ncbi.nlm.nih.gov/articles/PMC5175278/
- Neil T.R. & Askew G.N. 2018. Jet-paddling jellies… *Catostylus mosaicus*. *J Exp Biol* 221:jeb191148. https://doi.org/10.1242/jeb.191148
- Rakow K.C. & Graham W.M. 2006. Orientation and swimming mechanics by *Aurelia* in shear flow. *Limnol Oceanogr* 51:1097. https://doi.org/10.4319/lo.2006.51.2.1097
- West E.J., Pitt K.A. et al. 2009. Top-down and bottom-up influences of jellyfish on primary productivity… (*C. mosaicus* non-zooxanthellate vs *P. punctata* zooxanthellate). *Limnol Oceanogr* 54:2058. https://doi.org/10.4319/lo.2009.54.6.2058
- Garm A., O'Connor M., Parkefelt L., Nilsson D.-E. 2007. Visually guided obstacle avoidance in the box jellyfish. *J Exp Biol*. https://doi.org/10.1242/jeb.004044
- Makabe R. et al. 2014. Marine artificial structures as amplifiers of *Aurelia aurita* s.l. blooms: a newly installed floating pier. *J Oceanogr* 70:447–455. https://tethys.pnnl.gov/sites/default/files/publications/Makbeetal2014.pdf
- Feng S. et al. 2017. Selective suppression of in situ proliferation of scyphozoan polyps by biofouling. *Mar Pollut Bull* 114:1046. https://doi.org/10.1016/j.marpolbul.2016.10.062
- Cassiopea heat stress: *C. xamachana* life-cycle heat stress, *Oceans* 6(1):6 (2025), https://doi.org/10.3390/oceans6010006; *C. andromeda* temperature and metals (2022), https://doi.org/10.1080/17451000.2022.2066132 (abstracts via OpenAlex)
- Behera D.P. et al. 2022. High occurrence of *Catostylus perezi* near industrial development, Gulf of Kutch. *Indian J Geo-Mar Sci* 51:536. https://doi.org/10.56042/ijms.v51i06.41458
- Pitt K.A. & Kingsford M.J. 2000. Geographic separation of stocks of *C. mosaicus*. *MEPS* 196:143 (strong swimmers, estuarine retention). https://int-res.com/abstracts/meps/v196/p143-155
- Aravind A. 2024. Reproductive biology of the jellyfish outbreak along the UAE coastal waters (PhD, UAEU). https://scholarworks.uaeu.ac.ae/all_dissertations/314
- Frolova A. & Miglietta M.P. 2020. *Aurelia* thermal tolerance (polyps; method caveats). *Front Mar Sci* 7:93. https://doi.org/10.3389/fmars.2020.00093

**Abstract or search-result level only (cite with care)**
- Larson R.J. 1987. Costs of transport for *Stomolophus meleagris*. *Can J Zool* 65:2690 (15 cm/s; 0.05 ml O₂ h⁻¹ g WW⁻¹ active at 30 °C). https://fau.isle.flvc.org/node/31230
- Thuesen E.V. et al. 2005. Intragel oxygen promotes hypoxia tolerance of scyphomedusae. *J Exp Biol* 208:2475. https://cob.silverchair.com/jeb/article/208/13/2475/15656/
- Vaquer-Sunyer R. & Duarte C.M. 2008. Thresholds of hypoxia for marine biodiversity. *PNAS* 105:15452. https://pmc.ncbi.nlm.nih.gov/articles/PMC2556360
- Hays G.C. et al. 2015 (Fossette co-author). High activity and Lévy searches: jellyfish can search the water column like fish. *Proc R Soc B*. https://research.ucc.ie/en/publications/high-activity-and-l%C3%A9vy-searches-jellyfish-can-search-the-water-co/
- Honda N. et al. 2009. *Nemopilema nomurai* swimming depths (tags). *Fish Sci* 75:947. https://nagasaki-u.repo.nii.ac.jp/records/16403
- Hamner W.M. & Hauri I.R. 1981. Long-distance horizontal migrations of zooplankton (*Mastigias*). *Limnol Oceanogr* 26:414 (via Dawson & Hamner 2003, https://thescyphozoan.ucmerced.edu/tsPDF/Dawson&Hamner2003.pdf)
- Abrams M.J., Goentoro L. et al. 2015. Self-repairing symmetry in jellyfish. *PNAS*. https://authors.library.caltech.edu/records/r7pmj-fbx84
- Hoover R.A. & Purcell J.E. 2009. Substrate preferences of scyphozoan *Aurelia labiata* polyps. *Hydrobiologia* 616:259. https://dx.doi.org/10.1007/s10750-008-9595-6
- Duarte C.M. et al. 2013. Is global ocean sprawl a cause of jellyfish blooms? *Front Ecol Environ* 11:91. https://eprints.soton.ac.uk/346307
- Loveridge A. et al. 2021. Extreme changes in salinity drive population dynamics of *C. mosaicus*. https://research-repository.griffith.edu.au/items/670401aa-982e-4eb4-b084-29b3373fd795
- Albert D.J. *Aurelia labiata* in Roscoe Bay avoid tidal dispersion by vertical migration (*J Sea Res*), and Wadden Sea medusae tidal migration, https://hmr.biomedcentral.com/articles/10.1007/BF02367045
- Blue pigment "rhizostomins" in *C. mosaicus*, AMSA 2022 abstract. https://amsa-2022.p.asnevents.com.au/days/2022-08-09/abstract/80996
- Dong J. et al. 2018. *Rhopilema esculentum* stock enhancement, Liaodong Bay. IntechOpen. https://www.intechopen.com/chapters/60154
- Pitt K.A. 2000. Life history and settlement preferences of *C. mosaicus*. *Mar Biol* 136:269 (**not read at source**). https://doi.org/10.1007/s002270050685
- Fish shear analogue: MF18116, https://publish.csiro.au/MF/MF18116; Harbor/Nofima electric fence (trade press), https://www.fishfarmingexpert.com/aquaculture-atlantic-technological-university-electric-fence/electric-fence-maker-has-positive-news-for-gill-health-conference/1926531

**Project files used:** `../../JAZR_v4.md`, `../00_TEST_REPORT.md`, `../00_data/README.md` (Hashemi 2025 sizes; Aravind 2023 bell sizes), `../04_biology_wildlife_ops/params.py`, `../../../agent_enec_science.md`, `../../../05_fact_check.md`.
