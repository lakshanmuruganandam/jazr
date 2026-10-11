"""
run_vt.py - eta_r lever study in the extended VIRTUAL TANK (1:20 Froude tank analogue).
*** SIMULATED - model-based, not physical evidence. ***
Each config: >= 10 seeds x 30 bells (stage-1 180 s, early stop when every remaining bell is still > 10 s).
Writes results/vt_runs.jsonl (cache, one line per run) and results/vt_levers.csv (aggregated with 95% CIs).
Usage: python3 run_vt.py [group ...]
"""
import os, sys, json, time
import numpy as np
from dataclasses import replace, asdict
import multiprocessing as mp
from scipy import stats as sst
from vt_ext import ParamsX, SimX, metrics, design_rate_per_min, VSCALE, BYPASS, ACTIVE

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "results")
CACHE = os.path.join(RES, "vt_runs.jsonl")
V41 = dict(n_mid_slots=3, bypass_frac=0.20)          # v4.1 tank analogue: 4 entrances, 20% entrance flow
SEEDS = 10
CM = 0.01 / VSCALE                                   # 1 cm/s prototype -> tank m/s


def one(job):
    kw = dict(V41, **job.get("kw", {}))
    P = replace(ParamsX(), **kw)
    seed = job["seed"]
    swim = job.get("swim", 0.0) * CM
    s = SimX(P, seed, swim_mode=job.get("swim_mode", "random"), cue_speed=job.get("cue", 0.0) * CM)
    dr = job.get("d_range", (0.04, 0.06))
    t0 = time.time()
    if job.get("density"):
        rate = design_rate_per_min(job["density"]) / 60.0
        acc = [0.0]
        def cb(sim):
            if sim.t < 120.0:
                acc[0] += rate * P.dt
                if acc[0] >= 1:
                    nn = int(acc[0]); acc[0] -= nn
                    sim.release_bells(nn, x_range=(0.03, 0.10), d_range=dr, swim=swim)
        s.run(240.0, early_stop=False, callback=cb)
    else:
        s.release_bells(30, d_range=dr, swim=swim)
        s.run(180.0)
    m = metrics(s)
    m["ent"] = s.entrance_counts().tolist()
    if job.get("series") and m["n"] > 0:
        # bells left on screen 1 are released (relief / cycling) onto an identical catch screen 2
        left = np.nonzero(s.status == ACTIVE)[0]
        m["stage1_eta"] = m["eta"]
        if len(left):
            s2 = SimX(P, seed + 7777, swim_mode=job.get("swim_mode", "random"))
            s2.add(np.column_stack([np.random.default_rng(seed).uniform(0.03, 0.18, len(left)),
                                    np.random.default_rng(seed + 1).uniform(P.y_lo + 0.03, P.y_up - 0.03, len(left))]),
                   s.pos[left, 2], s.d[left], s.rho[left] - 1000.0, swim=s.swim[left])
            s2.run(180.0)
            m2 = metrics(s2)
            m["bypass"] += m2["bypass"]; m["stuck"] = m2["stuck"]
            m["eta"] = m["bypass"] / m["n"]; m["jam"] = m2["stuck"] / m["n"]
            m["contacts"] = float((s.ncont.sum() + s2.ncont.sum()) / m["n"])
            m["tface"] = float((s.tface.sum() + s2.tface.sum()) / m["n"])
            m["stage2_eta"] = m2["eta"]
    m.update(tag=job["tag"], group=job["group"], seed=seed, cpu=round(time.time() - t0, 1))
    return m


