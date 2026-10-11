# 05 · Economics, risk, emissions and regulatory tests: JAZR Gate v3

*Run on 11 Oct 2026. Re-run with `python3 run_all.py` (about 7 s). Tests: `python3 -m pytest tests -q` (19 passing).*
*Never-invent rule: every input sits in `inputs.py` with a label. **VERIFIED** means a source was read. **DOC** means a figure from v3 or the audit. **MODEL** means twin output. **ASSUMED** means an engineering or economic assumption. Change the assumptions, not the code.*

| File | Contents |
|---|---|
| `inputs.py` | All parameters, with ranges and source labels |
| `econ.py` | Cost, frequency (Gamma-Poisson), Monte Carlo NPV, break-even, real option and emissions |
| `run_all.py` | Writes `out/results.json`, `out/npv_table.csv` and `charts/*.png` |
| `data/site_event_counts.csv` | 51 coastal nuclear sites and 41 generation-affecting events, from `13_global_incidents.md` (§A–G and the §J "searched, none found" list) |
| `data/event_severity.csv` | Unit-days lost for each of 19 events (ranges; "n.s." durations marked ASSUMED) |
| `data/alternatives.csv`, `data/regulatory_checklist.csv` | Tests T4 and T6 |
| `tests/test_economics.py` | Checks that the cost and emissions tables compute and their totals agree, plus checks on the NPV, break-even and data |

---

## Headline (for the pitch team)
1. **Whether JAZR pays back depends almost entirely on how often the plant would lose output to jellyfish. Nobody knows that number.** No the plant outage is public. Fitting the global catalogue and adding the plant's 0 events in 5.5 years gives **≈0.015 events per site-year** (about one in 68 years). At that rate the **probability of payback is ≈0%** in every case. JAZR pays back **only at a Hanul- or Gravelines-like event rate**: 87% (Case A) at Hanul's 1996–2006 rate.
2. **v3's AED 30–80 M per unit is probably low.** A bottom-up estimate gives **USD ≈51 M (AED ≈187 M) per unit at mode values**. The 5 km seabed pipe alone is USD 7.5–15 M (AED 28–55 M).
3. **So pitch break-even, not payback.** At v3's cost, JAZR breaks even if it prevents **≈0.9 unit-days per unit per year** (≈28 unit-days over 30 years). That equals **one Hanul-type site event every ~2 years**.
4. **Pilot first.** A one-unit pilot puts a quarter of the capital at risk and buys information on the screen's efficiency (η), the cost and the local bloom rate.

---

## T1 · Cost model (CAPEX by component, OPEX, ranges, levelised cost)
**Purpose.** Test v3's "AED 30–80 M per unit".
**Method.** Case A takes v3's figure as a triangular distribution (30/50/80). Case B builds the cost bottom-up from 7 components, adds engineering, nuclear QA, licensing and seismic (20–40%), then contingency (20–50%). OPEX covers maintenance (2–4% of direct cost), staff and drills, pigging and inspection, and energy. The Monte Carlo uses 20k draws.
**Result (per unit).**

