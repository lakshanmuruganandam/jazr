"""T6 Monte Carlo uncertainty propagation. 500 input samples, each input drawn UNIFORMLY from the T5 ranges
(an assumption: no data to justify any other distribution), tide phase at alert ~ U(0, 2pi), one seed per sample.
The SAME sample (inputs, phase, seed) is run for Today and for v3 (paired). N = 1500 particles (stated).
Today ignores eta_g, eta_r, gate_y (system off). Output: P10/P50/P90 of % reaching intake, and of the
paired reduction."""
import numpy as np, time, csv
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from common import J, V3, TODAY, pmap, save, FIGS, OUT
from vv_sensitivity import FACT
NS = 500; NP = 1500

if __name__ == "__main__":
    t0 = time.time(); rng = np.random.default_rng(2026)
    U = rng.random((NS, len(FACT))); phase = rng.uniform(0, 2*np.pi, NS); seeds = np.arange(5000, 5000+NS)
    jobs = []
    for base in (TODAY, V3):
        for u, p, s in zip(U, phase, seeds):
            kw = dict(base, N=NP, seed=int(s), phase0=float(p)); patch = {}
            for (n, lo, hi), x in zip(FACT, u):
                v = lo + x*(hi-lo)
                if n == "U0": patch["U0"] = float(v)
                elif n == "hours": kw["hours"] = float(v)
                elif base is V3 or n in ("swim", "vr", "ur"): kw[n] = float(v)
            jobs.append((kw, patch))
    res = pmap(jobs)
    yt = np.array([r["captured_frac"] for r in res[:NS]])*100; yv = np.array([r["captured_frac"] for r in res[NS:]])*100
    red = yt - yv; ratio = yv/np.maximum(yt, 1e-9)
    def pct(a): return {f"P{q}": float(np.percentile(a, q)) for q in (5, 10, 50, 90, 95)} | {"mean": float(a.mean())}
    R = dict(today=pct(yt), v3=pct(yv), reduction_pctpts=pct(red), v3_over_today=pct(ratio),
             P_v3_below_10pct=float((yv < 10).mean()), P_v3_below_20pct=float((yv < 20).mean()),
             P_v3_above_30pct=float((yv > 30).mean()), P_v3_lower_than_today=float((yv < yt).mean()),
             spearman_v3_vs_inputs={n: float(np.corrcoef(np.argsort(np.argsort(U[:, i])), np.argsort(np.argsort(yv)))[0, 1]) for i, (n, _, _) in enumerate(FACT)},
             settings=dict(samples=NS, N_particles=NP, distribution="uniform on ranges", ranges={n: [lo, hi] for n, lo, hi in FACT}))
    print({k: (v if not isinstance(v, dict) else {a: round(b, 2) for a, b in v.items()}) for k, v in R.items() if k != "settings"})
    save("t6_montecarlo.json", R)
    with open(f"{OUT}/t6_montecarlo_samples.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow([n for n, _, _ in FACT] + ["phase0", "seed", "today_pct", "v3_pct"])
        for u, p, s, a, b in zip(U, phase, seeds, yt, yv): w.writerow([lo+x*(hi-lo) for x, (n, lo, hi) in zip(u, FACT)] + [p, s, a, b])
    fig, ax = plt.subplots(1, 2, figsize=(12, 4.2))
    bins = np.linspace(0, 100, 51)
    ax[0].hist(yt, bins, color="#9ca3af", label="Today"); ax[0].hist(yv, bins, color="#2563eb", alpha=.85, label="v3")
    for a, c in ((yt, "#4b5563"), (yv, "#1e40af")):
        for q in (10, 50, 90): ax[0].axvline(np.percentile(a, q), color=c, ls=":" if q != 50 else "-", lw=1)
    ax[0].set_xlabel("% of swarm reaching intake"); ax[0].set_ylabel("samples"); ax[0].legend(frameon=False)
    ax[0].set_title(f"T6 Monte Carlo ({NS} samples, uniform input ranges)")
    s = np.sort(yv); ax[1].plot(s, np.arange(1, NS+1)/NS, color="#2563eb", label="v3"); s = np.sort(yt); ax[1].plot(s, np.arange(1, NS+1)/NS, color="#6b7280", label="Today")
    ax[1].set_xlabel("% reaching intake"); ax[1].set_ylabel("cumulative probability"); ax[1].grid(alpha=.3); ax[1].legend(frameon=False)
    fig.tight_layout(); fig.savefig(f"{FIGS}/t6_montecarlo.png", dpi=130)
    print("runtime s", round(time.time()-t0))