def jobs_for(group):
    J = []
    def add(tag, n=SEEDS, **kw):
        for sd in range(n):
            J.append(dict(group=group, tag=tag, seed=1000 + sd, **kw))
    if group == "L1_entrance_flow":
        add("3% (no dewatering: lift-limited)", kw=dict(bypass_frac=0.03))
        for f in (0.10, 0.20, 0.35, 0.50):
            add(f"{int(f*100)}% with dewatering", kw=dict(bypass_frac=f))
    elif group == "L2_apex_scoop":
        add("no apex entrance (mid only)", kw=dict(apex=False))
        add("apex, mouth 6 cm (=1.2 m)", kw=dict(gap_w=0.06))
        add("apex, mouth 10 cm (=2 m)", kw=dict(gap_w=0.10))
        add("apex, mouth 13 cm (=2.6 m)", kw=dict(gap_w=0.13))
        add("apex share 50%", kw=dict(apex_share=0.5))
        add("apex share 80%", kw=dict(apex_share=0.8))
        add("flared mid mouths x1.6", kw=dict(flare=1.6))
        add("flared mid mouths x2.0", kw=dict(flare=2.0))
    elif group == "L3_conveyor":
        for b in (0.0, 0.25, 0.5, 1.0):
            add(f"belt {b:.2f} x sweep", kw=dict(belt_frac=b))
    elif group == "L4_series":
        add("single screen", kw={})
        add("two screens in series", kw={}, series=True)
    elif group == "L5_friction":
        for mu in (0.05, 0.1, 0.2, 0.4):
            add(f"mu {mu}", kw=dict(mu_f=mu))
    elif group == "L6_baffles":
        add("no baffles", kw={})
        add("graded baffles (downstream 40%)", kw=dict(baffle=True))
    elif group == "L7_walljet":
        for j in (0.0, 0.1, 0.25, 0.5):
            add(f"wall jet {j:.2f} x sweep", kw=dict(jet_frac=j))
    elif group == "L8_size_swim":
        add("tank surrogate 4-6 cm (b/D~1.2)", kw={})
        add("bells 2-3 cm (b/D~2.4)", kw={}, d_range=(0.02, 0.03))
        add("geometric 6.5-12 cm real (0.33-0.6 cm tank, 1 mm mesh)", kw=dict(mesh_mm=1.0), d_range=(0.00325, 0.006))
        for sw in (3.6, 10.0):
            add(f"swim {sw} cm/s random", kw={}, swim=sw)
            add(f"swim {sw} cm/s rheotactic (worst)", kw={}, swim=sw, swim_mode="rheo")
    elif group == "L9_density":
        add("0.3 /m3 continuous feed", n=5, kw={}, density=0.3)
        add("1.0 /m3 continuous feed", n=5, kw={}, density=1.0)
    elif group == "CUE":     # HYPOTHETICAL behavioural cue near the apex
        for base_tag, kw in (("v4.1", {}), ("best", BEST_PRACTICAL)):
            for c in (-3, -2, -1, 0, 1, 2, 3):
                add(f"{base_tag} | cue {c:+d} cm/s", kw=kw, cue=float(c))
    elif group == "COMBO":
        steps = [("v4.1 (4 entr, 20%, mu 0.4)", {}),
                 ("+ 35% entrance flow", dict(bypass_frac=0.35)),
                 ("+ belt 0.5", dict(bypass_frac=0.35, belt_frac=0.5)),
                 ("+ flared mouths", dict(bypass_frac=0.35, belt_frac=0.5, flare=1.6)),
                 ("+ graded baffles", dict(bypass_frac=0.35, belt_frac=0.5, flare=1.6, baffle=True)),
                 ("+ wall jet 0.25", dict(bypass_frac=0.35, belt_frac=0.5, flare=1.6, baffle=True, jet_frac=0.25)),
                 ("+ mu 0.1 coating", dict(BEST_PRACTICAL, apex_share=-1.0)),
                 ("+ apex share 50% (= BEST)", dict(BEST_PRACTICAL))]
        for t, kw in steps:
            add(t, n=30, kw=kw)
        add("best + two screens in series", n=30, kw=BEST_PRACTICAL, series=True)
        add("belt 1.0 + 35% (minimal)", n=30, kw=dict(bypass_frac=0.35, belt_frac=1.0))
        add("belt 0.5 + 20% (cheap)", n=30, kw=dict(belt_frac=0.5))
    elif group == "NOBELT":   # same stack without the conveyor (redundancy if the belt is not built / fails)
        steps = [("35% + flared", dict(bypass_frac=0.35, flare=1.6)),
                 ("35% + flared + baffles", dict(bypass_frac=0.35, flare=1.6, baffle=True)),
                 ("35% + flared + baffles + jet 0.25", dict(bypass_frac=0.35, flare=1.6, baffle=True, jet_frac=0.25)),
                 ("35% + flared + baffles + jet + mu 0.1 (no belt)", dict(bypass_frac=0.35, flare=1.6, baffle=True, jet_frac=0.25, mu_f=0.1)),
                 ("35% + baffles + mu 0.1", dict(bypass_frac=0.35, baffle=True, mu_f=0.1)),
                 ("50% + flared x2 + baffles + mu 0.1", dict(bypass_frac=0.5, flare=2.0, baffle=True, mu_f=0.1))]
        for t, kw in steps:
            add(t, n=30, kw=kw)
        add("no-belt best + apex share 50%", n=30, kw=dict(bypass_frac=0.35, flare=1.6, baffle=True, jet_frac=0.25, mu_f=0.1, apex_share=0.5))
        add("no-belt best + two screens in series", n=30, kw=dict(bypass_frac=0.35, flare=1.6, baffle=True, jet_frac=0.25, mu_f=0.1), series=True)
    elif group == "STRESS":   # best combo under worst-case conditions
        add("best | rheotactic 10 cm/s", kw=BEST_PRACTICAL, swim=10.0, swim_mode="rheo")
        add("best | mu 0.4 (coating worn)", kw=dict(BEST_PRACTICAL, mu_f=0.4))
        add("best | fouled bay 3", kw=dict(BEST_PRACTICAL, foul_bay=3))
        add("v4.1 | fouled bay 3", kw=dict(foul_bay=3))
        add("best | 1.0 /m3 feed", n=5, kw=BEST_PRACTICAL, density=1.0)
        add("best | small bells 2-3 cm", kw=BEST_PRACTICAL, d_range=(0.02, 0.03))
        add("best | belt stopped (fault)", kw=dict(BEST_PRACTICAL, belt_frac=0.0))
    return J


