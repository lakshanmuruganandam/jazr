"""
run_twin.py - plant-scale twin (../../../twin/jazr_twin.py, imported unchanged) with the improved eta_r values.
*** SIMULATED - reduced-order twin, not validated. ***
Settings (as instructed): system=True, ring=False, policy="immediate", gate_x=10000, gate_y=3000, vr=-0.025,
hours 72 and 240; 4 tide phases x 2 seeds, N=1500 (same averaging as twin/v4study.avg).
Writes results/twin_eta.csv
"""
import os, sys, csv, json
import numpy as np
import multiprocessing as mp
TWIN = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "twin"))
sys.path.insert(0, TWIN)
sys.dont_write_bytecode = True
import jazr_twin as J

RES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")
PH = (0, np.pi / 2, np.pi, 3 * np.pi / 2); SEEDS = (1, 2)
BASE = dict(system=True, ring=False, policy="immediate", gate_x=10000, gate_y=3000, vr=-0.025)


def one(a):
    kw, ph, sd = a
    return J.simulate(N=1500, phase0=ph, seed=sd, **kw)[0]["captured_frac"]


def cases():
    vt = {}
    p = os.path.join(RES, "vt_levers.csv")
    if os.path.exists(p):
        for r in csv.DictReader(open(p)):
            vt[r["config"]] = r
    C = [("Today (no JAZR)", None)]
    def g(cfg, col="eta_mean"):
        return float(vt[cfg][col]) if cfg in vt else None
    named = [("v4.1 (tank: 4 entrances, 20%, batch)", g("v4.1 (4 entr, 20%, mu 0.4)")),
             ("v4.1 published 0.73", 0.73), ("v4.1 published 0.82 (35%)", 0.82),
             ("two screens in series (tank)", g("two screens in series")),
             ("best combo (tank, point)", g("+ mu 0.1 coating")),
             ("best combo (tank, 95% lower bound)", g("+ mu 0.1 coating", "eta_cp_lo")),
             ("best + series (tank, 95% lower bound)", g("best + two screens in series", "eta_cp_lo")),
             ("best | belt fault (tank)", g("best | belt stopped (fault)")),
             ("best | rheotactic 10 cm/s (tank)", g("best | rheotactic 10 cm/s"))]
    C += [(n, v) for n, v in named if v is not None]
    C += [(f"sweep eta_r={e}", e) for e in (0.5, 0.7, 0.8, 0.9, 0.95, 0.98, 0.99, 0.995, 1.0)]
    return C


if __name__ == "__main__":
    rows = []
    with mp.get_context("fork").Pool(10) as pool:
        for name, eta in cases():
            for hrs in (72, 240):
                kw = dict(system=False, hours=hrs, vr=-0.025) if eta is None else dict(BASE, eta_r=min(eta, 1.0), hours=hrs)
                r = pool.map(one, [(kw, ph, sd) for ph in PH for sd in SEEDS])
                rows.append(dict(case=name, eta_r=("" if eta is None else round(eta, 4)), hours=hrs,
                                 pct_reaching_plant=round(100 * np.mean(r), 2), min_pct=round(100 * min(r), 2),
                                 max_pct=round(100 * max(r), 2), runs=len(r),
                                 data_type="SIMULATED twin (reduced-order, not validated)"))
                print(rows[-1], flush=True)
    with open(os.path.join(RES, "twin_eta.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
