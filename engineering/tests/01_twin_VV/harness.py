"""Test harness: a line-for-line copy of jazr_twin.simulate() (twin/ is NOT edited) with optional extras
that the twin does not model. With all extras off it must reproduce J.simulate() bit-for-bit (tested).

Extras (all default OFF):
  init_xy      : (x0, y0) arrays -> explicit initial positions instead of the random band (N = len(x0))
  current_fn   : f(t_seconds) -> (u_bg, v_bg) replaces the tide U0 sin(wt) + ur, vr (hindcast forcing).
                 The "tide" sign used by the lane / Ebb policy is then sign(u_bg).
  wind_fn      : f(t) -> (wx, wy) wind velocity at 10 m (m/s, direction the wind blows TOWARD)
  windage      : leeway coefficient (fraction of wind speed added to drift), e.g. 0.02-0.03
  beach        : if True, a free particle that reaches the coast (y <= 0) further than beach_excl from the
                 intake is STRANDED (state 3) and stays there forever (never captured later)
Extra outputs: final state array, first-capture time per particle (s from start, nan if never), and the
first time each particle came inside r_arrive (default the ring R_I).
"""
import numpy as np
from common import J

FREE, HELD, CAPT, STRAND = 0, 1, 2, 3

def simulate(N=3000, hours=72, dt=60.0, swim=0.036, ur=0.0, vr=0.0, system=False,
             eta_g=0.7, eta_r=0.8, policy="ebb", window=0.5, hold_h=6.0, phase0=0.0,
             seed=1, gate_x=None, gate_y=None, ratchet=0.0, field_x=2000.0, field_y=(150.0, 1500.0),
             ring=True, cap_t=None,
             init_xy=None, current_fn=None, wind_fn=None, windage=0.0, beach=False, beach_excl=200.0,
             r_arrive=None):
    Q, H, U0, W = J.Q, J.H, J.U0, J.W
    R_CAP, R_I, R_G = J.R_CAP, J.R_I, J.R_G
    POCKET_X = J.POCKET_X
    gate_x = J.POCKET_X if gate_x is None else gate_x
    gate_y = J.GATE_Y if gate_y is None else gate_y
    r_arrive = R_I if r_arrive is None else r_arrive
    rng = np.random.default_rng(seed)
    if init_xy is None:
        x = np.empty(0); y = np.empty(0)
        while x.size < N:
            xs = rng.uniform(*J.BAND_X, 2*N); ys = rng.uniform(*J.BAND_Y, 2*N)
            ok = np.hypot(xs, ys) > R_I + 50
            x = np.concatenate([x, xs[ok]]); y = np.concatenate([y, ys[ok]])
        x, y = x[:N].copy(), y[:N].copy()
    else:
        x = np.asarray(init_xy[0], float).copy(); y = np.asarray(init_xy[1], float).copy(); N = x.size
    th = rng.uniform(0, 2*np.pi, N)
    st = np.zeros(N, int); side = np.zeros(N); held_t = np.zeros(N)
    n_int = np.zeros(N, int)
    t = phase0/W; t_start = t
    rprev = np.hypot(x, y)
    animals_per_particle = J.DENS*(J.BAND_X[1]-J.BAND_X[0])*(J.BAND_Y[1]-J.BAND_Y[0])*H/N
    t_cap = np.full(N, np.nan); t_arr = np.full(N, np.nan)
    t_arr[rprev < r_arrive] = 0.0
    occ, capt_ts = [], []
    steps = int(hours*3600/dt)
    for k in range(steps):
        free = st == FREE
        r = np.hypot(x, y) + 1e-9
        us = -Q/(np.pi*r*H)
        if current_fn is None:
            u_tide = U0*np.sin(W*t); ub, vb = u_tide + ur, vr
        else:
            ub, vb = current_fn(t - t_start); u_tide = ub
        u = ub + us*x/r; v = vb + us*y/r
        if wind_fn is not None and windage > 0:
            wx, wy = wind_fn(t - t_start); u = u + windage*wx; v = v + windage*wy
        if ratchet > 0:
            inf = (np.abs(x) < field_x) & (y > field_y[0]) & (y < field_y[1])
            v = v + np.where(inf, ratchet*abs(u_tide), 0.0)
        th += rng.normal(0, 0.3, N)
        x = np.where(free, x + (u + swim*np.cos(th))*dt, x)
        y = np.where(free, y + (v + swim*np.sin(th))*dt, y)
        if beach:
            hitc = free & (y <= 0) & (np.hypot(x, y) > beach_excl)
            st[hitc] = STRAND; y = np.where(hitc, 0.0, y)
        y = np.abs(y)
        r = np.hypot(x, y)
        if system:
            cross = (st == FREE) & free & (rprev >= R_I) & (r < R_I)
            hit = cross & (rng.random(N) < (eta_g if ring else 0.0))
            crossg = (st == FREE) & free & ~hit & (rprev >= R_G) & (r < R_G)
            hitg = crossg & (rng.random(N) < eta_r)
            routed = hit | hitg
            if routed.any():
                s = np.sign(u_tide) if u_tide != 0 else 1.0
                side[routed] = s
                st[routed] = HELD; held_t[routed] = 0.0; n_int[routed] += 1
                x[routed] = s*POCKET_X; y[routed] = 30.0
        newcap = (st == FREE) & (r < R_CAP)
        st[newcap] = CAPT
        t_cap[newcap] = (t - t_start) + dt
        arr = np.isnan(t_arr) & (r < r_arrive)
        t_arr[arr] = (t - t_start) + dt
        if system:
            held = st == HELD
            held_t[held] += dt
            ph = (W*t) % (2*np.pi)
            out_pos = (ph < np.pi); frac_pos = ph/np.pi; frac_neg = (ph-np.pi)/np.pi
            if policy == "immediate":
                rel = held
            elif policy == "hold":
                rel = held & (held_t >= hold_h*3600)
            else:
                good_pos = out_pos and frac_pos < window
                good_neg = (not out_pos) and frac_neg < window
                rel = held & (((side > 0) & good_pos) | ((side < 0) & good_neg))
            if cap_t is not None:
                cap_n = int(cap_t*1000/J.MASS/animals_per_particle)
                for sd in (-1.0, 1.0):
                    idx = np.where(held & ~rel & (side == sd))[0]
                    if idx.size > cap_n:
                        old = idx[np.argsort(-held_t[idx])][:idx.size-cap_n]
                        rel[old] = True
            if rel.any():
                st[rel] = FREE
                x[rel] = side[rel]*gate_x; y[rel] = gate_y
                r = np.hypot(x, y)
        rprev = r
        occ.append(int((st == HELD).sum())); capt_ts.append(int((st == CAPT).sum()))
        t += dt
    capt = (st == CAPT).mean()
    res = dict(captured_frac=float(capt), captured_tonnes=float(capt*N*animals_per_particle*J.MASS/1000),
               swarm_tonnes=float(N*animals_per_particle*J.MASS/1000),
               mean_handlings=float(n_int.mean()), peak_held_tonnes=float(max(occ)*animals_per_particle*J.MASS/1000),
               still_held_frac=float((st == HELD).mean()), stranded_frac=float((st == STRAND).mean()),
               far_frac=float(((st == FREE) & (np.hypot(x, y) > 2000)).mean()))
    return res, dict(state=st, t_cap=t_cap, t_arr=t_arr, x=x, y=y, capt_ts=np.array(capt_ts),
                     occ=np.array(occ), n_int=n_int)

def hrun(args):
    kw = args
    return simulate(**kw)[0]