BEST_PRACTICAL = dict(bypass_frac=0.35, belt_frac=0.5, flare=1.6, baffle=True, jet_frac=0.25, mu_f=0.1, apex_share=0.5)
ALL = ["L1_entrance_flow", "L2_apex_scoop", "L3_conveyor", "L4_series", "L5_friction", "L6_baffles",
       "L7_walljet", "L8_size_swim", "L9_density", "COMBO", "NOBELT", "STRESS", "CUE"]


def ci(x):
    x = np.asarray(x, float)
    if len(x) < 2:
        return x.mean(), x.mean(), x.mean()
    h = sst.t.ppf(0.975, len(x) - 1) * x.std(ddof=1) / np.sqrt(len(x))
    return x.mean(), max(0.0, x.mean() - h), min(1.0, x.mean() + h)


def aggregate():
    R = [json.loads(l) for l in open(CACHE)]
    by = {}
    for r in R:
        by.setdefault((r["group"], r["tag"]), []).append(r)
    rows = []
    for (g, t), v in by.items():
        eta = [r["eta"] for r in v]
        m, lo, hi = ci(eta)
        k = sum(r["bypass"] for r in v); n = sum(r["n"] for r in v)
        cp_lo = sst.beta.ppf(0.025, k, n - k + 1) if k > 0 else 0.0
        cp_hi = sst.beta.ppf(0.975, k + 1, n - k) if k < n else 1.0
        rows.append(dict(group=g, config=t, seeds=len(v), bells=n, eta_mean=m, eta_ci_lo=lo, eta_ci_hi=hi,
                         eta_pooled=k / n, eta_cp_lo=cp_lo, eta_cp_hi=cp_hi,
                         jam_rate=np.mean([r["jam"] for r in v]),
                         contacts_per_bell=np.mean([r["contacts"] for r in v]),
                         t_face_s_tank=np.mean([r["tface"] for r in v]),
                         t_face_s_proto=np.mean([r["tface"] for r in v]) * VSCALE,
                         stage2_eta=np.nanmean([r.get("stage2_eta", np.nan) for r in v]) if any("stage2_eta" in r for r in v) else "",
                         data_type="SIMULATED virtual tank (1:20) - model-based"))
    order = {g: i for i, g in enumerate(ALL)}
    rows.sort(key=lambda r: (order.get(r["group"], 99)))
    import csv
    with open(os.path.join(RES, "vt_levers.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader()
        for r in rows:
            w.writerow({k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items()})
    return rows


if __name__ == "__main__":
    groups = sys.argv[1:] or ALL
    if groups == ["agg"]:
        for r in aggregate():
            print(f"{r['group']:17s} {r['config']:45s} eta {r['eta_mean']:.3f} [{r['eta_ci_lo']:.3f}-{r['eta_ci_hi']:.3f}] "
                  f"CP>={r['eta_cp_lo']:.3f} jam {r['jam_rate']:.3f} contacts {r['contacts_per_bell']:.2f} tface {r['t_face_s_proto']:.0f}s")
        sys.exit()
    done = set()
    if os.path.exists(CACHE):
        for l in open(CACHE):
            r = json.loads(l); done.add((r["group"], r["tag"], r["seed"]))
    J = [j for g in groups for j in jobs_for(g) if (j["group"], j["tag"], j["seed"]) not in done]
    J.sort(key=lambda j: -(j.get("density") or 0))
    print(len(J), "runs", flush=True)
    t0 = time.time()
    with mp.get_context("fork").Pool(10) as pool:
        for k, r in enumerate(pool.imap_unordered(one, J)):
            with open(CACHE, "a") as f:
                f.write(json.dumps(r) + "\n")
            if k % 20 == 0:
                print(k, r["tag"], round(r["eta"], 2), round(time.time() - t0), flush=True)
    aggregate()
    print("wall", round(time.time() - t0))
