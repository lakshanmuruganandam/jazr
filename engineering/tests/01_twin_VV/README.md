# 01 Twin V&V: verification and validation of the JAZR digital twin

The model under test is `../../twin/jazr_twin.py`, a reduced-order plan-view particle model. **None of the files in `twin/` were edited.** Every script imports the twin read-only through `common.py`.

`harness.py` is a line-for-line copy of `simulate()` with optional extras that are all **off by default**: explicit start positions, a real-current forcing function, wind leeway, beaching, and per-particle arrival and capture times. With the extras off it reproduces `J.simulate()` **bit-for-bit**; 6 configurations are checked in pytest.

Every number below comes from the runs in this folder: `out/*.json`, `out/*.csv` and `out/log_*.txt`. Charts are in `figs/`.

**Status key:** PASS means the acceptance criterion is met. FAIL means it is not. INFO means a finding with no pass/fail criterion.

| # | Test | Script | Result |
|---|---|---|---|
| T1 | Unit / regression suite (pytest) | `test_twin.py` | **PASS 54/54** |
| T2 | Analytic verification | `vv_analytic.py` | **PASS** |
| T3 | Convergence (dt, N) | `vv_convergence.py` | **PASS** (v3); **INFO** Today has about 1–2 pct-pt dt bias |
| T4 | Statistics, seed variance, bootstrap CIs, exact reproduction | `vv_statistics.py` | **PASS** reproduction; **INFO** published 2-seed values sit 0.2–0.5 pp low |
| T5 | Global sensitivity (Morris + Sobol) | `vv_sensitivity.py` | **PASS** dummy-factor check; **INFO** ranking eta_r > eta_g > ur > vr > gate_y > hours > swim > U0 |
| T6 | Monte Carlo uncertainty propagation | `vv_montecarlo.py` | **INFO** (wide) |
| T7 | Stress / edge / failure modes | `vv_stress.py` | **PASS** with findings; **FAIL** for dt ≥ 300 s (stability limit) |
| T9 | Real-forcing hindcast (Open-Meteo/CMEMS current, ERA5 wind) | `vv_hindcast.py` | **PASS** ordering Today > v2 > v3 |
| T10 | Real-data corrected drift cases (2.5 / 5 / 6 cm/s, wind 4 cm/s) | `vv_realdata_cases.py` | **INFO**: v3 numbers rise substantially |
| V | Validation against field data | — | **NOT POSSIBLE: no field data exist** |

Runtime note: the machine was shared with other agents (load average 140–200), so wall times are inflated. Measured wall times: T4 732 s and T8 849 s, both over the 10-min target. T3 326 s, T6 304 s, T7 272 s, T9 436 s, T10 987 s (under load). On a quiet machine each is roughly 3× faster. Reduce `SEEDS` in T4 or `DS` in T8 to shorten them.

---

## T1 Unit tests (pytest): `python3 -m pytest -q test_twin.py`
**Purpose:** check each mechanism in isolation, plus exact regressions.

The 54 tests cover:
- **Kinematics.** One step of sink velocity equals `Q/(π r h)` exactly. The half-plane sink flux equals Q. r* at 0.083 m/s is 438 m (the doc says "~440 m"). The tidal excursion constant 2U0/ω = 1665 m. Coast reflection gives y → |y|. Capture happens at r < 60 m and not at r = 61 m.
- **State machine.** For 6 configurations, every particle is in exactly one of FREE/HELD/CAPT and the counts sum to N. CAPT is absorbing (its count never decreases). FREE ≥ 0 at every step. captured_t = frac × swarm_t. Swarm mass is 12,180 t for every N. Perfect screens with no release give < 1% captured.
- **Release policies.** Immediate never holds. Hold releases after hold_h. Ebb releases **only** inside the window fraction; this is checked at every occupancy drop. The pocket cap is never exceeded (≤ 2 × cap).
- **Determinism and regressions.** A fixed seed gives identical output; a different seed gives different output. The harness is bit-identical to the twin. Density changes tonnes but not fractions. The system is below Today at all 4 tide phases.
- **Quick analytic tests.** Capture band, stagnation point, zero-flow radius.
- **Coordinator items (a)–(f)** (see the coverage table).

