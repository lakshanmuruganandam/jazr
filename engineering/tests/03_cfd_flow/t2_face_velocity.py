"""
T2 - Through-screen (Vn) and sweep (Vt) velocity distribution along the face.
Lane W = 28 m, h = 7 m, Q = 100 m3/s (U = 0.51 m/s), dx = 0.5 m production grid (see T1 for grid error).
Cases: angle 8/11/15/20 deg (lane width fixed -> screen area changes); porosity beta 0.3/0.5/0.7 (k from the
wire-screen correlation); bypass fraction 0/1/2/4 % and terminal-weighted split; entrance spacing 15/30/60 m;
added uniform back-baffle loss (k_total 10/30/100) as an equalisation option; eddy-viscosity sensitivity.
Outputs: data/t2_results.json, data/t2_profiles.npz, figs/t2_*.png
"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from multiprocessing import Pool
from lane import solve, face_profile, screen_stats, centred, HERE, BASE
from jzcfd import k_wire

OUT = os.path.join(HERE, "data"); FIG = os.path.join(HERE, "figs")
CASES = {
    "theta08": dict(theta=8.0), "theta11": dict(theta=11.0), "theta15": dict(theta=15.0), "theta20": dict(theta=20.0),
    "beta0.3": dict(k=float(k_wire(0.3))), "beta0.7": dict(k=float(k_wire(0.7))),
    "fb0": dict(fb=0.0), "fb1": dict(fb=0.01), "fb4": dict(fb=0.04), "fb2_term50": dict(split="terminal50"),
    "sp15": dict(spacing=15.0), "sp60": dict(spacing=60.0), "noentr": dict(spacing=0, fb=0.0),
    "baffle10": dict(k=10.0), "baffle30": dict(k=30.0), "baffle100": dict(k=100.0),
    "nu0.006": dict(nu=0.006), "nu0.05": dict(nu=0.05),
    "theta20_baffle30": dict(theta=20.0, k=30.0),
}


def run(name):
    P = CASES[name]; t0 = time.time()
    tm = 900 if P.get("k", 0) >= 30 else 1500
    G = solve(P, t_max=tm, avg=400 if tm > 1000 else 300)
    st = screen_stats(G); F = face_profile(G, ds=0.25)
    return name, dict(stats=st, info={k: v for k, v in G["info"].items()}, n_entr=len(G["mouths"]),
                      mouths=[float(m) for m in G["mouths"]]), (F["s"]/G["L"], F["Vn"], F["Vt"], F["inmouth"])


def smooth(a, n=9):
    k = np.ones(n)/n; return np.convolve(np.pad(a, n//2, mode="edge"), k, mode="valid")


def fieldfig(name, fn):
    G = solve(CASES[name], t_max=1500, avg=400)
    uc, vc = centred(G); dx = G["P"]["dx"]
    X = (np.arange(G["nx"]) + 0.5)*dx; Y = (np.arange(G["ny"]) + 0.5)*dx
    spd = np.ma.masked_where(~G["fluid"], np.hypot(uc, vc))
    fig, ax = plt.subplots(2, 1, figsize=(13, 6.2))
    im = ax[0].pcolormesh(X, Y, spd.T, cmap="viridis", shading="auto", vmin=0, vmax=0.9)
    ax[0].streamplot(X, Y, uc.T, vc.T, density=(3.5, 1.2), color="w", linewidth=0.5, arrowsize=0.6)
    plt.colorbar(im, ax=ax[0], label="|u| [m/s]")
    p = np.ma.masked_where(~G["fluid"], G["p"]*1000/9.81)
    im = ax[1].pcolormesh(X, Y, p.T, cmap="magma", shading="auto"); plt.colorbar(im, ax=ax[1], label="head [mm]")
    for a in ax:
        a.plot([G["P0"][0], G["P1"][0]], [G["P0"][1], G["P1"][1]], "c-", lw=1)
        for sm in G["mouths"]:
            q = G["P0"] + sm*G["t"]; a.plot(q[0], q[1], "o", mfc="none", mec="r", ms=7)
        a.set_aspect("equal"); a.set_xlabel("x [m]"); a.set_ylabel("y [m]")
    ax[0].set_title(f"Lane flow, screen {G['P']['theta']:.0f} deg, k={G['P']['k']:.2f}, bypass {G['P']['fb']*100:.0f}% "
                    f"({len(G['mouths'])} entrances, red o) - speed + streamlines")
    ax[1].set_title("Kinematic pressure as head [mm] (relative to outlet)")
    plt.tight_layout(); plt.savefig(os.path.join(FIG, fn), dpi=130); plt.close()


if __name__ == "__main__":
    t0 = time.time()
    with Pool(8) as pool:
        R = pool.map(run, list(CASES))
    res = {n: r for n, r, _ in R}; prof = {n: p for n, _, p in R}
    np.savez_compressed(os.path.join(OUT, "t2_profiles.npz"), **{f"{n}_{c}": np.asarray(p[i]) for n, p in prof.items()
                                                             for i, c in enumerate(("sL", "Vn", "Vt", "inmouth"))})
    res["_wall_s"] = time.time() - t0
    json.dump(res, open(os.path.join(OUT, "t2_results.json"), "w"), indent=1, default=float)
    # --- figures
    fieldfig("theta11", "t2_flowfield_11deg.png"); fieldfig("theta20", "t2_flowfield_20deg.png")
    cols = {"theta08": "#9ecae1", "theta11": "#08306b", "theta15": "#e6550d", "theta20": "#a50f15"}
    fig, ax = plt.subplots(1, 2, figsize=(13, 4.3))
    for n, c in cols.items():
        sL, Vn, Vt, im = prof[n]
        ax[0].plot(sL, np.where(im, np.nan, smooth(Vn)), color=c, label=f"{n[-2:]} deg (A={res[n]['stats']['area']:.0f} m2)")
        ax[1].plot(sL, np.where(im, np.nan, smooth(Vt/np.maximum(Vn, 1e-3))), color=c, label=f"{n[-2:]} deg")
    ax[0].axhline(0.10, color="k", ls="--", lw=0.8)
    ax[0].set(xlabel="s / L (0 = upstream end, 1 = apex)", ylabel="Vn [m/s] (2 m running mean)", title="Through-screen velocity vs angle")
    ax[1].set(xlabel="s / L", ylabel="Vt / Vn", ylim=(0, 20), title="Sweep-to-through ratio along the face")
    for a in ax: a.grid(alpha=.3); a.legend(fontsize=8)
    plt.tight_layout(); plt.savefig(os.path.join(FIG, "t2_face_vs_angle.png"), dpi=130); plt.close()
    fig, ax = plt.subplots(1, 3, figsize=(16, 4.3))
    for a, group, title in ((ax[0], ["beta0.3", "theta11", "beta0.7"], "porosity (beta 0.3 / 0.5 / 0.7)"),
                            (ax[1], ["fb0", "fb1", "theta11", "fb4", "fb2_term50", "sp15", "sp60"], "bypass fraction / spacing"),
                            (ax[2], ["theta11", "baffle10", "baffle30", "baffle100", "theta20", "theta20_baffle30"], "added back-baffle loss k_total")):
        for n in group:
            sL, Vn, Vt, im = prof[n]
            lab = {"theta11": "baseline 11deg beta0.5 fb2% 30m"}.get(n, n)
            a.plot(sL, np.where(im, np.nan, smooth(Vn)), label=lab)
        a.axhline(0.10, color="k", ls="--", lw=0.8); a.set(xlabel="s / L", ylabel="Vn [m/s]", title=title); a.grid(alpha=.3); a.legend(fontsize=7)
    plt.tight_layout(); plt.savefig(os.path.join(FIG, "t2_face_sensitivity.png"), dpi=130); plt.close()
    for n in CASES:
        s = res[n]["stats"]
        print(f"{n:18s} A={s['area']:6.0f} Vn mean {s['Vn_mean']:.3f} p95 {s['Vn_p95']:.3f} max {s['Vn_max']:.3f} "
              f"cv {s['Vn_cv']:.2f} >0.12:{s['frac_over_0p12']:.2f} Vt {s['Vt_mean']:.2f} Vt/Vn {s['sweep_ratio_mean']:.1f} "
              f"min {s['sweep_ratio_min_core']:.1f} conv {res[n]['info']['converged']} wall {res[n]['info']['wall']:.0f}s")
    print("total", time.time() - t0)
