"""
T5 - Outer guide line: partial-depth roll-down curtains at 15-25 deg to the tidal current.
Part A (vertical slice, n-z plane normal to the line, 2.5D): flow under / through a curtain of depth d_c in water
  depth H = 3.5 m (twin offshore depth), mesh (beta 0.5, k = 1.65) or solid, d_c/H = 0.5 / 0.75.
  -> share of flow passing through the mesh vs under the tip, effective depth-averaged loss k_eff,
     and the downward velocity w(z) on the upstream face (what carries a pinned bell down to the tip).
Part B (plan view, depth-averaged): tidal current U = 0.117 m/s (twin's peak M2 amplitude) past a 1000 m line at
  alpha = 15/20/25 deg, represented as a porous line with k_eff from Part A, with/without 10 m turtle gaps every
  100 m.  3000 bells (D 0.35 m, passive or 3.6 cm/s swim) with a depth coordinate: bells below the curtain tip pass
  under; bells on the face slide along it at the local sweep velocity and sink at w(z) (scaled by local Vn) until
  they clear the tip.  eta_g = bells delivered to the downstream end of the line / bells that met the line.
Outputs: data/t5_results.json, figs/t5_slice.png, figs/t5_planview.png, figs/t5_eta.png
"""
import sys, os, json, time, itertools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from multiprocessing import Pool
from jzcfd import Flow2D, Interp, k_wire, alpha_refr

HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "data"); FIG = os.path.join(HERE, "figs")
H = 3.5; U0 = 0.117; K_MESH = float(k_wire(0.5)); D = 0.35; R = D/2


# ------------------------------------------------------------------ Part A: vertical slice
def slice_case(args):
    dcH, kind, Un, dz = args
    Lx = 60.0; nx, nz = int(Lx/dz), int(round(H/dz)); xc = 30.0
    xcen = (np.arange(nx) + 0.5)*dz; zcen = (np.arange(nz) + 0.5)*dz
    X, Z = np.meshgrid(xcen, zcen, indexing="ij")
    tip = H*(1 - dcH)
    fluid = np.ones((nx, nz), bool); Kq = np.zeros((nx, nz)); Kt = np.zeros((nx, nz))
    if kind == "solid":
        fluid[(np.abs(X - xc) < dz/2 + 1e-9) & (Z > tip)] = False
    else:
        w = np.where(np.abs(X - xc) < dz, (1 - np.abs(X - xc)/dz)/dz, 0.0)*(Z > tip)
        Kq = 0.5*K_MESH*w; Kt = -np.log(alpha_refr(K_MESH))*w
    F = Flow2D(nx, nz, dz, fluid=fluid, Kq=Kq, Kt=Kt, u_in=Un, nu=0.0015, fric=0.0, cfl=0.3, umax=4*Un,
               dt_max=0.5/(Kq.max()*0.2 + 1e-9))
    F.run(t_min=600, t_max=4000, tol=1e-7, wall_max=500, avg=800)
    uc, vc = F.centred(); I = Interp(uc, vc, dz)
    # flux through curtain zone vs under
    i_c = int(xc/dz)
    q_through = F.u[i_c, :][zcen > tip].sum()*dz if kind != "solid" else 0.0
    q_tot = F.u[0].sum()*dz
    pm = F.p.mean(axis=1); up = (xcen > xc - 25) & (xcen < xc - 8); dn = (xcen > xc + 8) & (xcen < xc + 25)
    dp = np.polyval(np.polyfit(xcen[up], pm[up], 1), xc) - np.polyval(np.polyfit(xcen[dn], pm[dn], 1), xc)
    zz = np.linspace(tip + 0.02, H - 0.02, 60)
    off = R + dz
    u_f, w_f = I(np.full_like(zz, xc - off), zz)
    return dict(dcH=dcH, kind=kind, Un=Un, dz=dz, frac_through=float(q_through/q_tot), k_eff=float(dp/(0.5*Un**2)),
                depth_below_surface=(H - zz).tolist(), w_down_over_Un=(-w_f/Un).tolist(), un_over_Un=(u_f/Un).tolist(),
                mass_imb=F.mass_balance()["imbalance"], converged=bool(F.converged),
                field=(uc[::2, ::1].tolist(), vc[::2, ::1].tolist()) if dz >= 0.05 else None, nx=nx, nz=nz)


# ------------------------------------------------------------------ Part B: plan view
LX, LY, DXP, X0, Y0, LG = 1800.0, 900.0, 10.0, 300.0, 150.0, 1000.0


