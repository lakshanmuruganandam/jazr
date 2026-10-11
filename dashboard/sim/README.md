# JAZR live Simulation module (`sim/`)

**Model-based simulation (toy twin, validated against our Python model, not field data).**

Standalone, embeddable module: open `index.html` directly (file:// works through a Blob-worker fallback) or embed with
`<iframe src="sim/index.html">`. When embedded, it posts `{source:'jazr-sim', hour, jazrPct, todayPct, params}` to the parent.

| File | Role |
|---|---|
| `index.html` | ISA-101 dark HMI layout, controls, chart containers (ECharts 5.5.0 pinned, cdnjs) |
| `app.js` | UI, canvas map renderer, charts, Monte Carlo fan, sweeps, CSV/PNG export |
| `twin.worker.js` | JS port of `twin/jazr_twin.py` (Web Worker; also `require()`-able in Node) |
| `validate.js` | Headless Node validation vs `twin/out/*.json` → `validation.json`, `validation.txt` |
| `shots/` | Headless-Chrome screenshots (0 console errors) |

## Physics (same as the Python twin)
Coast y = 0 reflecting · half-plane sink u = −Q/(πrh), Q = 400 m³/s, h = 3.5 m · M2 tide U₀ = 0.117 sin(ωt), T = 12.42 h ·
residual ur, vr · optional wind drift (1% of wind, assumption) · random-heading swim (3.6 or 10 cm/s) with heading noise N(0, 0.3) per 60 s step ·
optional outer ring η_g at r = 500 m · inner screen η_r on inward crossing of r = 120 m → pocket (x = ±600 m, side = tide direction) ·
release policies immediate (600, 150) / near (1.2 km, 5 km out) / far (10 km alongshore, 3 km out) / auto (far if vr < 0) ·
capture (leak) at r < 60 m · 0.33 kg per animal · seeded RNG (sfc32 + Box–Muller; streams differ from NumPy, statistics match).
Survival: engineering budget 0.978 (TESTS/10_mechanisms/survival_budget.csv) and conservative Monte Carlo 0.76 (0.68–0.85), design target ≥ 0.95, applied per handling (s^k).

## Validation (`node validate.js`)
Protocol identical to the Python studies: N = 1500, 4 tide phases × 2 seeds, mean of 8 runs; tolerance ±3 pp.
Swim 3.6 cm/s, no outer line unless stated; vr −2.5 = 2.5 cm/s onshore.

| Case | Reference | Python % | JS % | Δ pp | JS range | |
|---|---|---|---|---|---|---|
| Today, onshore 2.5 cm/s, 72 h | v4study | 97.0 | 96.9 | -0.1 | 94.0–99.2 | PASS |
| Today, no residual, 72 h | v3study | 95.5 | 95.4 | -0.1 | 92.0–98.3 | PASS |
| Today, onshore 3 cm/s, 72 h | v3study | 96.8 | 96.9 | +0.0 | 94.0–99.2 | PASS |
| Today, 10-day bloom | v3study | 100.0 | 100.0 | +0.0 | 100.0–100.0 | PASS |
| FAR release (10 km, 3 km out), eta_r 0.9, vr -2.5, 240 h | v5_far | 10.6 | 10.1 | -0.6 | 9.3–10.9 | PASS |
| FAR release, + ur 1 cm/s, 240 h | v5_far | 12.9 | 12.8 | -0.1 | 10.9–14.7 | PASS |
| NEAR release-only (5 km), eta_r 0.9, vr -2.5, 240 h | v5_noharm | 49.9 | 50.2 | +0.2 | 48.7–52.9 | PASS |
| NEAR release-only (5 km), 72 h | v4b | 17.9 | 17.8 | -0.2 | 16.2–18.7 | PASS |
| Offshore 10 km release, 240 h | v5_far | 28.1 | 26.6 | -1.4 | 24.6–27.8 | PASS |
| Alongshore 5 km release, 240 h | v5_far | 27.1 | 26.8 | -0.3 | 25.2–28.8 | PASS |
| Hold-unlimited (removed recover), eta_r 0.9, 240 h | v5_noharm | 10.4 | 10.0 | -0.5 | 9.2–10.7 | PASS |
| Hold (removed recover), eta_r 0.7, 240 h | v4b | 30.0 | 29.8 | -0.3 | 28.5–30.9 | PASS |
| Outer line 0.4 + near release, vr -2.5, 72 h | v4study | 11.3 | 10.6 | -0.6 | 8.9–12.2 | PASS |
| Gate 3 km (x 1.2 km), no residual, 72 h | v3study | 14.9 | 14.9 | +0.1 | 13.5–16.4 | PASS |
| FAR release, eta_r 0.99, vr -2.5, 72 h | expected (coordinator, no JSON) | 1.1 | 0.9 | -0.2 | 0.5–1.4 | PASS |
| FAR release, eta_r 0.996, vr -2.5, 72 h | expected (coordinator, no JSON) | 0.4 | 0.4 | +0.0 | 0.1–0.7 | PASS |

Worst |Δ| = **1.4 pp**. "Hold" reproduces the removed lethal *recover* option for validation only (not in the UI).
The last two rows are coordinator-supplied expected values (no Python JSON on disk).

## URL parameters
`?eta=0.953&policy=far&days=10&vr=2.5&ur=0&wind=0&swim=0.036&N=2000&seed=1&dens=0.1&speed=40&zoom=12000&sbs=1&ring=1&mc=1&sweep=1`
