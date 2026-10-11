"""
controller.py - SIMULATED AI closed-loop controller for the inner screen (virtual tank, 1:20).
*** SIMULATED - model-based. ***

Knobs (27 arms): apex share of the entrance flow {equal 25%, 50%, 80%} x belt speed {0, 0.25, 0.5} x sweep
x wall jet {0, 0.25, 0.5} x sweep; total entrance flow fixed at 20% (lift/dewatering capacity).
Observable per epoch: bells entering each entrance (counts) and bells NOT guided (left on the face = would be
released to the plant by relief / cycling). Reward = guided / arrived.
Conditions change over 120 epochs: 0-29 nominal 0.3 /m3 batch; 30-59 density rising to 1 /m3 (continuous
feed with clogging feedback); 60-89 fouled downstream bay (4x mesh resistance, mu 0.8); 90-119 belt drive
fault (belt arms behave as belt 0) on top of the fouled bay.
Method: (1) every arm x condition is simulated with 6 seeds in the virtual tank (pool);
(2) controllers are replayed against the pool (each epoch draws one simulated run of the chosen arm):
  - discounted Thompson sampling (Beta posteriors, gamma = 0.92) = the AI controller;
  - best FIXED arm (chosen at commissioning = best mean under nominal conditions);
  - oracle (best arm of each condition, known in hindsight).
"""
import os, sys, json, time, itertools
import numpy as np
import multiprocessing as mp
from run_vt import one, RES

SPLITS = [-1.0, 0.5, 0.8]; BELTS = [0.0, 0.25, 0.5]; JETS = [0.0, 0.25, 0.5]
ARMS = list(itertools.product(SPLITS, BELTS, JETS))
CONDS = {"nominal": {}, "density1": {"density": 1.0}, "fouled": {"kw": {"foul_bay": 3}}}
POOL = os.path.join(RES, "ctrl_pool.jsonl")
NSEED = 6


def jobs():
    J = []
    for ai, (sp, bt, jt) in enumerate(ARMS):
        for cn, c in CONDS.items():
            kw = dict(apex_share=sp, belt_frac=bt, jet_frac=jt, **c.get("kw", {}))
            for sd in range(NSEED):
                J.append(dict(group="CTRL", tag=f"{ai}|{cn}", seed=5000 + sd, kw=kw, density=c.get("density")))
    return J


def build_pool():
    done = set()
    if os.path.exists(POOL):
        for l in open(POOL):
            r = json.loads(l); done.add((r["tag"], r["seed"]))
    J = [j for j in jobs() if (j["tag"], j["seed"]) not in done]
    J.sort(key=lambda j: -(j.get("density") or 0))
    print(len(J), "pool runs", flush=True)
    with mp.get_context("fork").Pool(10) as p:
        for k, r in enumerate(p.imap_unordered(one, J)):
            with open(POOL, "a") as f:
                f.write(json.dumps(r) + "\n")
            if k % 50 == 0:
                print(k, flush=True)


def load_pool():
    pool = {}
    for l in open(POOL):
        r = json.loads(l)
        ai, cn = r["tag"].split("|")
        pool.setdefault((int(ai), cn), []).append((r["bypass"], r["n"], r["ent"]))
    return pool


SCHED = ["nominal"] * 30 + ["density1"] * 30 + ["fouled"] * 30 + ["fault"] * 30


def draw(pool, ai, cond, rng):
    if cond == "fault":                      # belt drive fault on top of the fouled bay
        sp, bt, jt = ARMS[ai]
        ai = ARMS.index((sp, 0.0, jt)); cond = "fouled"
    runs = pool[(ai, cond)]
    return runs[rng.integers(len(runs))]


def thompson(pool, rng, gamma=0.92):
    a = np.ones(len(ARMS)); b = np.ones(len(ARMS)); out = []
    for cond in SCHED:
        ai = int(np.argmax(rng.beta(a, b)))
        k, n, ent = draw(pool, ai, cond, rng)
        a = 1 + gamma * (a - 1); b = 1 + gamma * (b - 1)
        a[ai] += k; b[ai] += n - k
        out.append((k, n, ai))
    return out


def factored(pool, rng, gamma=0.8):
    """AI controller: factored discounted Thompson sampling - one Beta posterior per value of each knob, so evidence
    is shared across arms that use the same split / belt / jet setting (adapts faster than per-arm TS)."""
    vals = [SPLITS, BELTS, JETS]
    A = [np.ones(3) for _ in range(3)]; B = [np.ones(3) for _ in range(3)]; out = []
    for cond in SCHED:
        ch = [int(np.argmax(rng.beta(A[q], B[q]))) for q in range(3)]
        ai = ARMS.index(tuple(vals[q][ch[q]] for q in range(3)))
        k, n, ent = draw(pool, ai, cond, rng)
        for q in range(3):
            A[q] = 1 + gamma * (A[q] - 1); B[q] = 1 + gamma * (B[q] - 1)
            A[q][ch[q]] += k; B[q][ch[q]] += n - k
        out.append((k, n, ai))
    return out