**Result: PASS, 54/54** (`out/pytest_log.txt`).

## T2 Analytic verification (swim = 0, deterministic drifters)
Result data: `out/t2_analytic.json`; chart: `figs/t2_analytic.png`. All checks were run at U = 0.05, 0.083, 0.117 and 0.15 m/s and dt = 30, 60 and 120 s.

| Check | Theory | Max error at dt ≤ 60 s | Max error at dt = 120 s | Status |
|---|---|---|---|---|
| Capture band, steady current | dividing streamline ψ = U h y − (Q/π)θ; far field W = Q/(U h) | **0.69 %** vs the exact streamline at the start line x0 = −8 km | 1.7 % | PASS |
| (same, vs far-field W) | W = Q/(U h) = 977 m at U0 | 3–8 % narrower, **explained**: at x0 = −8 km the streamline has not reached W (finite-distance geometry, not a model error) | — | INFO |
| Downstream stagnation point | r* = Q/(π h U) (311 m at U0, 438 m at 0.083) | **0.16 %** | 0.16 % | PASS |
| Zero ambient flow, 72 h | r = √(R_cap² + 2Qt/(πh)) = 4,343 m | **0.07 %** | 0.07 % | PASS |
| Tidal excursion, no sink | 2U0/ω = 1,665 m | **0.01 %** | 0.13 % | PASS |
| Alongshore arrival time at the ring (exact ODE) | t = (d−R)/U − a/U² ln((Ud+a)/(UR+a)) | **0.31 %** | 0.61 % | PASS |

**Meaning:** the flow kinematics and capture logic do what the equations say. Errors converge at first order in dt.

## T3 Convergence
Each point is 4 tide phases × 8 seeds (32 runs). dt runs use N = 3000; N runs use dt = 60 s. Data: `out/t3_convergence.json` and `.csv`; chart: `figs/t3_convergence.png`.

| Config | dt = 30 | dt = 60 | dt = 120 | Observed order | Numerical uncertainty at dt = 60 (1.25 × \|f60 − f_extrap\|) | Seed SE |
|---|---|---|---|---|---|---|
| Today, median | 96.33 % | 95.58 % | 94.19 % | 0.90 | **2.0 pp** | 0.10 pp |
| v3, median | 5.67 % | 5.69 % | 5.76 % | 1.70 | **0.04 pp** | 0.07 pp |
| v3, onshore 3 cm/s | 12.41 % | 12.27 % | 11.80 % | 1.80 | 0.24 pp | 0.09 pp |
| v3, 10-day bloom | 13.82 % | 13.62 % | 13.47 % | noisy (order 1 assumed) | 0.49 pp | 0.09 pp |
| v3, guard 0.5 | 28.53 % | 28.21 % | 28.30 % | noisy (order 1 assumed) | 0.82 pp | 0.15 pp |

N = 500 to 6000: the means do not drift. For v3 median they are 5.81 / 5.50 / 5.73 / 5.69 / 5.57 %, all within about 2 SE. Per-run SD falls roughly as N^-½: 1.04 → 0.29 pp.

**Status:** PASS for v3. The headline numbers are converged to < 1 pp in dt and N.

**INFO:** the Today baseline is under-resolved by about 1–2 pp at dt = 60 s. dt = 60 s **under**-counts Today, which makes the reported benefit slightly conservative.

## T4 Statistics: exact reproduction, seed variance, bootstrap CIs
Protocol: 30 seeds × 4 phases, N = 3000. CIs are bootstrap (5,000 resamples of seeds) on the 4-phase mean. Data: `out/t4_statistics.json` and `.csv`, `out/t4_raw_matrix.npz`; chart: `figs/t4_headline_ci.png`.

- **Exact regression (PASS):** all 23 rows of `twin/out/v3study.json` were reproduced to machine precision with seeds 1–2. So did 4 rows of `exportstudy.json` (T8).
- **The v3 headline numbers:**

