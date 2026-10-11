"""
proto_track.py - PROTOTYPE-scale bell tracking on the lane CFD flows (extends 03_cfd_flow/particles.py).
*** SIMULATED - model-based, 2D depth-averaged, an UPPER BOUND on guidance (no 3D leak paths). ***

Per bell (diameter D uniform in d_range, real Gulf bells 6.5-12 cm):
  advection by the time-averaged CFD flow (RK2) x flow_scale, + swimming:
     'random' correlated random heading (tau 10 s), 'rheo' heading into the local flow (worst case),
     plus an optional HYPOTHETICAL cue velocity toward (+) / away from (-) the apex.
  face contact (centre within D/2 of the face, outside a mouth it fits): pinning Fn = (k+1) rho Vn_eff^2 A_n / 2,
     drag Ft = Cd rho (Vt + jet - v_belt)^2 A_t / 2 (belt frame). Slides at Vt + jet if Ft > mu Fn, otherwise
     it is carried at the belt speed (0 = held). Clogging feedback: Vn_eff = Vn / (1 - c(s)), c(s) = face cover
     from the bells currently on the face (each particle = w real bells at the stated density).
  capture when the centre crosses the face plane inside a mouth it fits (|s - s_m| <= b/2 - r).
Outcome: captured / held (on face at the end) / lingering (apex pile-up) / leaked (crossed the face) / back.
Metrics: eta = captured / n, jam = held + lingering, face contacts per bell, time on face.
"""
import numpy as np
from jzcfd import Interp
from lane import centred


