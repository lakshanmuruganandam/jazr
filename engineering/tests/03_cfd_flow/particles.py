"""
particles.py - finite-size bell tracking on a solved lane flow (lane.py).

Bell model (all stated assumptions):
  * centre advected by the local depth-averaged velocity (RK2), plus optional swimming at speed `swim` with a
    random heading that diffuses with persistence time tau (correlated random walk).
  * finite size: bell radius r = D/2; the bell touches the screen when its centre is within r of the face line.
  * on the face: it cannot move through the mesh.  Normal (pinning) force  Fn = (k+1)*rho/2*Vn^2*A_n
    (screen pressure drop + stagnation on the blocked patch); tangential drag Ft = Cd*rho/2*Vt^2*A_t.
    It slides at the local sweep velocity if Ft > mu*Fn, otherwise it is held (impinged) unless it swims off.
    A_n = pi D^2/4 (bell disc), A_t = 0.5 D^2 (side profile), Cd = 1, mu = 0.5 (gel on wet mesh; unknown -> sensitivity).
    The fluid velocity used for contact forces and sliding is sampled at the bell centre + band half-width
    (just outside the smeared porous band).
  * bypass mouths: the face is open over the mouth span.  If the bell fits (|s - s_m| <= b/2 - r) it is free there
    and is CAPTURED when its centre crosses the face plane (d <= 0); at the mouth edges it is treated as on the face.
  * outcomes: 1 captured (by entrance index), 2 held on the face (impinged) at t_max, 0 still drifting at t_max
    (lingering, typically at the apex), 3 leaked to the downstream side, 4 swam back out of the lane inlet.
"""
import numpy as np
from jzcfd import Interp
from lane import centred