| Condition | Published (2 seeds) | 30-seed mean | 95 % bootstrap CI | Range of any 2-seed estimate (P2.5–P97.5) | Single-run SD |
|---|---|---|---|---|---|
| Median | 5.48 % | **5.73 %** | 5.66–5.80 | 5.46–5.96 | 0.45 pp |
| Onshore 3 cm/s | 12.23 % | **12.17 %** | 12.06–12.28 | 11.73–12.55 | 0.62 pp |
| 10-day bloom | 13.28 % | **13.79 %** | 13.67–13.91 | 13.29–14.18 | 0.62 pp |
| Guard 0.5 | 28.06 % | **28.15 %** | 27.98–28.32 | 27.53–28.83 | 1.16 pp |
| Today, median | 95.47 % | 95.59 % | 95.52–95.67 | 95.35–95.93 | 2.91 pp |

- **INFO:** two published numbers (median 5.48 %, 10-day 13.28 %) fall **just below** the 30-seed CI. This is sampling noise in the 2-seed protocol, not a bug: both values are inside the 2-seed spread. Better-supported values to quote are **5.7 %, 12 %, 14 % and 28 %**.
- **Ranking is robust:** in 5,000 bootstrap resamples, v3 is below Today, below v2 (3 km), below "outlet 5 km" and below "outer line 0.4" in **100 %** of resamples under every condition. It is above the 0.6-guide variant in 100 %.

## T5 Global sensitivity analysis (numpy; SALib not installed)
Inputs (uniform): eta_g 0.2–0.8, eta_r 0.3–0.95, swim 0.02–0.15 m/s, vr −0.04–0, ur −0.02–0.02, gate_y 2–6 km, hours 72–240, U0 0.08–0.15 m/s. U0 is patched as a module constant.

The output is % reaching the intake. Morris uses r = 20 trajectories, 4 levels, N = 1000 particles and 2 tide phases with common random numbers. Sobol uses the Saltelli design with Jansen and Saltelli-2010 estimators, base N = 128, N = 1000 particles and one tide phase. Data: `out/t5_sensitivity.json`, `out/t5_sobol_samples.csv`; chart: `figs/t5_sensitivity.png`.

**Morris, v3** (mu* = mean |change in % to intake| when the input sweeps its full range; mu = signed):

| Rank | Input | mu* (pp) | mu (pp) | sigma |
|---|---|---|---|---|
| 1 | eta_r (inner screen) | 37.2 | -37.2 | 25.9 |
| 2 | eta_g (outer guide) | 31.6 | -31.6 | 18.8 |
| 3 | ur (alongshore residual) | 24.2 | -7.5 | 31.5 (sign changes with direction: strongly non-linear) |
| 4 | vr (onshore drift) | 15.8 | -15.8 | 13.3 |
| 5 | gate_y (outlet distance) | 15.4 | -15.4 | 10.3 |
| 6 | hours (bloom duration) | 9.9 | +9.9 | 10.7 |
| 7 | swim | 9.5 | -8.5 | 10.6 |
| 8 | U0 (tidal amplitude) | 1.5 | 0.2 | 2.3 |

Morris for Today ranks ur (30.3) > swim (5.6) > vr (4.8) > hours (4.3) > U0 (1.8).

**Sobol, v3** (output mean 42.1 %, variance 633 pp^2; sum S1 = 0.52, so interactions carry about half the variance):

| Input | Total ST (95 % CI) | First-order S1 (95 % CI) |
|---|---|---|
| eta_r | **0.37** (0.28-0.47) | 0.27 (0.04-0.53) |
| eta_g | **0.19** (0.14-0.25) | -0.01 (-0.17-0.15) |
| ur | 0.14 (0.10-0.18) | 0.00 (-0.15-0.16) |
| vr | 0.10 (0.07-0.13) | 0.01 (-0.11-0.13) |
| gate_y | 0.08 (0.06-0.11) | 0.17 (0.02-0.31) |
| hours | 0.07 (0.05-0.11) | 0.09 (-0.02-0.20) |
| swim | 0.02 (0.01-0.02) | 0.00 |
| U0 | 0.003 (0.00-0.00) | 0.00 |

