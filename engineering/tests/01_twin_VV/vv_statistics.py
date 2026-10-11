"""T4 Statistical: (i) exact reproduction of twin/out/v3study.json (seeds 1,2; N=3000) -> regression check;
(ii) seed variance with 30 seeds x 4 tide phases (N=3000) for every row of the v3 table;
(iii) bootstrap 95% CIs (resampling seeds) on the 4-phase mean; (iv) how far the published 2-seed estimate
can sit from the 30-seed mean; (v) probability the table's ranking holds across bootstrap resamples."""
import numpy as np, json, os, time, csv
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from common import J, V3_BASE, TODAY, CONDS, PH, pmap, save, FIGS, OUT, TWIN
SEEDS = tuple(range(1, 31)); B = 5000
CONFIGS = {"Gate (guard 0.9, outlet 3 km)": {}, "Gate, outlet 5 km": dict(gate_y=5000),
           "Gate + outer guide line (0.4)": dict(ring=True, eta_g=0.4),
           "Gate + outer guide (0.4) + outlet 5 km": dict(ring=True, eta_g=0.4, gate_y=5000),
           "Gate + outer guide (0.6) + outlet 5 km": dict(ring=True, eta_g=0.6, gate_y=5000)}
TODAYC = {"median": {}, "10-day bloom": dict(hours=240), "onshore 3 cm/s": dict(vr=-0.03)}

if __name__ == "__main__":
    t0 = time.time()
    pub = json.load(open(os.path.join(TWIN, "out", "v3study.json")))
    cfgs = {}
    for cn, ck in CONFIGS.items():
        for dn, dk in CONDS.items(): cfgs[f"{cn}|{dn}"] = dict(V3_BASE, **ck, **dk)
    for dn, dk in TODAYC.items(): cfgs[f"today|{dn}"] = dict(TODAY, **dk)
    jobs, keys = [], []
    for k, kw in cfgs.items():
        for p in PH:
            for s in SEEDS: jobs.append((dict(kw, N=3000, phase0=p, seed=s), None)); keys.append((k, p, s))
    res = pmap(jobs)
    M = {}
    for (k, p, s), r in zip(keys, res): M.setdefault(k, np.zeros((len(PH), len(SEEDS))))[PH.index(p), s-1] = r["captured_frac"]
    rng = np.random.default_rng(12345); R = {}; rows = []
    for k, m in M.items():
        rep = m.mean(0)                                  # 4-phase average per seed
        boot = rng.choice(rep, (B, rep.size)).mean(1)
        two = m[:, :2].mean()                            # = published protocol (seeds 1,2)
        pairs = np.array([m[:, [i, j]].mean() for i in range(30) for j in range(i+1, 30)])
        R[k] = dict(published=pub[k]["captured"], reproduced_seeds12=float(two),
                    exact_reproduction=bool(abs(two-pub[k]["captured"]) < 1e-12),
                    mean30=float(m.mean()), ci95=[float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))],
                    sd_seed_avg=float(rep.std(ddof=1)), sd_single_run=float(m.std(ddof=1)),
                    phase_means=[float(v) for v in m.mean(1)],
                    two_seed_estimates_P2_5_P97_5=[float(np.percentile(pairs, 2.5)), float(np.percentile(pairs, 97.5))],
                    published_inside_30seed_ci=bool(R.get(k) is None and np.percentile(boot, 2.5) <= pub[k]["captured"] <= np.percentile(boot, 97.5)))
        rows.append([k, pub[k]["captured"], two, m.mean(), *R[k]["ci95"], rep.std(ddof=1)])
        print(f"{k:55s} pub {pub[k]['captured']*100:6.2f}  rep {two*100:6.2f}  mean30 {m.mean()*100:6.2f}  CI [{R[k]['ci95'][0]*100:.2f},{R[k]['ci95'][1]*100:.2f}]", flush=True)
    # ranking robustness per condition (bootstrap jointly over seeds)
    order = ["today", *CONFIGS.keys()]
    rank = {}
    for dn in CONDS:
        names = [n for n in order if f"{n}|{dn}" in M]
        reps = np.array([M[f"{n}|{dn}"].mean(0) for n in names])
        idx = rng.integers(0, 30, (B, 30))
        bm = reps[:, idx].mean(2)                       # names x B
        v3 = names.index("Gate + outer guide (0.4) + outlet 5 km")
        rank[dn] = {f"P(v3 < {n})": float((bm[v3] < bm[i]).mean()) for i, n in enumerate(names) if i != v3}
        print(dn, rank[dn])
    R["_ranking"] = rank
    save("t4_statistics.json", R)
    with open(f"{OUT}/t4_statistics.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["config|condition", "published", "reproduced_seeds_1_2", "mean_30_seeds", "ci95_lo", "ci95_hi", "sd_of_4phase_avg"]); w.writerows(rows)
    np.savez(f"{OUT}/t4_raw_matrix.npz", **{k.replace("|", "__"): v for k, v in M.items()})
    hk = [f"Gate + outer guide (0.4) + outlet 5 km|{c}" for c in CONDS]
    fig, ax = plt.subplots(figsize=(8, 4.2))
    for i, k in enumerate(hk):
        reps = M[k].mean(0)*100
        ax.scatter(np.full(30, i)+np.random.default_rng(i).uniform(-.12, .12, 30), reps, s=10, alpha=.5, color="#6b7280")
        ax.errorbar(i+.25, R[k]["mean30"]*100, yerr=[[R[k]["mean30"]*100-R[k]["ci95"][0]*100], [R[k]["ci95"][1]*100-R[k]["mean30"]*100]], fmt="o", color="#2563eb", capsize=4, label="30-seed mean, 95% bootstrap CI" if i == 0 else None)
        ax.plot(i+.25, R[k]["published"]*100, "x", color="#dc2626", ms=9, label="published (2 seeds)" if i == 0 else None)
    ax.set_xticks(range(4)); ax.set_xticklabels(list(CONDS)); ax.set_ylabel("% of swarm reaching intake")
    ax.set_title("T4 v3 headline numbers: seed spread (grey = per-seed 4-phase average)"); ax.legend(frameon=False); ax.grid(alpha=.3, axis="y")
    fig.tight_layout(); fig.savefig(f"{FIGS}/t4_headline_ci.png", dpi=130)
    print("runtime s", round(time.time()-t0))