def plan_flow(alpha, k_eff):
    nx, ny = int(LX/DXP), int(LY/DXP); a = np.radians(alpha)
    t = np.array([np.cos(a), np.sin(a)]); n = np.array([-t[1], t[0]])
    xc = (np.arange(nx) + 0.5)*DXP; yc = (np.arange(ny) + 0.5)*DXP
    X, Y = np.meshgrid(xc, yc, indexing="ij")
    d = (X - X0)*n[0] + (Y - Y0)*n[1]; s = (X - X0)*t[0] + (Y - Y0)*t[1]
    Kq = np.zeros((nx, ny)); Kt = np.zeros((nx, ny)); nvec = np.zeros((nx, ny, 2)); nvec[..., 0] = 1
    if np.isfinite(k_eff):
        wgt = np.where((np.abs(d) < DXP) & (s >= 0) & (s <= LG), (1 - np.abs(d)/DXP)/DXP, 0.0)
        Kq = 0.5*k_eff*wgt; Kt = -np.log(alpha_refr(k_eff))*wgt; nvec[wgt > 0] = n
        fluid = np.ones((nx, ny), bool)
    else:   # impermeable full-depth line
        fluid = ~((np.abs(d) < 0.75*DXP) & (s >= 0) & (s <= LG))
    F = Flow2D(nx, ny, DXP, fluid=fluid, Kq=Kq, Kt=Kt, nvec=nvec, u_in=U0, nu=0.2, fric=0.0025/H, cfl=0.3,
               umax=0.3, dt_max=0.5/(Kq.max()*0.1 + 1e-9))
    F.run(t_min=6000, t_max=30000, tol=2e-8, wall_max=3000, avg=6000)
    return F, t, n


def plan_flow_cached(args):
    alpha, ckey, k_eff = args
    fn = os.path.join(OUT, "cache_v3", f"t5_plan_{alpha:.0f}_{ckey}.npz")
    if not os.path.exists(fn):
        F, t, n = plan_flow(alpha, k_eff); uc, vc = F.centred()
        np.savez_compressed(fn, uc=uc, vc=vc, converged=F.converged, imb=F.mass_balance()["imbalance"], wall=F.wall)
    Z = np.load(fn)
    return Z["uc"], Z["vc"], bool(Z["converged"]), float(Z["imb"])