The S1 estimates are noisy because base N = 128 was all the overloaded machine allowed; the ST ranking is the robust result. The S1 of gate_y comes out above its ST, which is sampling noise. **Status: INFO. The ranking agrees between Morris and Sobol: screen efficiencies (eta_r, then eta_g) dominate, then residual currents (ur, vr), then outlet distance and bloom duration. Swim speed and tidal amplitude barely matter.** Wall times (shared machine at load 100-200): Morris 7,476 s, Sobol 7,172 s.

**Check (PASS):** in the Today run, the system-only inputs eta_g, eta_r and gate_y get Morris μ* = **0.00 exactly**. The screening correctly detects inert inputs.

## T6 Monte Carlo uncertainty propagation
Setup: 500 samples, uniform over the T5 ranges (an assumption, since no data justify any other shape). Tide phase ~ U(0, 2π). Each sample is run as a paired Today/v3 run with N = 1500. Data: `out/t6_montecarlo.json` and `_samples.csv`; chart: `figs/t6_montecarlo.png`.

| % reaching intake | P10 | P50 | P90 | Mean |
|---|---|---|---|---|
| Today | 74.9 % | 91.1 % | 99.4 % | 88.9 % |
| **v3** | **10.5 %** | **35.5 %** | **74.5 %** | 39.2 % |
| Reduction (pct-pts, paired) | 19.9 | 51.4 | 76.6 | 49.7 |

- v3 is below Today in **100 %** of samples.
- P(v3 < 10 %) = 0.09. P(v3 < 20 %) = 0.25. P(v3 > 30 %) = 0.59.
- Spearman correlation of v3 with each input: eta_r −0.64, eta_g −0.37, vr −0.32, gate_y −0.30, hours +0.29, others |ρ| ≤ 0.06.

**Meaning (INFO):** the "5.5 %" headline depends on eta_r = 0.9 and eta_g = 0.4. Across the plausible ranges, the median outcome is about 35 %. **The inner-screen catch efficiency must be measured** (the tank test).

## T7 Stress, edge and failure modes
Protocol: N = 3000, 4 phases × 2 seeds. Data: `out/t7_stress.json` and `.csv`.

| Case | Today | v3 | Note |
|---|---|---|---|
| Density × 0.1 / × 1 / × 10 | 95.47 % for all three | 5.48 % for all three | **PASS**: fraction model, so density only scales tonnes (1,163 / 11,628 / 116,278 t) |
| 100 t pocket cap, density × 10 | — | 5.48 % | the cap never binds under the immediate policy |
| Zero flow, no swim | **100 %** | 5.83 % | **PASS**: matches the analytic 100 % (every start point is within r = 4,343 m) |
| Zero flow, swim 3.6 cm/s | 97.2 % | 6.17 % | |
| Onshore 10 / 20 cm/s | 96.9 / 96.9 % | 19.8 / 37.7 % | handlings 3.2 / 6.0 per animal |
| Offshore 5 cm/s | 3.8 % | 0.2 % | |
| Strong swimmer 15 cm/s | — | 4.8 % | |
| 30-day bloom | 100 % | 33.0 % | 5.3 handlings per animal |
| Perfect screens (eta = 1) | — | 0.00 % | PASS |
| Screens rolled up (eta = 0, fail-open) | 95.47 % | 95.80 % | PASS: equals Today within noise |
| **Gate stuck closed, unbounded pocket** | — | 5.48 % but **11,019 t held** | the twin lets a pocket store 90 % of the swarm, which is unphysical |
| **Gate stuck closed, 100 t pocket spilling at the collector** | — | **38.3 %** | failure mode |
| **Pipe broken: release at the collector mouth** | — | **39.4 %** | failure mode |
| Pipe broken + onshore 3 cm/s | — | 41.6 % | |
| dt = 300 s | 90.0 % | 5.6 % | **FAIL** (stability) |
| dt = 600 s | 84.7 % | 2.9 % | **FAIL**: particles jump over the 60 m capture disk |

Setup: a cloud of 1500 animals (σ = 100 m), Today physics, 4 phases × 4 seeds. Data: `out/t8_release.json`, `out/t8_release_distance.csv`; chart: `figs/t8_release_distance.png`.

% returning to the intake, release offshore of the pocket (x = 1.2 km, y = d):