| Item, USD M | Low | Mode | High |
|---|---|---|---|
| Training wall 150–200 m | 1.5 | 4 | 10 |
| Piled gantry | 3 | 6 | 15 |
| Mesh bays, drums, rails, motors | 2 | 4 | 8 |
| Bypass, camera, screw, head tank, pump | 2 | 4 | 8 |
| **Seabed HDPE pipe 5 km, 1.2 m ID** (auditor's USD 1.5–3 k/m) | 7.5 | 10 | 15 |
| Outlets ×2 | 0.5 | 1 | 3 |
| Controls share | 0.03 | 0.07 | 0.27 |
| **Total incl. markups** | **23.8 (AED 87 M)** | **51.0 (AED 187 M)** | **124.5 (AED 457 M)** |

- Monte Carlo CAPEX per unit, P10–P90:
  - Case A: AED 40–68 M.
  - Case B: AED 190–263 M.
- OPEX: USD 0.5–0.8 M per unit-year (A) and USD 1.2–1.7 M per unit-year (B).
- **Levelised cost at 6% over 30 years: USD 1.7 M per unit-year (A) and USD 5.8 M per unit-year (B).**
- Line power while running: **≈490 kW** (440–540). That is the screw at 2 m³/s lifting 5–11 m plus the 195–286 kW pipe pump in v3.
- Cross-check: the Glenn-Colusa fish screen cost **≈US$75 M (1998–2001; 85 m³/s; ~1,100 ft screen plus a river gradient facility)**, about US$145 M in 2025 money. The source is the Water Education Foundation GCID briefing PDF. A screen of that scale costs tens to hundreds of millions of US dollars.

**Verdict: RISK.** Case A is plausible only without the 5 km pipe or with one shared pipe. Present cost as "AED 30–80 M/unit (team), bottom-up up to ~AED 190 M; pipe is the swing item". The cheapest saving is a shared pipe or a 3 km phase 1.

## T2 · Benefit model: event frequency and severity from global data
**Purpose.** Turn the 91-row catalogue into outage risk at the plant.
**Method.**
- **Frequency.** Generation-affecting jellyfish and salp events at 51 coastal nuclear sites: 41 events over ≈2,222 site-years. Zero-event sites come from 13_ §J. Fit a Gamma-Poisson (negative-binomial MLE), then update with the plant's 0 events in 5.5 site-years.
- **Severity.** Unit-days lost per event, bootstrapped from 19 events, each drawn uniformly within its range. A unit-day is 1,337 MWe net (WNA) × 24 h = **32.1 GWh**.
- **Value.** USD 46–100 per MWh, mode 60:
  - USD 46 is the Fujairah F3 CCGT tariff bid in 2019, our conversion.
  - The the plant PPA price is not public.
  - The high end is an LNG-fuel assumption.
- **Other inputs.** A fixed cost per event of USD 0.1–2 M, assumed. A response-crew saving anchored on Gravelines spending ~€0.5 M a year.
- **JAZR effect.** Loss multiplier = A·(reach/0.95) + (1−A):
  - reach 5.5/12/28% (**MODEL, twin, labelled toy**);
  - availability A 85–99% (assumed).

**Result.**

| Scenario | λ (events/site-yr) | Expected loss without JAZR (USD M/yr) |
|---|---|---|
| S0 base: global fit + the plant 0/5.5 yr | 0.015 (P90 0.044; P(λ>0.1) = 2.4%) | 0.22 |
| S1 jellyfish-prone site (pooled rate of event sites) | 0.057 | 0.86 |
| S2 Hanul-like (9 shutdowns 1996–2006) | 0.82 | 12.5 |
| S3 Gravelines-like (3 events 2025–26) | 1.5 | 22.9 |

Mean severity is **7.7 unit-days per event** (median 3.75). The mean is dominated by multi-unit trips: Gravelines 2025, Turkey Point 1984, Hanul 2021.

**Caveats.**
- Public reporting is incomplete, which biases the rate low.
- The zero-event list is not every coastal plant, which biases it high.
- Severity draws on 1 GW-class units.
- the plant's bloom season is Oct–Nov (UAEU), and the Gulf has a regional precedent (Kuwait "annual", Oman 2002–03).

**Verdict: the decisive uncertainty.** ENEC's own (unpublished) outage and near-miss data would settle it. Ask for it in mentoring.

## T3 · NPV, payback, break-even and tornado
**Method.** Each draw runs a 30-year year-by-year Poisson event path. Construction takes 2 years and benefits start in year 2. Discount rates: 3, 6, 8 and 10%.
**Result: P(NPV>0), full rollout (4 units).**

| | 3% | 6% | 8% | 10% |
|---|---|---|---|---|
| A · S0 base | 0.3% | **0.1%** | 0.1% | 0.1% |
| A · S1 prone | 0.5% | 0.3% | 0.2% | 0.2% |
| A · S2 Hanul | 95% | **87%** | 79% | 67% |
| A · S3 Gravelines | 100% | 99.9% | 99% | 98% |
| B · S0 / S1 | 0% | 0% | 0% | 0% |
| B · S2 Hanul | 8% | 2% | 0.6% | 0.3% |
| B · S3 Gravelines | 61% | 30% | 16% | 8% |

Median NPV at 6% is −80 M (A·S0), +54 M (A·S2) and −164 M (B·S2), in USD. All rows are in `out/npv_table.csv`.

**Break-even** (mode inputs, reach 12%, availability 95%):

| | 3% | 6% | 8% | 10% |
|---|---|---|---|---|
| Case A: unit-days per unit-year | 0.75 | **0.93** | 1.07 | 1.21 |
| Case A: site events needed per year | 0.38 | **0.47** (one every 2.1 yr) | 0.54 | 0.61 |
| Case B: unit-days per unit-year | — | **3.0** | 3.5 | 4.1 |
| Case B: site events needed per year | — | **1.5** | 1.8 | 2.1 |

**Tornado** (`charts/tornado_npv.png`; Case A, 6%, base = prone-site rate). **Only the event rate moves NPV across zero.** CAPEX and OPEX come next. The twin's reach (5.5–28%) and availability hardly matter, because once JAZR stops most of the swarm the residual loss is small.

**Charts.**
- `charts/payback_probability_vs_event_rate.png`: P(payback) against λ.
- `charts/npv_hist_S2.png`.

**Verdict: FAIL as a "payback" claim, PASS as a "break-even insurance" claim.** Say: *"At AED 30–80 M per unit, JAZR breaks even if it prevents about one unit-day per unit per year: one Hanul-type event every two years at the site. the plant has no public event, so we propose a pilot."* Do **not** say "a handful of avoided unit-days over 60 years" (v3 §5). At 6%, Case A needs ≈28 unit-days per unit over 30 years.

## T4 · Alternatives (cost and capability; `data/alternatives.csv`)

| Option | CAPEX | Throughput | Crew in bloom | Wildlife | Evidence |
|---|---|---|---|---|---|
| Status quo (screens, crews, boats) | ~0 incremental; Gravelines ~€0.5 M/yr | ~1 t/h per boat | 3–7 boats 24/7, 24 h crews | Lethal | Failed at Gravelines in 2026 and Hanul in 2021 |
| Hongyanhe-style layered nets | Not stated | 2,420 t → 48.5 t per season | Suction crews, cranes, drills | Lethal; fouling; turtle risk | Only public NPP success (self-reported) |
| Bubble curtain alone | 135–440 kW compressor | Deflection only | Low | Fauna effects not assessed | Lab only |
| Higashi-Niigata live pumping | Not stated | ~86% of 290 t/yr | Low | Lethal (decay) | Operating |
| **JAZR v3** | AED 30–80 M/unit (team), up to ~AED 190 M (bottom-up) | Pilot ~35 t/h peak per line; 108 t/h needs ~3 lines | 1–2 operators, no boats | Live by design; survival untested | Twin only; tank pending |


## T5 · Phasing and real options
**Method.** Pilot on 1 unit now. At year 4 the team knows the true reach, the cost and the observed events, and expands to 3 more units only if expected NPV > 0. We compare two learners: a sceptical Bayesian using the global prior, and a site-data learner.

**Result (Case A, 6%, E[NPV] in USD M).**

| Scenario | Full now | Pilot only | Pilot + option (site-data learner) | P(expand) |
|---|---|---|---|---|
| S0 base | −80 | **−20** | −20 | 1% |
| S1 prone | −73 | **−18** | −20 | 5% |
| S2 Hanul | **+61** | +15 | +42 | 82% |
| S3 Gravelines | **+180** | +45 | +141 | 98% |

**Verdict.** A pilot **cuts the downside fourfold**: −20 M instead of −80 M if blooms are rare. It costs about 19–39 M of upside if blooms are frequent. With no the plant data, the pilot is the rational first step, and v3 already says this. In Case B even the pilot is negative unless the rate is Gravelines-like.

## T6 · Emissions (added at the coordinator's request)
**Method.**
- **Operation.** Line kW × hours, at the marginal UAE grid factor of 0.359–0.468 kgCO₂/kWh. Sources: LowCarbonPower 2023 and Ember/OWID 2024 (VERIFIED); DEWA 2020 is 0.404. Plant electricity used is electricity not exported, so it displaces gas.
- **Embodied.** Steel 1,000–2,500 t, HDPE 600–1,200 t and concrete ballast 2,500–7,500 t per unit, with ICE-database factors (recalled, not re-fetched: ASSUMED), plus installation fuel.
- **Status quo boats.** 3–7 boats (Gravelines, VERIFIED) × 5–15 days × 20–60 L/h × 2.68 kg/L, at 1–5 blooms a year (ASSUMED).

**Result (mode values, per site-year).**

| Item | tCO₂ |
|---|---|
| JAZR, 4 lines (operation 158/unit + embodied 209/unit, amortised) | **1,468** (embodied ≈6,300 t per unit up front) |
| Status quo boats, diesel | 206 |
| **One avoided unit-day of outage replaced by gas** | **≈12,960** |

- Avoided emissions per site-year: ≈1,160 (S0), ≈4,400 (S1), ≈64,000 (S2).
- Carbon payback: 48 years (S0), 6.7 years (S1), 0.4 years (S2).

**Verdict.** On direct emissions **JAZR is the highest-emitting option**, about 7× the boats, because of the steel and pipe. It is carbon-positive only through avoided outages. Do not claim "low-carbon" without the outage term. Say: *"one avoided unit-day saves ~13,000 tCO₂, about 9 years of JAZR's whole-site footprint."*

## T6b · Regulatory and permit checklist (`data/regulatory_checklist.csv`): 2 PASS, 11 RISK, 1 N/A

| # | Requirement | Status |
|---|---|---|
| R1 | FANR/Nawah modification review: in the cooling-water path (IAEA SSG-71; FANR regulations IAEA-based) | RISK |
| R2 | Seismic II/I and external hazards near safety SSCs | RISK |
| R3 | Never block UHS flow (open relief bay, passive relief) | PASS (design), needs evidence |
| R4 | **Cyber security** of the control-room-actuated system (FANR-REG-08 v2, May 2024). **v3 is silent** | RISK |
| R5 | ENEC brief: "no plant redesign" | RISK |
| R6 | EAD environmental permit and EIA for marine works (Federal Law 24/1999). the plant's own EIA took >4 years | RISK |
| R7 | **Amend the plant's annually renewed EAD Operational Environmental Permit** for new outlets releasing live biomass | RISK (highest) |
| R8 | Federal Law 23/1999 and MR 302/2001: protected marine turtles | RISK |
| R9 | Abu Dhabi Maritime Administrative Decision 69/2025: marine-works permit (AED 30,000 fine without one), notices to mariners, navigation aids | RISK |
| R10 | Site maritime security zone (CICPA/Coast Guard) | RISK |
| R11 | **Decision 17/2026** (DMT): testing of autonomous or remotely operated small marine craft. **N/A** to JAZR's fixed plant; **applies if the team uses USVs or drones** for drifters or outlet surveys | N/A |
| R12 | Disposal of recovered biomass ("recover" mode) | RISK |
| R13 | No chemicals, discharge unchanged | PASS |
| R14 | Works inside an operating nuclear intake (work control, derate) | RISK |

**Verdict.** No requirement is a blocker in principle, but the permit path takes years. Add a one-line "permit path" slide: FANR/Nawah mod + cyber → EAD EIA + permit amendment → ADM marine works → CICPA. **Add cyber security to v3.**


## T8 · Competition-rule compliance (from `00_official_pages.md`): team to-dos

| # | Requirement | Action |
|---|---|---|
| 1 | Team of 3–4, **≥1 UAE national**, all UAE residents (passport or EID), students or 2025–26 graduates, one track only | Confirm names and IDs. Check that "IIT Delhi – Abu Dhabi Cohort" is your team. Under-18s tick the declaration |
| 2 | Deadline **11 Oct 2026, 23:59 GMT+4 (today)** | Submit the 10-slide PDF (participant details, exec summary, detailed proposal), the 1–2 min video and the form answers |
| 3 | Proposal must contain: problem, solution and benefit, simple diagram, technical and environmental considerations, **assumptions and limitations**, test/demo plan | Use `inputs.py` labels as the assumptions slide |
| 4 | **AI declaration**; team must explain the work in its own words | Declare AI use (research, drafting, code). Every member rehearses the cost, break-even and twin numbers |
| 6 | Confidentiality and media | Don't publish challenge materials without approval. Keep others' information confidential; an NDA may be required |
| 7 | IP: you own it, ENEC gets a non-exclusive licence, organisers may publish | Include nothing you can't share (third-party images or data without rights) |
| 8 | Demo Days 10–13 Nov, ADNEC Al Ain; attendance required | Confirm availability; prepare the physical prototype or simulation ("Critical") |
| 9 | Language: English. "Basic prototype, simulation or model, not just a concept" | Attach the twin and tank evidence |
| 10 | Remove self-ratings (v3 §8) from all submitted material | Edit before export |

---

## Sources verified this session
- WNA reactor database (the plant 1–4: 1,337 MWe net; 2024 load factors 83.7–85.9%): world-nuclear.org/nuclear-reactor-database/details/SITE-1
- the plant PPA (structure only, no price public): world-nuclear-news.org "First nuclear generation purchase agreement for UAE"; enec.ae ENEC Commercial
- Fujairah F3 CCGT tariff bids, 16.79–17.11 fils/kWh (2019): MEED via search
- GCID fish screen, ~US$75 M: watereducation.org/sites/main/files/file-attachments/gcid.pdf
- UAE grid factor 359–468 gCO₂/kWh: lowcarbonpower.org (UAE); inzonex Power Atlas (Ember/OWID); Climatiq (DEWA 2020)
- the plant EAD Operational Environmental Permit (first issued 2018, renewed annually; EIA >4 years): enec.ae/our-subsidiaries/enec-operations/environment-permit/
- EAD EIA authority, Federal Law 24/1999: WAM 2023 (SEA programme); Khaleej Times 2012
- Abu Dhabi Administrative Decision 69/2025 (maritime safety bylaw): admaritime.ae PDF; Gulf News (AED 30,000 fine)
- Decision 17/2026 (autonomous marine craft testing): LexisNexis Middle East blog, 27 Jun 2026 (secondary; primary text not read)
- Federal Law 23/1999 and MR 302/2001 (protected turtles): FAOLEX / UNEP LEAP summaries
- FANR-REG-08 v2 (physical protection and cyber security, May 2024): WAM. IAEA SSG-71 (modifications to NPPs, 2022): iaea.org
- **Not verified:** Hanul 2021 "US$21.8 M" (taken from 13_ [48]; not re-confirmed tonight; S&P confirms the shutdowns but gives no cost). Also: FANR modification-procedure text; the waste regulator for biomass; ICE embodied-carbon factors; all [ENG] unit rates.
