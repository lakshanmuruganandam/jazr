"""
lane.py - geometry, flow solve and face diagnostics for one JAZR training-walled intake lane (plan view).

Lane: x streamwise, 0 <= y <= W (training walls, free slip).  Inlet at x=0 carries Q/h per metre depth.
Screen: straight line from P0 = (x0, W) (upstream end, on the far wall) to P1 = (x0 + W/tan(theta), 0) (apex).
  n = unit normal pointing to the UPSTREAM side, t = unit tangent pointing along the face toward the apex.
Bypass entrances: mouths of width b in the face at along-face positions s = L - b/2 - k*spacing (k = 0,1,...);
  k = 0 is the terminal (apex) entrance.  Inside each mouth the band cells become sink cells (bypass draw,
  equal share of f_b*Q per entrance) and a solid back-wall is placed behind, so the bypass draws only from the
  upstream (fish/bell) side.
"""
import numpy as np, os, json, hashlib
from jzcfd import Flow2D, Interp, k_wire, alpha_refr

BASE = dict(W=28.0, h=7.0, Q=100.0, theta=11.0, L_up=30.0, L_down=40.0, dx=0.5, k=float(k_wire(0.5)),
            fb=0.02, spacing=30.0, b=2.0, nu=0.012, Cf=0.0025, lam=0.0, wband=1.0, terminal=True, split="equal",
            kprof=None)

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "data", "cache_v3"); os.makedirs(CACHE, exist_ok=True)