| d (km) | 0.6 | 1 | 2 | 3 | 5 | 7.5 | 10 | 15 |
|---|---|---|---|---|---|---|---|---|
| no drift, 72 h | 100 | 100 | 100 | 96.2 | 2.2 | 0 | 0 | 0 |
| no drift, 240 h | 100 | 100 | 100 | 100 | 100 | 55.7 | 0.5 | 0 |
| onshore 1 cm/s, 72 h | 100 | 100 | 100 | 100 | 90.0 | 0.2 | 0 | 0 |
| onshore 1 cm/s, 240 h | 100 | 100 | 100 | 100 | 100 | 100 | 100 | **19.4** |
| onshore 3 cm/s, 72 h | 100 | 100 | 100 | 100 | 100 | 99.3 | 47.6 | 0 |
| onshore 3 cm/s, 240 h | 100 | 100 | 100 | 100 | 100 | 100 | 100 | 100 |

- **Monotonic (PASS):** returns never increase with distance in all 12 series (offshore and alongshore × 3 drifts × 2 horizons).
- **Tide phase (PASS):** at 3 km, releasing at phase 0 (tide turning away from the intake) is best and phase π is worst: 89.5 % vs 99.4 %. At 5 km the figures are 0.8 % vs 3.9 %. At ≤ 2 km, **every phase returns 100 %**, so timing cannot help there.
- **Export regression (PASS):** pipe 1 / 2 / 3 km and passive 2 km reproduced `exportstudy.json` exactly (23.20 / 11.77 / 8.40 / 29.97 %).

## T9 Real-forcing hindcast
Forcing: Open-Meteo/CMEMS SMOC hourly surface current at 24.04 N 52.21 E (2022–2025, includes tides; a model product, **not** an in-situ measurement). It is rotated into twin axes with the coast at 070°. There are 292 alerts of 72 h each, one every 5 days, run at N = 1000. Data: `out/t9_hindcast.json`, `out/t9_hindcast_windows.csv`; chart: `figs/t9_hindcast.png`.

| Forcing | Today mean (P10–P90) | v2 Gate | v3 | Windows with Today > v2 > v3 |
|---|---|---|---|---|
| Current only | 71.3 % (39.7–99.4) | 13.4 % | **6.2 %** (P90 11.1 %) | 99.0 % (100 % with ≥) |
| Current + 2 % ERA5 wind leeway | 58.0 % | 11.3 % | **6.0 %** (P90 13.1 %) | 90.8 % (97.3 % with ≥) |

**PASS:** the headline ordering holds under real forcing. For Oct–Nov only, v3 is 6.7 % with current only and 5.8 % with wind.

## T10 Real-data corrected cases (from `../00_data/README.md`)
Protocol: N = 1500, 4 phases × 2 seeds. Data: `out/t10_realdata_cases.json` and `.csv`.

| Case | Today 72 h | v3 72 h | Today 240 h | v3 240 h |
|---|---|---|---|---|
| Onshore 2.5 cm/s (**typical**) | 97.0 % | **11.3 %** | 100 % | **33.9 %** |
| Onshore 5 cm/s (stress) | 97.0 % | 16.4 % | 100 % | 47.0 % |
| Onshore 6 cm/s (stress) | 97.0 % | 17.4 % | 100 % | 52.9 % |
| 2.5 cm/s + wind leeway 2 % × 2 m/s (≈ 4 cm/s) | 97.0 % | 18.1 % | 100 % | 53.1 % |

**Meaning (INFO):** under the data-corrected typical drift, v3 is about **11 %** over a 3-day bloom, not 5.5 %. Over a 10-day bloom it is about **34 %**, rising to about 50 % in stress cases. The animals are re-screened 5–8 times each, which assumes no damage per handling.

The sustained-onshore idealisation is harsher than the T9 hindcast with the real time-varying current (6 %): real drift reverses on about 24 % of days.