def track(G, n=1000, D=0.35, swim=0.0, tau=10.0, mu=0.5, Cd=1.0, dt=0.25, t_max=1800.0, seed=0,
          x_rel=5.0, s_bins=None, kprof_s=None, kprof_k=None, record=0):
    rng = np.random.default_rng(seed)
    P = G["P"]; W = P["W"]; r = D/2; dx = P["dx"]
    uc, vc = centred(G); I = Interp(uc, vc, dx)
    P0, t, nn, L, b = G["P0"], G["t"], G["n"], G["L"], P["b"]
    mouths = np.asarray(G["mouths"], float)
    dw = G.get("dw", dx)
    A_n, A_t = np.pi*D**2/4, 0.5*D**2
    x = np.full(n, x_rel); y = rng.uniform(r, W - r, n); ph = rng.uniform(0, 2*np.pi, n)
    out = np.zeros(n, int); ent = -np.ones(n, int); t_cap = np.full(n, np.nan); t_first = np.full(n, np.nan)
    held = np.zeros(n, bool); t_held = np.zeros(n)
    nb = 0 if s_bins is None else len(s_bins) - 1
    occ = np.zeros(nb)                                    # bell-seconds on the face per s-bin (all particles)
    tracks = []
    act = np.ones(n, bool); time = 0.0
    def kloc(s):
        if kprof_s is None: return P["k"]
        return np.interp(s, kprof_s, kprof_k)
    while act.any() and time < t_max:
        ia = np.nonzero(act)[0]
        xa, ya = x[ia], y[ia]
        u1, v1 = I(xa, ya); u2, v2 = I(xa + 0.5*dt*u1, ya + 0.5*dt*v1)
        ph[ia] += np.sqrt(2*dt/tau)*rng.standard_normal(ia.size)
        sx, sy = swim*np.cos(ph[ia]), swim*np.sin(ph[ia])
        xn = xa + dt*(u2 + sx); yn = ya + dt*(v2 + sy)
        yn = np.clip(yn, r, W - r)
        d = (xn - P0[0])*nn[0] + (yn - P0[1])*nn[1]
        s = (xn - P0[0])*t[0] + (yn - P0[1])*t[1]
        near = (d < r) & (s > -r) & (s < L + r)
        # mouths
        fits = np.zeros(ia.size, bool); midx = -np.ones(ia.size, int)
        if mouths.size:
            dm = np.abs(s[:, None] - mouths[None, :])
            j = np.argmin(dm, axis=1); dmin = dm[np.arange(ia.size), j]
            fits = dmin <= b/2 - r
            midx = np.where(dmin <= b/2, j, -1)
        cap = near & fits & (d <= 0)
        contact = near & ~fits
        # contact mechanics
        if contact.any():
            ic = np.nonzero(contact)[0]
            sc = np.clip(s[ic], 0, L)
            xs = P0[0] + sc*t[0] + (r + dw)*nn[0]; ys = P0[1] + sc*t[1] + (r + dw)*nn[1]
            uf, vf = I(xs, ys)
            Vn_t = -(uf*nn[0] + vf*nn[1])                 # toward the screen (+)
            Vt = uf*t[0] + vf*t[1]
            sw_n = -(sx[ic]*nn[0] + sy[ic]*nn[1]); sw_t = sx[ic]*t[0] + sy[ic]*t[1]
            Fn = 0.5*(kloc(sc) + 1)*A_n*np.maximum(Vn_t, 0)**2
            Ft = 0.5*Cd*A_t*Vt**2
            slide = Ft > mu*Fn
            off = (-sw_n) > np.maximum(Vn_t, 0)           # swims away faster than the through-flow pins it
            hold = ~slide & ~off
            ds = np.where(hold, 0.0, (Vt + sw_t)*dt)
            s_new = np.clip(sc + ds, -r, L + r)
            d_new = np.where(off, r + 0.25*dt*(-sw_n - np.maximum(Vn_t, 0)), r)
            xn[ic] = P0[0] + s_new*t[0] + d_new*nn[0]; yn[ic] = P0[1] + s_new*t[1] + d_new*nn[1]
            yn[ic] = np.clip(yn[ic], r, W - r)
            held[ia[ic]] = hold; t_held[ia[ic]] += hold*dt
            fresh = np.isnan(t_first[ia[ic]]); t_first[ia[ic[fresh]]] = time
            if nb:
                occ += np.histogram(sc, bins=s_bins)[0]*dt
        nc = ~contact
        held[ia[nc]] = False
        x[ia], y[ia] = xn, yn
        # outcomes
        if cap.any():
            ii = ia[cap]; out[ii] = 1; ent[ii] = midx[cap]; t_cap[ii] = time; act[ii] = False
        d2 = (x[ia] - P0[0])*nn[0] + (y[ia] - P0[1])*nn[1]
        s2 = (x[ia] - P0[0])*t[0] + (y[ia] - P0[1])*t[1]
        leak = act[ia] & (d2 < -r) & ((s2 > -r) & (s2 < L + r) | (x[ia] > G["x1"]))
        if leak.any(): out[ia[leak]] = 3; act[ia[leak]] = False
        back = act[ia] & (x[ia] < 0)
        if back.any(): out[ia[back]] = 4; act[ia[back]] = False
        if record and int(time/dt) % record == 0:
            tracks.append(np.c_[x[:200], y[:200]].copy())
        time += dt
    out[act & held] = 2
    res = dict(n=n, captured=float(np.mean(out == 1)), held=float(np.mean(out == 2)),
               lingering=float(np.mean(out == 0)), leaked=float(np.mean(out == 3)), back=float(np.mean(out == 4)),
               by_entrance=[float(np.mean(ent == m)) for m in range(len(mouths))],
               t_face_to_capture_median=float(np.nanmedian(t_cap - t_first)) if np.any(out == 1) else None,
               t_face_to_capture_p90=float(np.nanpercentile(t_cap - t_first, 90)) if np.any(out == 1) else None,
               held_time_mean=float(t_held.mean()))
    res["_out"] = out; res["_ent"] = ent; res["_occ"] = occ; res["_tracks"] = tracks
    res["_final"] = np.c_[x, y]
    return res


def public(res):
    return {k: v for k, v in res.items() if not k.startswith("_")}