def track(G, n=2000, d_range=(0.065, 0.12), swim=0.0, swim_mode="random", tau=10.0, mu=0.4, Cd=1.0, dt=0.25,
          t_rel=600.0, t_max=1500.0, seed=0, x_rel=5.0, belt_frac=0.0, jet_frac=0.0, density=0.0,
          cue=0.0, flow_scale=1.0, Vsw=0.59, record=0):
    rng = np.random.default_rng(seed)
    P = G["P"]; W = P["W"]; h = P["h"]; dx = P["dx"]
    uc, vc = centred(G); I0 = Interp(uc, vc, dx)
    I = (lambda x, y: tuple(flow_scale * a for a in I0(x, y)))
    P0, t, nn, L, b = G["P0"], G["t"], G["n"], G["L"], P["b"]
    apex_pt = G["P1"] + np.array([-1.0, 1.0])
    mouths = np.asarray(G["mouths"], float)
    dw = G.get("dw", dx)
    D = rng.uniform(*d_range, n); r = D / 2
    A_n, A_t = np.pi * D ** 2 / 4, 0.5 * D ** 2
    x = np.full(n, x_rel); y = rng.uniform(r, W - r); ph = rng.uniform(0, 2 * np.pi, n)
    t_on = rng.uniform(0, t_rel, n)                       # continuous release
    out = np.zeros(n, int); ent = -np.ones(n, int)
    ncont = np.zeros(n, int); tface = np.zeros(n); was = np.zeros(n, bool)
    v_belt = belt_frac * Vsw * flow_scale
    v_jet = jet_frac * Vsw * flow_scale
    w = density * P["Q"] * flow_scale * t_rel / n         # real bells per particle
    sb = np.linspace(0, L, 41); cov = np.zeros(40); cmax = np.zeros(40); cacc = np.zeros(40); ncov = 0
    kfun = (lambda s: P["k"])
    if P.get("kprof") is not None:
        se, kv = P["kprof"]; sc_ = 0.5 * (np.asarray(se[:-1]) + np.asarray(se[1:]))
        kfun = (lambda s: np.interp(s, sc_, kv))
    act = np.zeros(n, bool); time = 0.0; frames = []
    while time < t_max:
        act = (t_on <= time) & (out == 0)
        if time > t_rel and not act.any():
            break
        ia = np.nonzero(act)[0]
        if ia.size == 0:
            time += dt; continue
        xa, ya = x[ia], y[ia]
        u1, v1 = I(xa, ya); u2, v2 = I(xa + 0.5 * dt * u1, ya + 0.5 * dt * v1)
        if swim_mode == "rheo":
            ph[ia] = np.arctan2(-v2, -u2) + 0.3 * rng.standard_normal(ia.size)
        else:
            ph[ia] += np.sqrt(2 * dt / tau) * rng.standard_normal(ia.size)
        sx, sy = swim * np.cos(ph[ia]), swim * np.sin(ph[ia])
        if cue != 0.0:
            dv = apex_pt[None, :] - np.c_[xa, ya]; dd = np.linalg.norm(dv, axis=1) + 1e-9
            sx = sx + cue * dv[:, 0] / dd; sy = sy + cue * dv[:, 1] / dd
        xn = xa + dt * (u2 + sx); yn = ya + dt * (v2 + sy)
        ra = r[ia]
        yn = np.clip(yn, ra, W - ra)
        d = (xn - P0[0]) * nn[0] + (yn - P0[1]) * nn[1]
        s = (xn - P0[0]) * t[0] + (yn - P0[1]) * t[1]
        near = (d < ra) & (s > -ra) & (s < L + ra)
        fits = np.zeros(ia.size, bool); midx = -np.ones(ia.size, int)
        if mouths.size:
            dm = np.abs(s[:, None] - mouths[None, :]); j = np.argmin(dm, axis=1); dmin = dm[np.arange(ia.size), j]
            fits = dmin <= b / 2 - ra; midx = np.where(dmin <= b / 2, j, -1)
        cap = near & fits & (d <= 0)
        contact = near & ~fits
        if contact.any():
            ic = np.nonzero(contact)[0]
            sc = np.clip(s[ic], 0, L)
            xs = P0[0] + sc * t[0] + (ra[ic] + dw) * nn[0]; ys = P0[1] + sc * t[1] + (ra[ic] + dw) * nn[1]
            uf, vf = I(xs, ys)
            Vn_t = np.maximum(-(uf * nn[0] + vf * nn[1]), 0)
            if density > 0:
                bi = np.clip(np.searchsorted(sb, sc) - 1, 0, 39)
                Vn_t = Vn_t / np.maximum(1 - cov[bi], 0.1)
            Vt = uf * t[0] + vf * t[1] + v_jet
            sw_n = -(sx[ic] * nn[0] + sy[ic] * nn[1]); sw_t = sx[ic] * t[0] + sy[ic] * t[1]
            Fn = 0.5 * (kfun(sc) + 1) * A_n[ia[ic]] * Vn_t ** 2
            Ft = 0.5 * Cd * A_t[ia[ic]] * (Vt - v_belt) ** 2
            slide = Ft > mu * Fn
            off = (-sw_n) > Vn_t
            hold = ~slide & ~off
            vs = np.where(hold, v_belt, Vt + sw_t)
            s_new = np.clip(sc + vs * dt, -ra[ic], L + ra[ic])
            d_new = np.where(off, ra[ic] + 0.25 * dt * (-sw_n - Vn_t), ra[ic])
            xn[ic] = P0[0] + s_new * t[0] + d_new * nn[0]; yn[ic] = P0[1] + s_new * t[1] + d_new * nn[1]
            yn[ic] = np.clip(yn[ic], ra[ic], W - ra[ic])
        gi = ia[contact]
        ncont[gi[~was[gi]]] += 1
        tface[gi] += dt
        was[ia] = False; was[gi] = True
        x[ia], y[ia] = xn, yn
        if density > 0 and int(time / dt) % 8 == 0:
            on = ia[contact]
            sc_on = np.clip((x[on] - P0[0]) * t[0] + (y[on] - P0[1]) * t[1], 0, L)
            cov = np.minimum(np.histogram(sc_on, bins=sb, weights=w * A_n[on])[0] / ((sb[1] - sb[0]) * h), 0.9)
            if t_rel * 0.5 < time < t_rel:
                cmax = np.maximum(cmax, cov); cacc += cov; ncov += 1
        if cap.any():
            ii = ia[cap]; out[ii] = 1; ent[ii] = midx[cap]; act[ii] = False
        d2 = (x[ia] - P0[0]) * nn[0] + (y[ia] - P0[1]) * nn[1]
        s2 = (x[ia] - P0[0]) * t[0] + (y[ia] - P0[1]) * t[1]
        leak = act[ia] & (d2 < -r[ia]) & (((s2 > -r[ia]) & (s2 < L + r[ia])) | (x[ia] > G["x1"]))
        if leak.any(): out[ia[leak]] = 3; act[ia[leak]] = False
        back = act[ia] & (x[ia] < 0)
        if back.any(): out[ia[back]] = 4; act[ia[back]] = False
        if record and int(round(time / dt)) % record == 0:
            frames.append((time, x.copy(), y.copy(), out.copy(), act.copy(), was.copy()))
        time += dt
    held = (out == 0) & was
    linger = (out == 0) & ~was
    rel = t_on <= t_rel
    res = dict(n=n, eta=float(np.mean(out == 1)), held=float(np.mean(held)), lingering=float(np.mean(linger)),
               leaked=float(np.mean(out == 3)), back=float(np.mean(out == 4)),
               jam=float(np.mean(held | linger)),
               apex_share=float(np.mean(ent == 0) / max(np.mean(out == 1), 1e-9)),
               contacts=float(ncont.mean()), tface=float(tface.mean()),
               tface_p90=float(np.percentile(tface, 90)), cov_max=float(cmax.max()), cov_mean=float(cacc.mean() / max(ncov, 1)))
    res["_frames"] = frames
    return res