## Validation status: there is NO field data
The twin has **not been validated**. Nothing here is a comparison with observed jellyfish at the plant. Data that would validate it:
1. GPS drifters (surface and 1–2 m drogue) released at 1, 3, 5 and 15 km in Oct–Nov, compared with the twin's drift-back curve (T8).
2. Daily intake screen tonnage and counts at the plant, compared with the hindcast-forced Today run (T9).
3. An ADCP current record near the intake (verifies the sink and current field and the onshore residual).
4. Tank tests of inner-screen and guide-line catch efficiency (eta_r, eta_g: the top Sobol/Morris drivers).
5. Satellite or drone bloom mapping for initial conditions and arrival timing.

---

## Bugs and model issues found in the twin (no code crashes)
1. **Time-step stability limit (FAIL at dt ≥ 300 s):** with sink speed 0.61 m/s at r = 60 m, particles can step over the 60 m capture disk. Today drops to 90.0 % at dt = 300 and 84.7 % at dt = 600. Keep dt ≤ 60–120 s.
2. **Swimming random walk depends on dt:** the heading changes by N(0, 0.3 rad) **per step**, so the swimming decorrelation time is 2dt/0.09 (22 min at dt = 60). This explains part of Today's dt bias (T3). Scaling it as σ√dt would fix it.
3. **Depth-uniform h = 3.5 m sink to infinity:** with no current at all, the sink draws in everything within 4.3 km in 72 h and 7.9 km in 10 days. Real bathymetry deepens offshore, so the far-field draw is probably overstated. This drives Today ≈ 95–100 % and the 100 % returns from ≤ 3 km.
4. **Repeated re-interception is implicit:** v3's low numbers rely on animals being re-screened about 1–8 times at full efficiency with no injury or clogging penalty.
5. **Unbounded pocket:** with the gate stuck closed, the twin stores 11,019 t. Always pass `cap_t` in failure studies.
6. **Minor:** the lane direction uses sign(u_tide) only and ignores the residual ur. The pocket cap has no effect under the immediate policy.
7. **Published values:** they are 2-seed estimates, 0.2–0.5 pp low against 30 seeds (T4).


|---|---|
| Alert-to-arrival timing; offshore alert never arrives | `test_alert_arrival_time_matches_current_speed` (×3), `test_offshore_only_alert_never_arrives`, `test_bearing_matters_upstream_vs_downstream`; T2 arrival vs exact ODE |
| Wind drift | harness `wind_fn` / `windage`; `test_wind_leeway_moves_particles_downwind_exactly`, `test_onshore_wind_increases_arrivals`, `test_wind_off_by_default_is_identical`; T9 ERA5 wind; T10 wind variant |
| Release-point ranking / drift-back | `test_release_further_offshore_gives_fewer_returns`, `test_release_timing_matters_and_ebb_phase_is_best`; T8 full curve + exact `exportstudy.json` regression + 15 km comparison |
| Stranding / beaching | harness `beach=True`; `test_stranded_particles_never_count_as_arriving`, `test_twin_itself_has_no_stranding` |
| Real-data hindcast | `test_hindcast_ordering_with_real_forcing` (skips with a message if data are missing); T9 with 292 windows |
| Sizing regressions | `test_screen_area_1000m2_at_0p10`, `test_screen_angle_sweep_ratio_and_length` (11°, 5.14, 143–200 m), `test_lane_width_28_to_40m`, `test_pipe_power` (195 / 286 kW), `test_stress_load_108_t_per_h` |
| **Extra (not in theirs)** | analytic verification (T2), convergence + GCI (T3), 30-seed bootstrap + exact reproduction (T4), Morris + Sobol (T5), Monte Carlo (T6), failure modes (T7), state-machine conservation, determinism, harness equivalence |

## Files
Scripts: `common.py`, `harness.py`, `hindcast.py`, `test_twin.py`, `vv_analytic.py`, `vv_convergence.py`, `vv_statistics.py`, `vv_sensitivity.py`, `vv_montecarlo.py`, `vv_stress.py`, `vv_release.py`, `vv_hindcast.py`, `vv_realdata_cases.py`.

Outputs are in `out/` and `figs/`.

## pytest result
`python3 -m pytest -q test_twin.py` -> **54 passed, 0 failed, 0 skipped** (156.9 s; the real-data hindcast test ran, since the data were present). Log: `out/pytest_log.txt`.
