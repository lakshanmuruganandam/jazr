"""
run_proto.py - lever study at PROTOTYPE scale (2D lane CFD + extended bell tracker).
*** SIMULATED - model-based; 2D depth-averaged = UPPER BOUND (no 3D leak paths, no bell-bell jamming). ***
5 seeds x 2000 bells per config, real Gulf bells 6.5-12 cm unless stated. v4.1 reference: 11 deg, entrance flow
20%, 4 m mouths every 30 m + apex entrance, mu 0.4, passive bells.
Writes results/proto_levers.csv
"""
import os, sys, json, csv, time
import numpy as np
import multiprocessing as mp
from scipy import stats as sst
from lane import solve
from proto_track import track
from proto_flows import baffle_prof

RES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")
REF = dict(fb=0.20, b=4.0)
SEEDS = 5


def one(job):
    G = solve(job["flow"], t_max=1500, avg=400, wall_max=900)
    r = track(G, n=2000, seed=job["seed"], **job.get("kw", {}))
    r.pop("_frames")
    r.update(group=job["group"], tag=job["tag"], seed=job["seed"])
    return r


def jobs():
    J = []
    def add(g, tag, flow=None, **kw):
        for sd in range(SEEDS):
            J.append(dict(group=g, tag=tag, flow=dict(REF, **(flow or {})), kw=kw, seed=200 + sd))
    for f in (0.03, 0.10, 0.20, 0.35, 0.50):
        add("P1_entrance_flow", f"{int(f*100)}%" + (" (no dewatering)" if f == 0.03 else " + dewatering"), dict(fb=f))
    for b in (2.0, 4.0, 6.0):
        add("P2_apex_scoop", f"apex + {b:.0f} m scoops", dict(b=b))
    add("P2_apex_scoop", "NO apex entrance, 2 m", dict(b=2.0, terminal=False))
    add("P2_apex_scoop", "NO apex entrance, 4 m", dict(b=4.0, terminal=False))
    add("P2_apex_scoop", "apex share 50%, 4 m", dict(split="terminal50"))
    add("P2_apex_scoop", "35% equal split | half flow, rheo 10", dict(fb=0.35), flow_scale=0.5, swim=0.10, swim_mode="rheo")
    add("P2_apex_scoop", "35% apex share 50% | half flow, rheo 10", dict(fb=0.35, split="terminal50"), flow_scale=0.5, swim=0.10, swim_mode="rheo")
    for bt in (0.0, 0.25, 0.5, 1.0):
        add("P3_conveyor", f"belt {bt:.2f} x sweep", belt_frac=bt)
        add("P3_conveyor", f"belt {bt:.2f} | half flow, rheotactic 10 cm/s", belt_frac=bt, flow_scale=0.5, swim=0.10, swim_mode="rheo")
    for mu in (0.05, 0.1, 0.2, 0.4, 4.0):
        add("P5_friction", f"mu {mu}", mu=mu)
    add("P6_baffles", "no baffles")
    add("P6_baffles", "graded baffle k->10", dict(kprof=baffle_prof(10.0)))
    add("P6_baffles", "graded baffle k->30", dict(kprof=baffle_prof(30.0)))
    for j in (0.0, 0.1, 0.25, 0.5):
        add("P7_walljet", f"jet {j:.2f} x sweep", jet_frac=j)
        add("P7_walljet", f"jet {j:.2f} | half flow, rheotactic 10 cm/s", jet_frac=j, flow_scale=0.5, swim=0.10, swim_mode="rheo")
    add("P8_size_swim", "6.5-12 cm passive", d_range=(0.065, 0.12))
    add("P8_size_swim", "30-45 cm passive (old assumption)", d_range=(0.30, 0.45))
    for sw in (0.036, 0.10):
        add("P8_size_swim", f"swim {sw*100:.1f} cm/s random", swim=sw)
        add("P8_size_swim", f"swim {sw*100:.1f} cm/s rheotactic", swim=sw, swim_mode="rheo")
        add("P8_size_swim", f"swim {sw*100:.1f} cm/s rheotactic, half flow", swim=sw, swim_mode="rheo", flow_scale=0.5)
    add("P9_density", "0.3 /m3", density=0.3)
    add("P9_density", "1.0 /m3", density=1.0)
    add("P9_density", "1.0 /m3, 30-45 cm bells", density=1.0, d_range=(0.30, 0.45))
    add("P9_density", "1.0 /m3, 30-45 cm, mu 2", density=1.0, d_range=(0.30, 0.45), mu=2.0)
    for c in (-0.03, -0.02, -0.01, 0.0, 0.01, 0.02, 0.03):
        add("CUE_proto", f"cue {c*100:+.0f} cm/s | full flow, rheo 3.6", cue=c, swim=0.036, swim_mode="rheo")
        add("CUE_proto", f"cue {c*100:+.0f} cm/s | half flow, rheo 10", cue=c, swim=0.10, swim_mode="rheo", flow_scale=0.5)
    # best combination vs v4.1 under the prototype stress case
    best = dict(flow=dict(fb=0.35, b=4.0, split="terminal50", kprof=baffle_prof(10.0)))
    for lab, fl, kw in (("v4.1", {}, {}), ("best", best["flow"], dict(belt_frac=0.5, jet_frac=0.25, mu=0.1))):
        add("COMBO_proto", f"{lab} | nominal", fl, **kw)
        add("COMBO_proto", f"{lab} | half flow, rheo 10 cm/s", fl, flow_scale=0.5, swim=0.10, swim_mode="rheo", **kw)
        add("COMBO_proto", f"{lab} | 1 /m3", fl, density=1.0, **kw)
        add("COMBO_proto", f"{lab} | half flow, rheo 10, 1 /m3, mu 0.4", fl, flow_scale=0.5, swim=0.10, swim_mode="rheo", density=1.0, **dict(kw, mu=0.4))
    return J


