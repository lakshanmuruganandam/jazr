"""T7 Stress / edge / failure-mode tests. N = 3000, each case = 4 tide phases x 2 seeds (same protocol as the
published v3 table). Release-only failure modes are modelled with the twin's own switches:
  gate stuck CLOSED, no overflow  -> policy='hold', hold_h=1e9 (pocket never empties; unbounded storage)
  gate stuck CLOSED, 100 t pocket -> overflow spills at the collector mouth (gate at x=+-600 m, y=150 m)
  pipe broken / gate stuck OPEN   -> immediate release at the collector mouth (x=+-600, y=150)
  screens rolled up (fail-open)   -> system on, eta_g = eta_r = 0 (should equal Today statistically)"""
import numpy as np, time, csv
from common import J, V3, TODAY, PH, pmap, save, OUT
SEEDS = (1, 2)
NEAR = dict(gate_x=600.0, gate_y=150.0)
CASES = [
 ("Today median", TODAY, None), ("v3 median", V3, None),
 ("Today, density x0.1", TODAY, dict(DENS=0.01)), ("Today, density x10", TODAY, dict(DENS=1.0)),
 ("v3, density x0.1", V3, dict(DENS=0.01)), ("v3, density x10", V3, dict(DENS=1.0)),
 ("v3 + 100 t pocket cap, density x1", dict(V3, cap_t=100), None), ("v3 + 100 t pocket cap, density x10", dict(V3, cap_t=100), dict(DENS=1.0)),
 ("Today, zero flow (U0=0, swim=0)", dict(TODAY, swim=0.0), dict(U0=0.0)), ("v3, zero flow (U0=0, swim=0)", dict(V3, swim=0.0), dict(U0=0.0)),
 ("Today, zero flow, swim 3.6 cm/s", TODAY, dict(U0=0.0)), ("v3, zero flow, swim 3.6 cm/s", V3, dict(U0=0.0)),
 ("Today, onshore 10 cm/s", dict(TODAY, vr=-0.10), None), ("v3, onshore 10 cm/s", dict(V3, vr=-0.10), None),
 ("Today, onshore 20 cm/s", dict(TODAY, vr=-0.20), None), ("v3, onshore 20 cm/s", dict(V3, vr=-0.20), None),
 ("Today, offshore 5 cm/s", dict(TODAY, vr=0.05), None), ("v3, offshore 5 cm/s", dict(V3, vr=0.05), None),
 ("v3, strong swimmer 15 cm/s", dict(V3, swim=0.15), None),
 ("v3, 30-day bloom", dict(V3, hours=720), None), ("Today, 30-day bloom", dict(TODAY, hours=720), None),
 ("v3, perfect screens (eta_g=eta_r=1)", dict(V3, eta_g=1.0, eta_r=1.0), None),
 ("v3, screens rolled up (eta_g=eta_r=0)", dict(V3, eta_g=0.0, eta_r=0.0), None),
 ("FAIL gate stuck closed, unbounded pocket", dict(V3, policy="hold", hold_h=1e9), None),
 ("FAIL gate stuck closed, 100 t pocket spills at collector", dict(V3, policy="hold", hold_h=1e9, cap_t=100, **NEAR), None),
 ("FAIL pipe broken: release at collector mouth", dict(V3, **NEAR), None),
 ("FAIL pipe broken + onshore 3 cm/s", dict(V3, vr=-0.03, **NEAR), None),
 ("Today, dt=300 s", dict(TODAY, dt=300.0), None), ("v3, dt=300 s", dict(V3, dt=300.0), None),
 ("Today, dt=600 s", dict(TODAY, dt=600.0), None), ("v3, dt=600 s", dict(V3, dt=600.0), None),
]

if __name__ == "__main__":
    t0 = time.time(); jobs = []
    for name, kw, patch in CASES:
        for p in PH:
            for s in SEEDS: jobs.append((dict(kw, N=3000, phase0=p, seed=s), patch))
    res = pmap(jobs); R = {}; rows = []
    n = len(PH)*len(SEEDS)
    for i, (name, kw, patch) in enumerate(CASES):
        rs = res[i*n:(i+1)*n]
        d = {k: float(np.mean([r[k] for r in rs])) for k in rs[0]}
        d["captured_runs"] = [r["captured_frac"] for r in rs]
        R[name] = d; rows.append([name, d["captured_frac"], d["captured_tonnes"], d["swarm_tonnes"], d["mean_handlings"], d["peak_held_tonnes"], d["still_held_frac"]])
        print(f"{name:58s} capt {d['captured_frac']*100:6.2f}%  {d['captured_tonnes']:8.0f}/{d['swarm_tonnes']:.0f} t  handled {d['mean_handlings']:.2f}  peak held {d['peak_held_tonnes']:8.0f} t  still held {d['still_held_frac']*100:5.1f}%", flush=True)
    # analytic expectation for zero flow, no swim: captured iff r0 <= sqrt(R_CAP^2 + 2 Q t /(pi h))
    rth = np.sqrt(J.R_CAP**2 + 2*J.Q*72*3600/(np.pi*J.H))
    fr = []
    for s in SEEDS:
        rng = np.random.default_rng(s); x = np.empty(0); y = np.empty(0)
        while x.size < 3000:
            xs = rng.uniform(*J.BAND_X, 6000); ys = rng.uniform(*J.BAND_Y, 6000); ok = np.hypot(xs, ys) > J.R_I+50
            x = np.concatenate([x, xs[ok]]); y = np.concatenate([y, ys[ok]])
        fr.append(float((np.hypot(x[:3000], y[:3000]) <= rth).mean()))
    R["_zero_flow_analytic_today"] = dict(r_capture_72h=float(rth), expected_frac=float(np.mean(fr)))
    print("zero-flow analytic Today fraction", np.mean(fr))
    save("t7_stress.json", R)
    with open(f"{OUT}/t7_stress.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["case", "captured_frac", "captured_t", "swarm_t", "mean_handlings", "peak_held_t", "still_held_frac"]); w.writerows(rows)
    print("runtime s", round(time.time()-t0))