def plan_case(args):
    alpha, ckey, k_eff, dcH, wprof, gaps, swim, depth_mode = args
    a = np.radians(alpha); t = np.array([np.cos(a), np.sin(a)]); n = np.array([-t[1], t[0]])
    uc, vc, conv, imb = plan_flow_cached((alpha, ckey, k_eff)); I = Interp(uc, vc, DXP)
    rng = np.random.default_rng(3); N = 3000; dt = 5.0; dc = dcH*H
    x = np.full(N, 30.0); y = rng.uniform(5, LY - 5, N); ph = rng.uniform(0, 2*np.pi, N)
    zeta = rng.uniform(0, H if depth_mode == "uniform" else H/2, N)       # depth below surface
    state = np.zeros(N, int)   # 0 free/never met, 1 on face, 2 guided (left at end), 3 via gap, 4 under tip, 5 below tip at meeting
    met = np.zeros(N, bool)
    zz, wn = (np.array(wprof[0]), np.array(wprof[1])) if wprof is not None else (None, None)
    gap_c = np.arange(100.0, LG - 1, 100.0) if gaps else np.array([])
    def in_gap(s): return np.any(np.abs(s[:, None] - gap_c[None, :]) < 5.0, axis=1) if gap_c.size else np.zeros(s.size, bool)
    # geometry: flow is toward +x, so the UPSTREAM side of the line is d > 0 (n = (-sin a, cos a)).
    passed = np.zeros(N, bool)          # already crossed (under/below tip/gap) -> no further contact
    Pt = lambda s_, dd: (X0 + s_*t[0] + dd*n[0], Y0 + s_*t[1] + dd*n[1])
    for it in range(int(40000/dt)):
        free = state != 1
        u, v = I(x, y); ph += np.sqrt(2*dt/10.0)*rng.standard_normal(N)
        swx, swy = swim*np.cos(ph), swim*np.sin(ph)
        xn = np.where(free, x + dt*(u + swx), x); yn = np.where(free, y + dt*(v + swy), y)
        yn = np.clip(yn, 1, LY - 1)
        d_old = (x - X0)*n[0] + (y - Y0)*n[1]
        d = (xn - X0)*n[0] + (yn - Y0)*n[1]; s = (xn - X0)*t[0] + (yn - Y0)*t[1]
        hit = free & ~passed & (d_old >= R) & (d < R) & (s >= 0) & (s <= LG) & ~in_gap(s)
        met |= hit
        bl = hit & (zeta > dc); state[bl] = 5; passed[bl] = True          # below the tip: passes under
        on = hit & ~bl; state[on] = 1
        xn[on], yn[on] = Pt(s[on], R)
        x, y = xn, yn
        i = np.nonzero(state == 1)[0]
        if i.size:
            si = (x[i] - X0)*t[0] + (y[i] - Y0)*t[1]
            sx, sy = Pt(si, R + DXP); uf, vf = I(sx, sy)
            Vt = uf*t[0] + vf*t[1]; Vn = np.maximum(-(uf*n[0] + vf*n[1]), 0)
            s_new = si + (Vt + swx[i]*t[0] + swy[i]*t[1])*dt
            if zz is not None:
                zeta[i] += np.maximum(np.interp(zeta[i], zz, wn), 0)*Vn*dt
            und = zeta[i] > dc
            end = ~und & ((s_new > LG) | (s_new < 0))
            gp = ~und & ~end & in_gap(s_new)
            stay = ~und & ~end & ~gp
            xs_, ys_ = Pt(s_new, R); x[i] = xs_; y[i] = ys_
            xd, yd = Pt(s_new, -2*R)
            for msk, code, down in ((und, 4, True), (end, 2, False), (gp, 3, True)):
                j = i[msk]; state[j] = code; passed[j] = True
                if down: x[j], y[j] = xd[msk], yd[msk]
        if np.all((x > LX - 50) | (state == 1) & False): break
    metc = met.sum()
    res = dict(alpha=alpha, curtain=ckey, k_eff=k_eff, dcH=dcH, gaps=gaps, swim=swim, depth_mode=depth_mode,
               met=int(metc), guided=int((state == 2).sum()), via_gap=int((state == 3).sum()),
               under=int((state == 4).sum()), below_tip=int((state == 5).sum()), stuck_on_face=int((state == 1).sum()),
               eta_g=float((state == 2).sum()/max(metc, 1)), converged=conv, mass_imb=imb)
    if swim == 0 and depth_mode == "uniform" and gaps:
        res["_field"] = (uc, vc)
    return res