def ci(x):
    x = np.asarray(x, float)
    h = sst.t.ppf(0.975, len(x) - 1) * x.std(ddof=1) / np.sqrt(len(x))
    return x.mean(), max(0, x.mean() - h), min(1, x.mean() + h)


if __name__ == "__main__":
    t0 = time.time()
    with mp.get_context("fork").Pool(10) as p:
        R = p.map(one, jobs(), chunksize=2)
    json.dump(R, open(os.path.join(RES, "proto_runs.json"), "w"))
    by = {}
    for r in R:
        by.setdefault((r["group"], r["tag"]), []).append(r)
    rows = []
    for (g, t), v in by.items():
        m, lo, hi = ci([r["eta"] for r in v])
        k = sum(round(r["eta"] * r["n"]) for r in v); n = sum(r["n"] for r in v)
        cp_lo = sst.beta.ppf(0.025, k, n - k + 1) if k > 0 else 0.0
        rows.append(dict(group=g, config=t, seeds=len(v), bells=n, eta_mean=round(m, 4), eta_ci_lo=round(lo, 4),
                         eta_ci_hi=round(hi, 4), eta_cp_lo=round(cp_lo, 4),
                         jam_rate=round(np.mean([r["jam"] for r in v]), 4), held=round(np.mean([r["held"] for r in v]), 4),
                         lingering=round(np.mean([r["lingering"] for r in v]), 4), leaked=round(np.mean([r["leaked"] for r in v]), 4),
                         apex_share=round(np.mean([r["apex_share"] for r in v]), 3),
                         contacts_per_bell=round(np.mean([r["contacts"] for r in v]), 2),
                         t_face_s=round(np.mean([r["tface"] for r in v]), 1), t_face_p90_s=round(np.mean([r["tface_p90"] for r in v]), 1),
                         face_cover_max=round(np.mean([r["cov_max"] for r in v]), 3),
                         data_type="SIMULATED prototype 2D CFD tracker - upper bound"))
    with open(os.path.join(RES, "proto_levers.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    for r in rows:
        print(f"{r['group']:17s} {r['config']:48s} eta {r['eta_mean']:.3f} [{r['eta_ci_lo']:.3f}-{r['eta_ci_hi']:.3f}] jam {r['jam_rate']:.3f} cont {r['contacts_per_bell']} tface {r['t_face_s']} cov {r['face_cover_max']}")
    print("wall", round(time.time() - t0))
