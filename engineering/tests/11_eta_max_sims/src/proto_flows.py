"""
proto_flows.py - prototype-scale lane flows (copied 2D CFD solver from 03_cfd_flow, cache in ../results/cfd_cache).
*** SIMULATED - model-based. ***  11 deg screen in a 28 m x 7 m lane, Q = 100 m3/s, dx = 0.5 m.
Entrance (bypass) flow 3-50% of lane flow; mouth (scoop) width 2/4/6 m; apex entrance on/off; apex share;
graded baffle k-profile behind the downstream 40% of the face.
"""
import sys, os, time, json
import numpy as np
import multiprocessing as mp
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lane import solve, status, screen_stats, geometry, BASE

FB = [0.03, 0.10, 0.20, 0.35, 0.50]
B = [2.0, 4.0, 6.0]


def baffle_prof(kmax):
    L = 28.0 / np.sin(np.radians(11.0))
    se = np.linspace(0, L, 41)
    sc = 0.5 * (se[:-1] + se[1:])
    k = np.where(sc < 0.6 * L, BASE["k"], BASE["k"] + (kmax - BASE["k"]) * (sc - 0.6 * L) / (0.4 * L))
    return (se.tolist(), k.tolist())


def flow_list():
    Ps = [dict(fb=f, b=b) for f in FB for b in B]
    Ps += [dict(fb=0.20, b=2.0, terminal=False), dict(fb=0.20, b=4.0, terminal=False),
           dict(fb=0.20, b=4.0, split="terminal50"), dict(fb=0.35, b=4.0, split="terminal50")]
    Ps.append(dict(fb=0.35, b=4.0, split="terminal50", kprof=baffle_prof(10.0)))
    for km in (10.0, 30.0):
        Ps.append(dict(fb=0.20, b=4.0, kprof=baffle_prof(km)))
        Ps.append(dict(fb=0.35, b=4.0, kprof=baffle_prof(km)))
    return Ps


def one(P):
    t0 = time.time()
    G = solve(P, t_max=1500, avg=400, wall_max=900)
    return P, G["info"]["converged"], G["info"]["n_avg"], time.time() - t0


if __name__ == "__main__":
    Ps = [P for P in flow_list() if status(P) != "ok"]
    print(len(Ps), "flows", flush=True)
    with mp.get_context("fork").Pool(int(sys.argv[1]) if len(sys.argv) > 1 else 6) as pool:
        for P, c, na, w in pool.imap_unordered(one, Ps):
            print({k: v for k, v in P.items() if k != "kprof"}, "kprof" if "kprof" in P else "", c, na, f"{w:.0f}s", flush=True)
