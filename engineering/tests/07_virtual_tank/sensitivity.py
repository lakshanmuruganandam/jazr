"""Calibration / uncertainty: how eta_r(11 deg) moves over plausible ranges of the unknown parameters.
SIMULATED virtual tank - not physical evidence."""
import json, os
import numpy as np
from dataclasses import replace
import multiprocessing as _mp
Pool = _mp.get_context("fork").Pool
from vtank import Params, Sim, LABEL

HERE = os.path.dirname(os.path.abspath(__file__))
NOM = Params()
SEEDS = 3
T_RUN = 120.0   # s; bells resolve in <60 s (machine was heavily shared, so runs were shortened)
CACHE = os.path.join(HERE, 'results', '_sens_cache.jsonl')

RANGES = {   # (low, nominal, high) - plausible ranges, chosen before running
    "E": (1000.0, 5000.0, 30000.0),          # bell stiffness, Pa (soft gel .. agar)
    "mu_f": (0.1, 0.4, 1.0),                  # bell-mesh friction
    "adhesion": (0.0, 0.0, 3.0),              # mucus adhesion, Pa
    "cd_mult": (0.6, 1.0, 1.6),               # drag coefficient multiplier
    "turb_I": (0.03, 0.10, 0.25),             # tank turbulence intensity
    "ell_s": (0.01, 0.05, 0.3),               # screen resistance length
    "rho_sd_scale": (0.1, 1.0, 2.0),          # density scatter of surrogates
}
BYPASS = [0.03, 0.10, 0.20, 0.35]


def job(a):
    P = replace(NOM, **a["kw"])
    s = Sim(P, a["seed"]); s.release_bells(30, d_range=a.get("d_range", (0.04, 0.06))); s.run(T_RUN)
    r = s.summary()
    return a["tag"], r["bypass"] / 30, r["stuck"] / 30, a["seed"]


def main():
    jobs = []
    for p, (lo, nom, hi) in RANGES.items():
        for lab, v in (("low", lo), ("high", hi)):
            if v == nom:
                continue
            for sd in range(SEEDS):
                jobs.append(dict(tag=f"OAT|{p}|{lab}|{v}", kw={p: v}, seed=30000 + sd))
    for sd in range(SEEDS):
        jobs.append(dict(tag="OAT|nominal|nom|0", kw={}, seed=30000 + sd))
    jobs = sorted(jobs, key=lambda j: {"BYP": 0, "DES": 1, "OAT": 2}.get(j["tag"][:3], 3))
    for b in BYPASS:
        for th in (11,):
            for sd in range(SEEDS):
                jobs.append(dict(tag=f"BYP|{th}|{b}", kw=dict(bypass_frac=b, theta_deg=th), seed=31000 + sd))
    # design scans (not uncertainties): geometrically-scaled bells (30 cm / 20 = 1.5 cm) and wider entrance
    for tag, kw, dr in (("DES|bells 1.5-2.5 cm", {}, (0.015, 0.025)), ("DES|bells 1.5-2.5 cm, bypass 3%", dict(bypass_frac=0.03), (0.015, 0.025)),
                        ("DES|entrance 10 cm", dict(gap_w=0.10), (0.04, 0.06)), ("DES|entrance 10 cm, bypass 3%", dict(gap_w=0.10, bypass_frac=0.03), (0.04, 0.06)),
                        ("DES|4 entrances, bypass 20%", dict(n_mid_slots=3, bypass_frac=0.2), (0.04, 0.06)),
                        ("DES|bells 1.5-2.5 cm, 20 deg", dict(theta_deg=20), (0.015, 0.025))):
        for sd in range(SEEDS):
            jobs.append(dict(tag=tag, kw=kw, seed=33000 + sd, d_range=dr))
    # Latin hypercube over all ranges (log for E, ell_s, adhesion+0.1)
    rng = np.random.default_rng(42)
    nL = 0
    keys = list(RANGES)
    U = (np.argsort(rng.random((len(keys), nL)), axis=1) + rng.random((len(keys), nL))) / nL
    for k in range(nL):
        kw = {}
        for q, p in enumerate(keys):
            lo, _, hi = RANGES[p]
            if p in ("E", "ell_s"):
                kw[p] = float(np.exp(np.log(lo) + U[q, k] * (np.log(hi) - np.log(lo))))
            else:
                kw[p] = float(lo + U[q, k] * (hi - lo))
        for sd in range(1):
            jobs.append(dict(tag=f"LHS|{k}|" + json.dumps(kw), kw=kw, seed=32000 + 10 * k + sd))
    with Pool(10) as pool:
        res = []
        if os.path.exists(CACHE):
            res = [tuple(json.loads(l)) for l in open(CACHE)]
        done = {(r[0], r[3]) for r in res}
        todo = [j for j in jobs if (j["tag"], j["seed"]) not in done]
        for k, r in enumerate(pool.imap_unordered(job, todo)):
            res.append(r)
            with open(CACHE, "a") as f:
                f.write(json.dumps(r) + "\n")
            print(f"{k+1}/{len(todo)} {r[0][:40]} eta={r[1]:.2f}", flush=True)
    agg = {}
    for tag, e, s, _ in res:
        agg.setdefault(tag, []).append((e, s))
    out = dict(label=LABEL, ranges=RANGES, seeds=SEEDS, oat={}, bypass={}, lhs=[])
    for tag, v in agg.items():
        v = np.array(v)
        kind = tag.split("|")[0]
        d = dict(eta_mean=float(v[:, 0].mean()), eta_sem=float(v[:, 0].std(ddof=1) / np.sqrt(len(v))) if len(v) > 1 else 0.0,
                 stuck_mean=float(v[:, 1].mean()))
        if kind == "OAT":
            out["oat"][tag[4:]] = d
        elif kind == "BYP":
            out["bypass"][tag[4:]] = d
        elif kind == "DES":
            out.setdefault("design", {})[tag[4:]] = d
        else:
            d["params"] = json.loads(tag.split("|", 2)[2]); out["lhs"].append(d)
    # combined band from the OAT extremes (LHS dropped: machine time)
    nom = out["oat"].get("nominal|nom|0", {}).get("eta_mean", np.nan)
    ex = [v["eta_mean"] for k, v in out["oat"].items()]
    out["oat_band"] = dict(nominal=nom, min=float(min(ex)), max=float(max(ex)))
    with open(os.path.join(HERE, "results", "SIM_sensitivity.json"), "w") as f:
        json.dump(out, f, indent=1)
    print(json.dumps({k: out[k] for k in ("oat", "bypass", "design", "oat_band")}, indent=1))


if __name__ == "__main__":
    main()
