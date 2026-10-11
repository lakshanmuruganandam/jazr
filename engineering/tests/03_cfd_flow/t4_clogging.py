"""
T4 - Clogging feedback: bells sitting on the face block mesh -> local porosity drops -> flow redistributes.
Loop (per bell density): flow -> track 2000 bells (D = 0.35 m, swim 3.6 cm/s) -> steady face coverage c(s)
  c(s) = (bell-seconds on face in bin) x (bells arriving per second / bells simulated) x A_bell / (bin length x h)
  arrival rate = density x Q (100 m3/s);  A_bell = pi D^2/4.  Bells still on the face at t_max (held / lingering)
  are counted for the whole t_max, i.e. they signal unbounded accumulation; c is capped at C_MAX.
  beta_eff = beta (1 - c),  k(s) = k_wire(beta_eff);  under-relaxed update (0.5), 4 iterations, warm-started flow.
Grid dx = 1.0 m.  Densities: 0.1, 0.3 (v3 design), 1.0 bells/m3.  Geometry: 11 deg, 30 m spacing, 2 % bypass (v3 baseline).
Plus an "apex-pile" variant at 0.3/m3 with the terminal entrance removed.
Outputs: data/t4_results.json, figs/t4_clogging.png
"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from multiprocessing import Pool
from lane import solve, face_profile, screen_stats, HERE
from particles import track, public
from jzcfd import k_wire

OUT = os.path.join(HERE, "data"); FIG = os.path.join(HERE, "figs")
BETA = 0.5; D = 0.35; SWIM = 0.036; C_MAX = 0.6; NIT = 4; NP = 2000; T_MAX = 1200.0
DX = 1.0   # coarse grid (T1: ~15-20 % error on hot-spot Vn) - chosen because the machine was heavily shared


def loop(args):
    dens, extra = args
    base = dict(theta=11.0, spacing=30.0, fb=0.02, k=float(k_wire(BETA)), dx=DX, **extra)
    G = solve(base, t_max=1500, avg=500, wall_max=3000)
    L = G["L"]; h = G["P"]["h"]; Q = G["P"]["Q"]
    edges = np.linspace(0, L, int(L/2.0) + 1); mids = 0.5*(edges[1:] + edges[:-1])
    c = np.zeros(len(mids)); hist = []
    A = np.pi*D**2/4; rate = dens*Q
    kprof = None
    for it in range(NIT + 1):
        F = face_profile(G, ds=0.25); st = screen_stats(G)
        kk = None if kprof is None else kprof[1]
        tr = track(G, n=NP, D=D, swim=SWIM, s_bins=edges, kprof_s=None if kprof is None else mids,
                   kprof_k=kk, t_max=T_MAX, seed=it)
        c_calc = np.minimum(tr["_occ"]*(rate/NP)*A/(np.diff(edges)*h), C_MAX)
        dp = 0.5*(np.interp(F["s"], mids, kk) if kk is not None else G["P"]["k"])*np.maximum(F["Vn"], 0)**2
        hist.append(dict(it=it, coverage_mean=float(c.mean()), coverage_max=float(c.max()),
                         frac_face_blocked_over_50=float(np.mean(c > 0.5)),
                         Vn_max=st["Vn_max"], Vn_p95=st["Vn_p95"], Vn_cv=st["Vn_cv"],
                         frac_Vn_over_0p15=float(np.mean(F["Vn"][~F["inmouth"]] > 0.15)),
                         dp_max_mm=float(dp.max()*1000/9.81), **public(tr),
                         c=c.tolist(), Vn=F["Vn"][::8].tolist(), s=F["s"][::8].tolist(), c_calc=c_calc.tolist()))
        print(dens, extra, it, f"cov mean {c.mean():.2f} max {c.max():.2f} Vn max {st['Vn_max']:.3f} p95 {st['Vn_p95']:.3f} "
              f"capt {tr['captured']:.3f} held {tr['held']:.3f} ling {tr['lingering']:.3f}", flush=True)
        if it == NIT: break
        c = 0.5*c + 0.5*c_calc if it > 0 else c_calc*0.5
        kprof = (edges.tolist(), np.round(k_wire(BETA*(1 - c)), 4).tolist())
        P = dict(base, kprof=kprof)
        G = solve(P, t_max=600, t_min=200, avg=250, init=(G["u"], G["v"]), wall_max=3000)
    return dict(density=dens, extra=extra, mids=mids.tolist(), hist=hist, L=float(L))


if __name__ == "__main__":
    t0 = time.time()
    jobs = [(0.1, {}), (0.3, {}), (1.0, {}), (0.3, dict(terminal=False))]
    with Pool(4) as pool:
        R = pool.map(loop, jobs)
    json.dump(R, open(os.path.join(OUT, "t4_results.json"), "w"), default=float)
    fig, ax = plt.subplots(2, 2, figsize=(14, 8))
    for r, c in zip(R, ("#9ecae1", "#08306b", "#a50f15", "#e6550d")):
        lab = f"{r['density']}/m3" + (" no apex entrance" if r["extra"] else "")
        h0, hN = r["hist"][0], r["hist"][-1]
        ax[0, 0].plot(np.array(r["mids"])/r["L"], hN["c"], color=c, label=lab)
        ax[0, 1].plot(np.array(hN["s"])/r["L"], hN["Vn"], color=c, label=lab)
        ax[1, 0].plot([h["it"] for h in r["hist"]], [h["Vn_max"] for h in r["hist"]], "o-", color=c, label=lab)
        ax[1, 1].plot([h["it"] for h in r["hist"]], [h["captured"] for h in r["hist"]], "o-", color=c, label=lab + " captured")
        ax[1, 1].plot([h["it"] for h in r["hist"]], [h["held"] + h["lingering"] for h in r["hist"]], "x--", color=c, label=lab + " held/lingering")
    ax[0, 1].plot(np.array(R[0]["hist"][0]["s"])/R[0]["L"], R[0]["hist"][0]["Vn"], "k:", label="clean screen")
    ax[0, 0].set(xlabel="s / L", ylabel="face coverage c (capped 0.6)", title="Steady bell coverage after feedback")
    ax[0, 1].set(xlabel="s / L", ylabel="Vn [m/s]", title="Through-screen velocity after feedback"); ax[0, 1].axhline(0.1, color="k", lw=.6)
    ax[1, 0].set(xlabel="iteration", ylabel="max Vn [m/s]", title="Hot-spot velocity vs feedback iteration")
    ax[1, 1].set(xlabel="iteration", ylabel="fraction of bells", title="Delivery to entrances", ylim=(0, 1.05))
    for a in ax.flat: a.grid(alpha=.3); a.legend(fontsize=7)
    plt.tight_layout(); plt.savefig(os.path.join(FIG, "t4_clogging.png"), dpi=130); plt.close()
    print("wall", time.time() - t0)
