"""
T1 - Verification of the CFD core.
 (a) porous-jump calibration: screen normal to the flow (theta = 90 deg); measured pressure drop vs k*U^2/2
 (b) refraction calibration: 45-deg screen; tangential velocity kept across the screen vs alpha = 1.1/sqrt(1+k)
 (c) mass balance and screen water-tightness (every run)
 (d) grid convergence of the 11-deg baseline lane: dx = 1.0, 0.5, 0.25 m; Richardson extrapolation + GCI
Outputs: data/t1_verification.json, figs/t1_grid_convergence.png
"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from multiprocessing import Pool
from lane import solve, face_profile, screen_stats, centred, HERE
from jzcfd import Interp, k_wire, alpha_refr

OUT = os.path.join(HERE, "data"); FIG = os.path.join(HERE, "figs")


def jump_case(k):
    G = solve(dict(theta=90.0, spacing=0, fb=0.0, k=k, dx=0.5, L_up=50.0, L_down=50.0, Cf=0.0), t_max=800, t_min=300)
    uc, vc = centred(G); dx = 0.5
    x = (np.arange(G["nx"]) + 0.5)*dx; p = G["p"].mean(axis=1)
    # fit linear (friction-free => flat) pressure on each side away from the band, extrapolate to the screen
    xs = G["x0"]; up = (x > xs - 30) & (x < xs - 5); dn = (x > xs + 5) & (x < xs + 30)
    pu = np.polyval(np.polyfit(x[up], p[up], 1), xs); pd = np.polyval(np.polyfit(x[dn], p[dn], 1), xs)
    U = G["U_in"]
    return dict(k=k, U=U, dp_cfd=float(pu - pd), dp_theory=float(k*U**2/2), ratio=float((pu - pd)/(k*U**2/2)),
                mass=G["info"]["mass"], watertight=G["info"]["watertight"], converged=G["info"]["converged"])


def refr_case(k):
    G = solve(dict(theta=45.0, spacing=0, fb=0.0, k=k, dx=0.5, Cf=0.0), t_max=900, t_min=300)
    uc, vc = centred(G); I = Interp(uc, vc, 0.5)
    t, n, P0, L = G["t"], G["n"], G["P0"], G["L"]
    s = np.linspace(0.35*L, 0.65*L, 21); out = {}
    for lab, dd in (("up", 3.0), ("dn", -3.0)):
        x = P0[0] + s*t[0] + dd*n[0]; y = P0[1] + s*t[1] + dd*n[1]
        u, v = I(x, y); out[lab] = (float(np.mean(u*t[0] + v*t[1])), float(np.mean(-(u*n[0] + v*n[1]))))
    return dict(k=k, Vt_up=out["up"][0], Vt_dn=out["dn"][0], Vn_up=out["up"][1], Vn_dn=out["dn"][1],
                ratio_cfd=out["dn"][0]/out["up"][0], alpha_theory=float(alpha_refr(k)),
                mass=G["info"]["mass"], converged=G["info"]["converged"])


def grid_case(dx):
    tm = {1.0: 1500, 0.5: 1500, 0.25: 1000}[dx]; av = {1.0: 500, 0.5: 500, 0.25: 350}[dx]
    G = solve(dict(dx=dx), t_max=tm, avg=av)
    F = face_profile(G, ds=0.25); st = screen_stats(G)
    L = G["L"]; s = F["s"]
    def mid(sa, sb, a): m = (s > sa*L) & (s < sb*L) & ~F["inmouth"]; return float(np.mean(a[m]))
    return dict(dx=dx, ncells=G["info"]["ncells"], wall=G["info"]["wall"], converged=G["info"]["converged"],
                n_avg=G["info"]["n_avg"], mass=G["info"]["mass"], watertight=G["info"]["watertight"],
                Vn_q1=mid(0.05, 0.15, F["Vn"]), Vn_q3=mid(0.60, 0.75, F["Vn"]), Vn_end=mid(0.85, 0.97, F["Vn"]),
                Vt_q1=mid(0.05, 0.15, F["Vt"]), Vt_q3=mid(0.60, 0.75, F["Vt"]),
                Vn_max_core=st["Vn_max_core"], flux_screen=st["flux_screen"], flux_expected=st["flux_expected"],
                dp_inlet_outlet=float(G["p"][0].mean() - G["p"][-1].mean()),
                profile=(s.tolist(), F["Vn"].tolist(), F["Vt"].tolist()))


def gci(f1, f2, f3, r=2.0):
    """f1 finest. Roache GCI with observed order p (bounded to [0.5, 4])."""
    e21, e32 = f2 - f1, f3 - f2
    if abs(e21) < 1e-12: return dict(p=None, f_ext=f1, gci_fine=0.0)
    ratio = e32/e21
    p = np.log(abs(ratio))/np.log(r) if ratio > 0 else np.nan
    p_used = float(np.clip(p, 0.5, 4.0)) if np.isfinite(p) else 1.0
    f_ext = f1 + (f1 - f2)/(r**p_used - 1)
    g = 1.25*abs((f1 - f2)/f1)/(r**p_used - 1)
    return dict(p_obs=None if not np.isfinite(p) else float(p), p_used=p_used, f_ext=float(f_ext),
                gci_fine=float(g), monotone=bool(ratio > 0))


if __name__ == "__main__":
    t0 = time.time()
    with Pool(8) as pool:
        rj = pool.map_async(jump_case, [float(k_wire(b)) for b in (0.7, 0.5, 0.3)])
        rr = pool.map_async(refr_case, [float(k_wire(0.5)), float(k_wire(0.3))])
        rg = pool.map_async(grid_case, [1.0, 0.5, 0.25])
        J, R, Gc = rj.get(), rr.get(), rg.get()
    res = dict(jump=J, refraction=R, grid=[{k: v for k, v in g.items() if k != "profile"} for g in Gc])
    keys = ["Vn_q1", "Vn_q3", "Vn_end", "Vt_q1", "Vt_q3", "Vn_max_core", "dp_inlet_outlet"]
    g1, g2, g3 = Gc[2], Gc[1], Gc[0]
    res["gci"] = {k: gci(g1[k], g2[k], g3[k]) for k in keys}
    res["wall_total_s"] = time.time() - t0
    json.dump(res, open(os.path.join(OUT, "t1_verification.json"), "w"), indent=1, default=float)
    # figure
    fig, ax = plt.subplots(1, 2, figsize=(12, 4.2))
    for g, c in zip(Gc, ("#bbbbbb", "#6a8fd8", "#1b2a6b")):
        s, Vn, Vt = map(np.asarray, g["profile"])
        ax[0].plot(s, Vn, color=c, lw=1.4, label=f"dx = {g['dx']} m ({g['ncells']} cells)")
        ax[1].plot(s, Vt, color=c, lw=1.4, label=f"dx = {g['dx']} m")
    ax[0].axhline(0.10, color="k", ls="--", lw=0.8); ax[0].text(2, 0.103, "design 0.10 m/s", fontsize=8)
    ax[0].set(xlabel="distance along face from upstream end s [m]", ylabel="through-screen velocity Vn [m/s]",
              title="Grid convergence: through-screen velocity (11 deg, 2% bypass, 5 entrances)")
    ax[1].set(xlabel="s [m]", ylabel="sweep velocity Vt at 1 m from face [m/s]", title="Sweep velocity")
    for a in ax: a.legend(fontsize=8); a.grid(alpha=0.3)
    plt.tight_layout(); plt.savefig(os.path.join(FIG, "t1_grid_convergence.png"), dpi=130)
    print(json.dumps({k: v for k, v in res.items()}, indent=1, default=float)[:6000])
