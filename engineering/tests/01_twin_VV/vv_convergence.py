"""T3 Convergence: timestep dt (30/60/120 s) at N=3000 and particle count N (500..6000) at dt=60 s.
Each point = 4 tide phases x 8 seeds (32 runs). Reports mean, standard error, observed order,
Richardson extrapolation and a GCI-style numerical uncertainty for the headline v3 numbers."""
import numpy as np, itertools, time, csv
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from common import J, V3, TODAY, CONDS, PH, pmap, save, FIGS, OUT
SEEDS = tuple(range(1, 9))
CFG = {"Today|median": TODAY, **{f"v3|{c}": dict(V3, **k) for c, k in CONDS.items()},
       "v3|median, swim=0 (no random walk)": dict(V3, swim=0.0)}

def batch(kw):
    return [(dict(kw, phase0=p, seed=s), None) for p in PH for s in SEEDS]

if __name__ == "__main__":
    t0 = time.time(); R = {"dt": {}, "N": {}}
    jobs, keys = [], []
    for name, kw in CFG.items():
        for dt in (30.0, 60.0, 120.0):
            b = batch(dict(kw, N=3000, dt=dt)); jobs += b; keys += [("dt", name, dt)]*len(b)
        for N in (500, 1000, 1500, 3000, 6000):
            b = batch(dict(kw, N=N, dt=60.0)); jobs += b; keys += [("N", name, N)]*len(b)
    res = pmap(jobs)
    acc = {}
    for k, r in zip(keys, res): acc.setdefault(k, []).append(r["captured_frac"])
    rows = []
    for (typ, name, v), c in acc.items():
        c = np.array(c)
        # per-seed mean over the 4 phases -> 8 replicate estimates of the 4-phase average
        reps = c.reshape(len(PH), len(SEEDS)).mean(0)
        d = dict(mean=float(c.mean()), se=float(reps.std(ddof=1)/np.sqrt(len(reps))),
                 run_sd=float(c.reshape(len(PH), len(SEEDS)).std(1, ddof=1).mean()), n_runs=len(c))
        R[typ].setdefault(name, {})[str(v)] = d
        rows.append([typ, name, v, d["mean"], d["se"], d["run_sd"]])
    # Richardson / GCI on dt (refinement ratio 2)
    R["gci"] = {}
    for name in CFG:
        f1, f2, f3 = (R["dt"][name][k]["mean"] for k in ("30.0", "60.0", "120.0"))
        e21, e32 = f2-f1, f3-f2
        p = float(np.log(abs(e32/e21))/np.log(2)) if e21 != 0 and e32/e21 > 0 else float("nan")
        p_use = p if np.isfinite(p) and 0.5 <= p <= 3 else 1.0
        f_ext = f1 - e21/(2**p_use-1)
        gci = 1.25*abs(e21)/(2**p_use-1)       # absolute uncertainty on the dt=30 result
        R["gci"][name] = dict(f30=f1, f60=f2, f120=f3, observed_order=p, order_used=p_use, f_extrap=float(f_ext),
                              num_unc_abs_at_dt60=float(abs(f2-f_ext)*1.25), gci_abs_dt30=float(gci),
                              se_seed_dt60=R["dt"][name]["60.0"]["se"])
        print(name, {k: (round(v, 4) if isinstance(v, float) else v) for k, v in R["gci"][name].items()})
    for name in CFG:
        print(name, "N:", {k: round(v["mean"]*100, 2) for k, v in R["N"][name].items()},
              "run_sd%:", {k: round(v["run_sd"]*100, 2) for k, v in R["N"][name].items()})
    save("t3_convergence.json", R)
    with open(f"{OUT}/t3_convergence.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["study", "config", "value", "mean_captured", "se_of_mean", "per_run_sd"]); w.writerows(rows)
    fig, ax = plt.subplots(1, 3, figsize=(15, 4.2))
    for name in CFG:
        if name.startswith("Today"): continue
        d = R["dt"][name]; xs = [30, 60, 120]
        ax[0].errorbar(xs, [d[str(float(x))]["mean"]*100 for x in xs], yerr=[1.96*d[str(float(x))]["se"]*100 for x in xs], marker="o", capsize=3, label=name)
        d = R["N"][name]; xs = [500, 1000, 1500, 3000, 6000]
        ax[1].errorbar(xs, [d[str(x)]["mean"]*100 for x in xs], yerr=[1.96*d[str(x)]["se"]*100 for x in xs], marker="o", capsize=3, label=name)
        ax[2].loglog(xs, [d[str(x)]["run_sd"]*100 for x in xs], marker="o", label=name)
    xs = np.array([500, 6000]); ax[2].loglog(xs, 0.5*np.sqrt(500/xs), "k--", label="slope -1/2")
    ax[0].set_xscale("log", base=2); ax[0].set_xlabel("dt (s)"); ax[0].set_ylabel("% reaching intake (95% CI)")
    ax[1].set_xscale("log"); ax[1].set_xlabel("particles N"); ax[1].set_ylabel("% reaching intake (95% CI)")
    ax[2].set_xlabel("particles N"); ax[2].set_ylabel("per-run SD (pct-points)")
    for a in ax: a.grid(alpha=.3)
    ax[0].legend(fontsize=7, frameon=False)
    fig.suptitle("T3 convergence (v3 configs; 4 tide phases x 8 seeds per point)"); fig.tight_layout()
    fig.savefig(f"{FIGS}/t3_convergence.png", dpi=130)
    print("runtime s", round(time.time()-t0))