def fixed(pool, rng, ai):
    return [draw(pool, ai, c, rng)[:2] + (ai,) for c in SCHED]


def mean_eta(pool, ai, cond):
    if cond == "fault":
        sp, bt, jt = ARMS[ai]; ai = ARMS.index((sp, 0.0, jt)); cond = "fouled"
    v = pool[(ai, cond)]
    return sum(x[0] for x in v) / sum(x[1] for x in v)


if __name__ == "__main__":
    if "pool" in sys.argv:
        build_pool()
    pool = load_pool()
    best_fixed = int(np.argmax([mean_eta(pool, i, "nominal") for i in range(len(ARMS))]))
    # tie-break: cheapest (lowest belt, jet) arm within 0.5 pp of the best nominal arm
    bn = mean_eta(pool, best_fixed, "nominal")
    cands = [i for i in range(len(ARMS)) if mean_eta(pool, i, "nominal") >= bn - 0.005]
    best_fixed = min(cands, key=lambda i: (ARMS[i][1], ARMS[i][2], -mean_eta(pool, i, "nominal")))
    oracle = {c: int(np.argmax([mean_eta(pool, i, c) for i in range(len(ARMS))])) for c in ("nominal", "density1", "fouled", "fault")}
    R = dict(arms=[dict(apex_share=a[0], belt=a[1], jet=a[2],
                        **{c: mean_eta(pool, i, c) for c in ("nominal", "density1", "fouled", "fault")}) for i, a in enumerate(ARMS)],
             best_fixed=best_fixed, oracle=oracle, schedule=["nominal", "density1", "fouled", "fault"])
    NREP = 200
    curves = {"AI controller (factored discounted Thompson)": [], "per-arm discounted Thompson": [], "best fixed (commissioning)": [], "v4.1 fixed (equal split, no belt/jet)": [], "oracle": []}
    for rep in range(NREP):
        rng = np.random.default_rng(rep)
        curves["AI controller (factored discounted Thompson)"].append([k / n for k, n, _ in factored(pool, rng)])
        curves["per-arm discounted Thompson"].append([k / n for k, n, _ in thompson(pool, rng)])
        curves["best fixed (commissioning)"].append([k / n for k, n, _ in fixed(pool, rng, best_fixed)])
        curves["v4.1 fixed (equal split, no belt/jet)"].append([k / n for k, n, _ in fixed(pool, rng, ARMS.index((-1.0, 0.0, 0.0)))])
        curves["oracle"].append([(lambda x: x[0] / x[1])(draw(pool, oracle[c], c, rng)) for c in SCHED])
    phases = {"nominal": slice(0, 30), "density 0.3->1": slice(30, 60), "fouled bay": slice(60, 90), "fouled + belt fault": slice(90, 120)}
    summ = {}
    for nm, c in curves.items():
        c = np.array(c)
        summ[nm] = {ph: dict(eta=float(c[:, sl].mean()), lo=float(np.percentile(c[:, sl].mean(1), 2.5)),
                             hi=float(np.percentile(c[:, sl].mean(1), 97.5))) for ph, sl in phases.items()}
        summ[nm]["all"] = dict(eta=float(c.mean()), lo=float(np.percentile(c.mean(1), 2.5)), hi=float(np.percentile(c.mean(1), 97.5)))
        R.setdefault("curve_mean", {})[nm] = c.mean(0).tolist()
    R["summary"] = summ
    R["label"] = "SIMULATED virtual tank + replayed controller - model-based"
    json.dump(R, open(os.path.join(RES, "controller.json"), "w"), indent=1)
    import csv
    with open(os.path.join(RES, "controller_summary.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["controller", "phase", "eta_mean", "ci95_lo", "ci95_hi", "data_type"])
        for nm, d in summ.items():
            for ph, v in d.items():
                w.writerow([nm, ph, round(v["eta"], 4), round(v["lo"], 4), round(v["hi"], 4), "SIMULATED"])
    print("best fixed arm", ARMS[best_fixed], "oracle", {c: ARMS[i] for c, i in oracle.items()})
    for nm, d in summ.items():
        print(f"{nm:42s}", " ".join(f"{ph}: {v['eta']:.3f}" for ph, v in d.items()))