if __name__ == "__main__":
    t0 = time.time()
    part = sys.argv[1] if len(sys.argv) > 1 else "all"
    if part in ("A", "all"):
        jobs = [(dcH, kind, U0*np.sin(np.radians(20)), dz) for dcH in (0.5, 0.75) for kind in ("mesh", "solid") for dz in (0.2, 0.1)]
        with Pool(8) as pool:
            SA = pool.map(slice_case, jobs)
        json.dump(SA, open(os.path.join(OUT, "t5_slice.json"), "w"), default=float)
        for r in SA:
            print(f"slice d_c/H={r['dcH']} {r['kind']:5s} dz={r['dz']} through-mesh {r['frac_through']:.2f} k_eff {r['k_eff']:.2f} "
                  f"w/Un at mid-curtain {np.interp(0.5*r['dcH']*H, r['depth_below_surface'][::-1], r['w_down_over_Un'][::-1]):.2f} "
                  f"conv {r['converged']} imb {r['mass_imb']:.1e}", flush=True)
        fig, ax = plt.subplots(1, 2, figsize=(12, 4.3))
        for r in SA:
            if r["dz"] != 0.1: continue
            ax[0].plot(r["w_down_over_Un"], r["depth_below_surface"], label=f"{r['kind']} d_c/H={r['dcH']}")
        ax[0].invert_yaxis(); ax[0].set(xlabel="downward velocity on upstream face / approach Un", ylabel="depth below surface [m]",
                                        title=f"Curtain face downdraft (H={H} m, {R+0.05:.2f} m from face)"); ax[0].legend(fontsize=8); ax[0].grid(alpha=.3)
        r = [q for q in SA if q["kind"] == "solid" and q["dcH"] == 0.5 and q["dz"] == 0.1][0]
        uc, vc = np.array(r["field"][0]), np.array(r["field"][1])
        xx = (np.arange(uc.shape[0])*2 + 0.5)*0.1; zz_ = (np.arange(uc.shape[1]) + 0.5)*0.1
        ax[1].streamplot(xx, zz_, uc.T, vc.T, density=1.6, color=np.hypot(uc, vc).T, cmap="viridis", linewidth=0.7)
        ax[1].plot([30, 30], [H*0.5, H], "k-", lw=3); ax[1].set(xlim=(20, 40), xlabel="n [m]", ylabel="z above bed [m]",
                                                                title="Solid curtain d_c/H = 0.5: all flow dives under the tip")
        plt.tight_layout(); plt.savefig(os.path.join(FIG, "t5_slice.png"), dpi=130); plt.close()
    if part in ("B", "all"):
        SA = json.load(open(os.path.join(OUT, "t5_slice.json")))
        curt = {}
        for r in SA:
            if r["dz"] != 0.1: continue
            zz = np.array(r["depth_below_surface"][::-1]); wn = np.array(r["w_down_over_Un"][::-1])
            curt[f"{r['kind']}_{r['dcH']}"] = (r["k_eff"], r["dcH"], (zz.tolist(), wn.tolist()))
        curt["fullmesh_1.0"] = (K_MESH, 1.0, None)
        jobs = [(a, ck, kv[0], kv[1], kv[2], g, sw, dm) for a in (15.0, 20.0, 25.0) for ck, kv in curt.items()
                for g in (False, True) for sw in (0.0, 0.036) for dm in ("uniform", "upper")]
        with Pool(8) as pool:
            fl = pool.map(plan_flow_cached, sorted({(j[0], j[1], j[2]) for j in jobs}, key=str))
            for (a_, ck_, _), f_ in zip(sorted({(j[0], j[1], j[2]) for j in jobs}, key=str), fl):
                print("plan flow", a_, ck_, "converged" if f_[2] else "time-averaged", f"imbalance {f_[3]:.1e}", flush=True)
            SB = pool.map(plan_case, jobs, chunksize=2)
        fields = {(r["alpha"], r["curtain"]): r.pop("_field") for r in SB if "_field" in r}
        json.dump(SB, open(os.path.join(OUT, "t5_results.json"), "w"), default=float, indent=0)
        for r in SB:
            if r["swim"] == 0:
                print(f"a={r['alpha']:.0f} {r['curtain']:12s} gaps={r['gaps']!s:5s} depth={r['depth_mode']:7s} met {r['met']:4d} "
                      f"eta_g {r['eta_g']:.2f} (guided {r['guided']}, gap {r['via_gap']}, under {r['under']}, below {r['below_tip']}, "
                      f"face {r['stuck_on_face']}) conv {r['converged']}")
        # figures
        fig, ax = plt.subplots(1, 2, figsize=(13, 4.5))
        for (a, ck), (uc, vc) in fields.items():
            if a == 20.0 and ck == "mesh_0.75":
                X = (np.arange(uc.shape[0]) + 0.5)*DXP; Y = (np.arange(uc.shape[1]) + 0.5)*DXP
                im = ax[0].pcolormesh(X, Y, np.hypot(uc, vc).T, shading="auto", cmap="viridis")
                ax[0].streamplot(X, Y, uc.T, vc.T, density=1.5, color="w", linewidth=0.5)
                tt = np.array([np.cos(np.radians(a)), np.sin(np.radians(a))])
                ax[0].plot([X0, X0 + LG*tt[0]], [Y0, Y0 + LG*tt[1]], "r-", lw=1.5); plt.colorbar(im, ax=ax[0], label="|u| m/s")
                ax[0].set(aspect="equal", title="Plan view: 20 deg mesh curtain (d_c/H 0.75), U = 0.117 m/s", xlabel="x [m]", ylabel="y [m]")
        for ck, c in zip(curt, ("#08306b", "#6baed6", "#a50f15", "#fc9272", "#31a354")):
            for g, ls in ((False, "-"), (True, "--")):
                yv = [np.mean([r["eta_g"] for r in SB if r["alpha"] == a and r["curtain"] == ck and r["gaps"] == g]) for a in (15, 20, 25)]
                ax[1].plot((15, 20, 25), yv, ls, marker="o", color=c, label=f"{ck}{' + gaps' if g else ''}")
        ax[1].axhspan(0.4, 0.6, color="grey", alpha=0.2, label="twin assumption eta_g 0.4-0.6")
        ax[1].set(xlabel="line angle to current [deg]", ylabel="eta_g (delivered to line end / met line)", ylim=(0, 1.05),
                  title="Guide-line efficiency (mean over swim 0/3.6 cm/s, depth uniform/upper)"); ax[1].legend(fontsize=7); ax[1].grid(alpha=.3)
        plt.tight_layout(); plt.savefig(os.path.join(FIG, "t5_planview_eta.png"), dpi=130); plt.close()
    print("wall", time.time() - t0)