def geometry(P):
    W, dx, th = P["W"], P["dx"], np.radians(P["theta"])
    x0 = P["L_up"]; x1 = x0 + W/np.tan(th); L = W/np.sin(th)
    Lx = np.ceil((x1 + P["L_down"])/dx)*dx
    nx, ny = int(round(Lx/dx)), int(round(W/dx))
    P0 = np.array([x0, W]); P1 = np.array([x1, 0.0]); t = (P1 - P0)/L
    n = np.array([-t[1], t[0]])
    if np.dot(np.array([0.0, W/2]) - P0, n) < 0: n = -n
    xc = (np.arange(nx) + 0.5)*dx; yc = (np.arange(ny) + 0.5)*dx
    X, Y = np.meshgrid(xc, yc, indexing="ij")
    d = (X - P0[0])*n[0] + (Y - P0[1])*n[1]
    s = (X - P0[0])*t[0] + (Y - P0[1])*t[1]
    deff = (abs(n[0]) + abs(n[1]))*dx                      # thickness of a 4-connected digital line
    dw = max(P["wband"]*dx, deff/2 + 1e-9)                   # half-width of the smeared porous band
    band = (np.abs(d) < dw) & (s > -2*dx) & (s < L + 2*dx)
    wgt = np.where(band, (1 - np.abs(d)/dw)/dw, 0.0)          # hat weights, integral over d = 1
    # bypass mouths
    mouths = []
    if P["spacing"] and P["spacing"] > 0:
        sm = L - P["b"]/2; kk = 0
        while sm - P["b"]/2 > 0.5*P["spacing"] or kk == 0:
            if (kk > 0) or P["terminal"]:
                mouths.append(sm)
            kk += 1; sm = L - P["b"]/2 - kk*P["spacing"]
            if sm - P["b"]/2 < 2.0: break
    fluid = np.ones((nx, ny), bool); sink = np.zeros((nx, ny))
    Kq = np.zeros((nx, ny)); lam = np.zeros((nx, ny)); Kt = np.zeros((nx, ny)); nvec = np.zeros((nx, ny, 2)); nvec[..., 0] = 1
    kfield = np.full((nx, ny), P["k"])
    if P.get("kprof") is not None:                         # along-face k profile (clogging), (s_edges, k_values)
        se, kv = P["kprof"]
        kfield = np.interp(s, 0.5*(np.asarray(se[:-1]) + np.asarray(se[1:])), kv)
    Kq[band] = 0.5*kfield[band]*wgt[band]
    Kt[band] = -np.log(alpha_refr(kfield[band]))*wgt[band]
    lam[band] = P["lam"]; nvec[band] = n
    Qb = P["fb"]*P["Q"]; nm = max(len(mouths), 1)
    if P["split"] == "equal":
        share = np.full(len(mouths), 1.0/nm)
    else:   # "terminal50": half to apex entrance, rest equally
        share = np.full(len(mouths), 0.5/max(nm - 1, 1)); share[0] = 0.5 if nm > 1 else 1.0
    mouth_cells = []
    for m, sm in enumerate(mouths):
        inspan = (s >= sm - P["b"]/2) & (s <= sm + P["b"]/2)
        mc = band & inspan
        back = inspan & (d <= -dw) & (d >= -dw - 2*dx)
        fluid[back] = False
        Kq[mc] = 0.0; lam[mc] = 0.0; Kt[mc] = 0.0
        q_e = share[m]*Qb/P["h"]                         # m^2/s per entrance
        sink[mc] += q_e/(mc.sum()*dx*dx)
        mouth_cells.append(mc)
    # anything in the apex wedge downstream of the solid back of the terminal mouth that is cut off -> solid
    from scipy import ndimage
    lab, nlab = ndimage.label(fluid)
    inlet_lab = lab[0, ny//2]
    fluid &= (lab == inlet_lab)
    G = dict(P=P, nx=nx, ny=ny, Lx=Lx, x0=x0, x1=x1, L=L, P0=P0, P1=P1, t=t, n=n, deff=deff, d=d, s=s,
             band=band, mouths=mouths, share=share, mouth_cells=mouth_cells, fluid=fluid, sink=sink,
             Kq=Kq, lam=lam, Kt=Kt, nvec=nvec, dw=dw, U_in=P["Q"]/(P["W"]*P["h"]))
    return G


def watertight(G):
    """True if the screen band (plus mouths/solids) separates the upstream region from the downstream one."""
    from scipy import ndimage
    open_ = G["fluid"] & ~G["band"]
    lab, _ = ndimage.label(open_)
    up = lab[0, G["ny"]//2]; dn = lab[-1, G["ny"]//2]
    return bool(up != dn)


def key(P):
    def rnd(v):
        if isinstance(v, (np.ndarray, tuple, list)): return [rnd(x) for x in v]
        return round(float(v), 4) if isinstance(v, (float, np.floating)) else v
    Pk = {k: (rnd(v) if isinstance(v, (np.ndarray, tuple, list)) else v) for k, v in P.items()}
    return hashlib.md5(json.dumps(Pk, sort_keys=True).encode()).hexdigest()[:12]


def solve(P=None, t_max=1200.0, t_min=400.0, tol=1e-5, avg=400.0, verbose=False, use_cache=True, init=None, wall_max=900, **kw):
    P = dict(BASE, **(P or {}), **kw)
    fn = os.path.join(CACHE, key(P) + ".npz")
    G = geometry(P)
    if use_cache and os.path.exists(fn):
        Z = np.load(fn, allow_pickle=True); inf = json.loads(str(Z["info"]))
        if inf.get("converged") or inf.get("n_avg", 0) > 0 or avg == 0:   # else: unsteady snapshot -> recompute
            G.update(u=Z["u"], v=Z["v"], p=Z["p"], info=inf)
            return G
    F = Flow2D(G["nx"], G["ny"], P["dx"], fluid=G["fluid"], sink=G["sink"], Kq=G["Kq"], lam=G["lam"], Kt=G["Kt"],
               nvec=G["nvec"], u_in=G["U_in"], nu=P["nu"], fric=P["Cf"]/P["h"], cfl=0.3, umax=1.2,
               dt_max=0.5/(G["Kq"].max()*0.2 + 1e-9))
    if init is not None:                                   # warm start from a previous (same-grid) solution
        F.u, F.v = init[0].copy(), init[1].copy()
    F.run(t_min=t_min, t_max=t_max, tol=tol, wall_max=wall_max, avg=avg, verbose=verbose)
    mb = F.mass_balance()
    info = dict(mass=mb, res=float(F.res), t_end=float(F.t), wall=float(F.wall), nsteps=F.nsteps, dt=F.dt, converged=bool(F.converged), n_avg=int(F.n_avg),
                ncells=int(G["fluid"].sum()), watertight=watertight(G))
    np.savez_compressed(fn, u=F.u, v=F.v, p=F.p, info=json.dumps(info))
    G.update(u=F.u, v=F.v, p=F.p, info=info)
    return G


def centred(G):
    uc = 0.5*(G["u"][:-1] + G["u"][1:]); vc = 0.5*(G["v"][:, :-1] + G["v"][:, 1:])
    return np.where(G["fluid"], uc, 0), np.where(G["fluid"], vc, 0)


def face_profile(G, ds=None, d_sweep=1.0):
    """Along-face profiles.  Vn: normal (through-screen) velocity on the band centre line (positive = through,
    i.e. from upstream to downstream side).  Vt: tangential (sweep, toward apex) velocity at distance d_sweep
    upstream of the face.  Through-flux check: integral Vn ds * h."""
    dx = G["P"]["dx"]; ds = ds or dx/2
    uc, vc = centred(G); I = Interp(uc, vc, dx)
    s = np.arange(ds/2, G["L"], ds)
    P0, t, n = G["P0"], G["t"], G["n"]
    def at(dd):
        x = P0[0] + s*t[0] + dd*n[0]; y = P0[1] + s*t[1] + dd*n[1]
        return I(x, y)
    u0, v0 = at(0.0); Vn = -(u0*n[0] + v0*n[1])
    u1, v1 = at(d_sweep); Vt = u1*t[0] + v1*t[1]; Vn_up = -(u1*n[0] + v1*n[1])
    inmouth = np.zeros_like(s, bool)
    for sm in G["mouths"]:
        inmouth |= np.abs(s - sm) <= G["P"]["b"]/2
    return dict(s=s, Vn=Vn, Vt=Vt, Vn_up=Vn_up, inmouth=inmouth, ds=ds)


def screen_stats(G):
    F = face_profile(G); m = ~F["inmouth"]
    Vn, Vt, s = F["Vn"][m], F["Vt"][m], F["s"][m]
    L = G["L"]; core = (s > 0.05*L) & (s < 0.95*L)
    h, Q = G["P"]["h"], G["P"]["Q"]
    flux_screen = np.sum(F["Vn"][m])*F["ds"]*h
    return dict(L=float(L), area=float(L*h), Vn_design=float(Q*(1 - G["P"]["fb"])/(L*h)),
                Vn_mean=float(Vn.mean()), Vn_max=float(Vn.max()), Vn_min=float(Vn.min()),
                Vn_p95=float(np.percentile(Vn, 95)), Vn_cv=float(Vn.std()/Vn.mean()),
                Vn_max_core=float(Vn[core].max()), s_at_Vn_max=float(s[np.argmax(Vn)]),
                frac_over_0p12=float(np.mean(Vn > 0.12)), frac_over_1p5mean=float(np.mean(Vn > 1.5*Vn.mean())),
                Vt_mean=float(Vt.mean()), Vt_min_core=float(Vt[core].min()),
                sweep_ratio_mean=float(np.mean(Vt[core])/np.mean(Vn[core])),
                sweep_ratio_min_core=float(np.min(Vt[core]/np.maximum(Vn[core], 1e-6))),
                flux_screen=float(flux_screen), flux_expected=float(Q*(1 - G["P"]["fb"])),
                dp_mean=None)


def status(P):
    """'ok' (converged or time-averaged), 'snap' (unsteady snapshot, not usable) or 'missing'."""
    P = dict(BASE, **P); fn = os.path.join(CACHE, key(P) + ".npz")
    if not os.path.exists(fn): return "missing"
    i = json.loads(str(np.load(fn, allow_pickle=True)["info"]))
    return "ok" if (i["converged"] or i["n_avg"] > 0) else "snap"
