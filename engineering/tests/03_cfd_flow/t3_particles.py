"""
T3 - Finite-size bell tracking -> guidance efficiency to the bypass entrances.
Sweep: angle 8/11/15/20 deg x entrance spacing 15/30/60 m x bypass fraction 1/2/3/4 % (48 flow solves, dx=0.5 m)
       x bell diameter 0.30/0.45 m x swimming 0 / 3.6 / 10 cm/s (random heading, tau = 10 s), 1000 bells each.
Extra: friction mu 0.5/1/2 (impingement threshold); no terminal (apex) entrance; terminal-weighted bypass split.
Usage:  python3 t3_particles.py flows A    (angles 8, 11)   |  flows B (angles 15, 20)  |  flows X (extras)
        python3 t3_particles.py track      (all particle runs + figures; needs the cached flows)
Outputs: data/t3_results.json, data/t3_table.csv, figs/t3_*.png
"""
import sys, os, json, time, itertools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from multiprocessing import Pool
from lane import solve, HERE, status
from particles import track, public

OUT = os.path.join(HERE, "data"); FIG = os.path.join(HERE, "figs")
ANG = [8.0, 11.0, 15.0, 20.0]; SP = [15.0, 30.0, 60.0]; FB = [0.01, 0.02, 0.03, 0.04]
SWIM = [0.0, 0.036, 0.10]; DIA = [0.30, 0.45]
EXTRA = {"noterm": dict(terminal=False), "term50": dict(split="terminal50"),
         "noterm_fb4": dict(terminal=False, fb=0.04), "b4m": dict(b=4.0), "b1m": dict(b=1.0)}


def flow(P):
    t0 = time.time(); G = solve(P, t_max=1500, avg=400)
    return P, G["info"]["converged"], time.time() - t0


def pkey(P): return json.dumps(P, sort_keys=True)


FB_REDUCED = {8.0: [0.02, 0.04], 20.0: [0.02, 0.04]}   # machine was heavily shared: reduced fb set at 8 and 20 deg


def warm(P):
    """re-solve an unsteady case warm-started from a usable flow at the same angle (same grid)."""
    t0 = time.time()
    donor = [dict(theta=P["theta"])] + [dict(theta=P["theta"], spacing=s, fb=f) for s in SP for f in FB]
    for Dn in donor:
        if status(Dn) == "ok": break
    G0 = solve(Dn)
    G = solve(P, t_min=100, t_max=500, avg=200, init=(G0["u"], G0["v"]), wall_max=4000)
    return P, G["info"]["converged"], time.time() - t0


