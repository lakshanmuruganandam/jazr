"""T10 Real-data corrected cases (from TESTS/00_data/README.md): onshore residual 2.5 cm/s is TYPICAL,
5-6 cm/s is the STRESS case, plus a wind-drift variant: 2% leeway x 2 m/s onshore wind = 4 cm/s extra onshore
(added through the harness wind term, on top of the 2.5 cm/s current). Today vs v3 (ring=True, eta_g=0.4,
eta_r=0.9, gate_x=1200, gate_y=5000, policy immediate). N = 1500, 4 tide phases x 2 seeds, 72 h and 240 h."""
import numpy as np, time, csv
from multiprocessing import Pool
from common import V3, TODAY, PH, save, OUT
from harness import hrun

class Wind:                       # picklable constant onshore wind (twin -y is onshore)
    def __init__(self, w): self.w = w
    def __call__(self, t): return (0.0, -self.w)

CASES = [("onshore 2.5 cm/s (typical)", dict(vr=-0.025)), ("onshore 5 cm/s (stress)", dict(vr=-0.05)),
         ("onshore 6 cm/s (stress)", dict(vr=-0.06)),
         ("onshore 2.5 cm/s + wind 2% x 2 m/s (=4 cm/s)", dict(vr=-0.025, wind_fn=Wind(2.0), windage=0.02))]

if __name__ == "__main__":
    t0 = time.time(); jobs, keys = [], []
    for hrs in (72, 240):
        for cn, ck in CASES:
            for sn, sk in (("Today", TODAY), ("v3", V3)):
                for p in PH:
                    for s in (1, 2):
                        jobs.append(dict(sk, **ck, N=1500, hours=hrs, phase0=p, seed=s)); keys.append((hrs, cn, sn))
    with Pool() as pool: res = pool.map(hrun, jobs, chunksize=2)
    acc = {}
    for k, r in zip(keys, res): acc.setdefault(k, []).append(r)
    R = {}; rows = []
    for (h, cn, sn), rs in acc.items():
        c = [r["captured_frac"] for r in rs]
        d = dict(captured=float(np.mean(c)), lo=float(min(c)), hi=float(max(c)), handlings=float(np.mean([r["mean_handlings"] for r in rs])))
        R[f"{sn}|{cn}|{h}h"] = d; rows.append([sn, cn, h, d["captured"], d["lo"], d["hi"], d["handlings"]])
        print(f"{sn:6s} {cn:46s} {h:4d} h: {d['captured']*100:6.2f}% [{d['lo']*100:.1f}-{d['hi']*100:.1f}] handled {d['handlings']:.2f}", flush=True)
    save("t10_realdata_cases.json", R)
    with open(f"{OUT}/t10_realdata_cases.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["config", "case", "hours", "captured_frac", "min_run", "max_run", "mean_handlings"]); w.writerows(rows)
    print("runtime s", round(time.time()-t0))