def one(args):
    P, D, sw, mu, seed, tag = args
    G = solve(P, t_max=1500, avg=400)
    r = public(track(G, n=1000, D=D, swim=sw, mu=mu, seed=seed))
    r.update(P=P, D=D, swim=sw, mu=mu, n_entr=len(G["mouths"]), L=float(G["L"]), tag=tag)
    return r


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "flows":
        part = sys.argv[2]
        if part == "W":
            Ps = [dict(theta=a, spacing=s, fb=f) for a in ANG for s in SP for f in FB_REDUCED.get(a, FB)]
            Ps += [dict(theta=a, **e) for a in (11.0, 20.0) for e in EXTRA.values()]
            Ps = [P for P in Ps if status(P) != "ok"]
            print(len(Ps), "flows to warm-solve", flush=True)
            with Pool(8) as pool:
                for P, conv, w in pool.imap_unordered(warm, Ps):
                    print(P, "converged" if conv else "time-averaged", f"{w:.0f}s", flush=True)
            sys.exit()
        if part in "AB":
            angs = ANG[:2] if part == "A" else ANG[2:]
            Ps = [dict(theta=a, spacing=s, fb=f) for a, s, f in itertools.product(angs, SP, FB)]
        else:
            Ps = [dict(theta=a, **e) for a in (11.0, 20.0) for e in EXTRA.values()]
        t0 = time.time()
        with Pool(8) as pool:
            for P, conv, w in pool.imap_unordered(flow, Ps):
                print(P, "converged" if conv else "time-averaged", f"{w:.0f}s", flush=True)
        print("wall", time.time() - t0)
        sys.exit()
    # ---------------- particle runs
    t0 = time.time()
    jobs = [(dict(theta=a, spacing=s, fb=f), D, sw, 0.5, 1) for a in ANG for s in SP for f in FB_REDUCED.get(a, FB)
            for D in DIA for sw in SWIM]
    jobs = [j + ("main",) for j in jobs]
    jobs += [(dict(theta=a, spacing=30.0, fb=0.02), D, 0.0, mu, 1, "mu") for a in ANG for D in DIA for mu in (1.0, 2.0, 4.0)]
    jobs += [(dict(theta=a, **e), D, sw, 0.5, 1, "x_" + nm) for a in (11.0, 20.0) for nm, e in EXTRA.items() for D in DIA for sw in SWIM]
    skipped = sorted({json.dumps(j[0], sort_keys=True) for j in jobs if status(j[0]) != "ok"})
    jobs = [j for j in jobs if status(j[0]) == "ok"]
    print("skipped flows (not usable):", skipped, flush=True)
    with Pool(8) as pool:
        R = pool.map(one, jobs, chunksize=4)
    json.dump(R, open(os.path.join(OUT, "t3_results.json"), "w"), indent=0, default=float)
    with open(os.path.join(OUT, "t3_table.csv"), "w") as f:
        f.write("tag,theta,spacing,fb,terminal,split,b,D,swim,mu,n_entr,captured,held,lingering,leaked,back,"
                "share_terminal,share_intermediate,t_face_to_capture_median,t_face_to_capture_p90\n")
        for r in R:
            P = r["P"]; be = r["by_entrance"]
            term = P.get("terminal", True)
            sh_t = be[0] if (be and term) else 0.0
            f.write(f"{r['tag']},{P['theta']},{P.get('spacing',30)},{P.get('fb',0.02)},{term},{P.get('split','equal')},{P.get('b',2.0)},"
                    f"{r['D']},{r['swim']},{r['mu']},{r['n_entr']},{r['captured']:.3f},{r['held']:.3f},{r['lingering']:.3f},"
                    f"{r['leaked']:.3f},{r['back']:.3f},{sh_t:.3f},{r['captured']-sh_t:.3f},"
                    f"{r['t_face_to_capture_median']},{r['t_face_to_capture_p90']}\n")
    # ---------------- figures
    fig, ax = plt.subplots(2, 3, figsize=(16, 8.5))
    cl = {0.0: "#08306b", 0.036: "#e6550d", 0.10: "#31a354"}
    for j, sp in enumerate(SP):
        a = ax[0, j]
        for sw in SWIM:
            for D, ls in ((0.30, "-"), (0.45, "--")):
                y_cap = [np.mean([r["captured"] for r in R if r["tag"] in ("main", "mu") and r["P"]["theta"] == th and r["P"]["spacing"] == sp
                                  and r["D"] == D and r["swim"] == sw and r["mu"] == 0.5]) for th in ANG]
                y_int = [np.mean([r["captured"] - r["by_entrance"][0] for r in R if r["tag"] in ("main", "mu") and r["P"]["theta"] == th
                                  and r["P"]["spacing"] == sp and r["D"] == D and r["swim"] == sw and r["mu"] == 0.5]) for th in ANG]
                a.plot(ANG, y_cap, ls, color=cl[sw], marker="o", label=f"all entrances, swim {sw*100:.1f} cm/s, D {D}")
                ax[1, j].plot(ANG, y_int, ls, color=cl[sw], marker="s", label=f"swim {sw*100:.1f} cm/s, D {D}")
        a.set(title=f"Guidance efficiency (captured by any entrance), spacing {sp:.0f} m", xlabel="screen angle [deg]",
              ylabel="fraction of bells (mean over bypass 1-4%)", ylim=(0, 1.05)); a.grid(alpha=.3)
        ax[1, j].set(title=f"Share caught by INTERMEDIATE entrances, spacing {sp:.0f} m", xlabel="screen angle [deg]",
                     ylabel="fraction of bells", ylim=(0, 1.05)); ax[1, j].grid(alpha=.3)
    ax[0, 0].legend(fontsize=6); ax[1, 0].legend(fontsize=6)
    plt.tight_layout(); plt.savefig(os.path.join(FIG, "t3_efficiency_vs_angle_spacing.png"), dpi=130); plt.close()
    fig, ax = plt.subplots(1, 2, figsize=(13, 4.3))
    for th, c in zip(ANG, ("#9ecae1", "#08306b", "#e6550d", "#a50f15")):
        y = [np.mean([r["captured"] - r["by_entrance"][0] for r in R if r["tag"] in ("main", "mu") and r["P"]["theta"] == th
                      and r["P"]["spacing"] == 30.0 and r["P"]["fb"] == f and r["mu"] == 0.5]) for f in FB]
        ax[0].plot(np.array(FB)*100, y, "o-", color=c, label=f"{th:.0f} deg")
        y = [np.mean([r["held"] + r["lingering"] for r in R if r["P"].get("theta") == th and r["mu"] == mu and r["tag"] in ("main", "mu")
                      and r["P"]["spacing"] == 30.0 and r["P"]["fb"] == 0.02 and r["swim"] == 0.0]) for mu in (0.5, 1.0, 2.0, 4.0)]
        ax[1].plot((0.5, 1, 2, 4), y, "o-", color=c, label=f"{th:.0f} deg")
    ax[0].set(xlabel="bypass flow [% of 100 m3/s]", ylabel="share caught before the apex entrance",
              title="Intermediate-entrance catch vs bypass flow (30 m spacing; mean of D, swim)"); ax[0].grid(alpha=.3); ax[0].legend()
    ax[1].set(xscale="log", xlabel="bell-mesh friction coefficient mu", ylabel="fraction held on face / not delivered",
              title="Impingement vs friction (passive bells, 30 m, 2%)"); ax[1].grid(alpha=.3); ax[1].legend()
    plt.tight_layout(); plt.savefig(os.path.join(FIG, "t3_bypass_and_friction.png"), dpi=130); plt.close()
    print("particle wall", time.time() - t0, "runs", len(R))
