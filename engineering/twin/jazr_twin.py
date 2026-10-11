"""
JAZR digital twin (reduced-order, NOT validated). Plan-view particle model of a jellyfish swarm near a
4-unit coastal intake, comparing (a) today's baseline with (b) the JAZR system: guide arms + tidal lane
+ Tide Lock pockets + residual guard, with three release policies (immediate / fixed hold / Ebb Window).

Physics (all stated assumptions, from the research folder's verified facts):
  coast y = 0 (reflecting); intake at origin, half-plane radial sink u = Q/(pi r h), Q = 400 m3/s, h = 3.5 m
  alongshore tide u = U0 sin(wt), U0 = 0.117 m/s (median |u| ~0.083), M2 period 12.42 h; residual drift ur
  jellyfish = drifters + random-heading swimming (3.6 cm/s juvenile figure and 10 cm/s large-rhizostome figure)
  captured by the intake if r < 60 m
System (parameters, not measurements -> the tank tests exist to measure them):
  interception ring R_i = 500 m (> sink capture radius ~440 m at h = 3.5 m); guide efficiency eta_g per crossing
  intercepted bells are carried by the lane in the direction of the tide to the downstream pocket (x = +/-600 m)
  residual guard at r = 120 m (angled louvre + bypass) catches eta_r of leakers and sends them to a pocket
  release from the pocket's seaward gate (x = +/-600, y = 150): policy decides WHEN
Outputs: results.json + charts in ./out
"""
import numpy as np, json, os, sys
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out"); os.makedirs(OUT, exist_ok=True)

Q, H = 400.0, 3.5
U0 = 0.117
W = 2*np.pi/(12.42*3600)
R_CAP, R_I, R_G = 60.0, 500.0, 120.0
POCKET_X, GATE_Y = 600.0, 150.0
# swarm: 0.1 ind/m3 over the initial band -> animals represented per particle
BAND_X, BAND_Y = (-4000.0, 4000.0), (50.0, 1500.0)
DENS, MASS = 0.1, 3.0

def simulate(N=3000, hours=72, dt=60.0, swim=0.036, ur=0.0, vr=0.0, system=False,
             eta_g=0.7, eta_r=0.8, policy="ebb", window=0.5, hold_h=6.0, phase0=0.0,
             seed=1, record_every=None, gate_x=POCKET_X, gate_y=GATE_Y,
             ratchet=0.0, field_x=2000.0, field_y=(150.0, 1500.0), ring=True, cap_t=None):
    rng = np.random.default_rng(seed)
    # initial band outside the ring (the early-warning alert gives lead time)
    x = np.empty(0); y = np.empty(0)
    while x.size < N:
        xs = rng.uniform(*BAND_X, 2*N); ys = rng.uniform(*BAND_Y, 2*N)
        ok = np.hypot(xs, ys) > R_I + 50
        x = np.concatenate([x, xs[ok]]); y = np.concatenate([y, ys[ok]])
    x, y = x[:N].copy(), y[:N].copy()
    th = rng.uniform(0, 2*np.pi, N)
    FREE, HELD, CAPT = 0, 1, 2
    st = np.zeros(N, int); side = np.zeros(N); held_t = np.zeros(N)
    n_int = np.zeros(N, int)                       # times each animal was handled by the system
    t = phase0/W
    rprev = np.hypot(x, y)
    animals_per_particle = DENS*(BAND_X[1]-BAND_X[0])*(BAND_Y[1]-BAND_Y[0])*H/N
    occ, capt_ts, frames = [], [], []
    steps = int(hours*3600/dt)
    for k in range(steps):
        free = st == FREE
        r = np.hypot(x, y) + 1e-9
        us = -Q/(np.pi*r*H)
        u_tide = U0*np.sin(W*t)
        u = u_tide + ur + us*x/r; v = vr + us*y/r
        if ratchet > 0:   # tidal ratchet field: angled self-reversing vanes turn |tide| into offshore drift
            inf = (np.abs(x) < field_x) & (y > field_y[0]) & (y < field_y[1])
            v = v + np.where(inf, ratchet*abs(u_tide), 0.0)
        th += rng.normal(0, 0.3, N)
        x = np.where(free, x + (u + swim*np.cos(th))*dt, x)
        y = np.where(free, y + (v + swim*np.sin(th))*dt, y)
        y = np.abs(y)
        r = np.hypot(x, y)
        if system:
            # guide arms + lane: inward crossing of the ring
            cross = free & (rprev >= R_I) & (r < R_I)
            hit = cross & (rng.random(N) < (eta_g if ring else 0.0))
            # residual guard: inward crossing of r = 120 m
            crossg = free & ~hit & (rprev >= R_G) & (r < R_G)
            hitg = crossg & (rng.random(N) < eta_r)
            routed = hit | hitg
            if routed.any():
                s = np.sign(u_tide) if u_tide != 0 else 1.0     # lane conveys with the tide
                side[routed] = s
                st[routed] = HELD; held_t[routed] = 0.0; n_int[routed] += 1
                x[routed] = s*POCKET_X; y[routed] = 30.0
        newcap = (st == FREE) & (r < R_CAP)
        st[newcap] = CAPT
        if system:
            held = st == HELD
            held_t[held] += dt
            # phase of the tide in the pocket's outward direction: release only early in an outgoing half-cycle
            ph = (W*t) % (2*np.pi)              # u_tide = U0 sin(ph)
            out_pos = (ph < np.pi)               # current toward +x
            frac_pos = ph/np.pi                  # fraction of the +x half-cycle elapsed
            frac_neg = (ph-np.pi)/np.pi
            if policy == "immediate":
                rel = held
            elif policy == "hold":
                rel = held & (held_t >= hold_h*3600)
            else:  # Ebb Window: outward tide AND early enough that the half-cycle carries them far
                good_pos = out_pos and frac_pos < window
                good_neg = (not out_pos) and frac_neg < window
                rel = held & (((side > 0) & good_pos) | ((side < 0) & good_neg))
            if cap_t is not None:   # pocket capacity cap: overflow -> release-only mode (oldest first)
                cap_n = int(cap_t*1000/MASS/animals_per_particle)
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
        if record_every and k % record_every == 0:
            frames.append((t, x.copy(), y.copy(), st.copy()))
        t += dt
    capt = (st == CAPT).mean()
    res = dict(captured_frac=float(capt), captured_tonnes=float(capt*N*animals_per_particle*MASS/1000),
               swarm_tonnes=float(N*animals_per_particle*MASS/1000),
               mean_handlings=float(n_int.mean()), peak_held_tonnes=float(max(occ)*animals_per_particle*MASS/1000),
               still_held_frac=float((st == HELD).mean()),
               far_frac=float(((st == FREE) & (np.hypot(x, y) > 2000)).mean()))
    return res, np.array(capt_ts)/N, np.array(occ)*animals_per_particle*MASS/1000, frames

if __name__ == "__main__":
    quick = "--quick" in sys.argv
    N = 1500 if quick else 3000
    R = {}
    cases = [("baseline", dict(system=False))]
    for pol in ("immediate", "hold", "ebb"):
        cases.append((f"jazr_{pol}", dict(system=True, policy=pol)))
    for swim in (0.036, 0.10):
        for drift_name, ur, vr in (("no residual", 0, 0), ("1 cm/s alongshore", 0.01, 0), ("1 cm/s onshore", 0, -0.01)):
            for name, kw in cases:
                key = f"{name}|swim={swim}|{drift_name}"
                caps = []; mh = []; ph = []
                for ph0 in (0, np.pi/2, np.pi, 3*np.pi/2):      # average over the tide phase at alert time
                    res, _, _, _ = simulate(N=N, swim=swim, ur=ur, vr=vr, phase0=ph0, **kw)
                    caps.append(res["captured_frac"]); mh.append(res["mean_handlings"]); ph.append(res["peak_held_tonnes"])
                R[key] = dict(captured_frac=float(np.mean(caps)), captured_range=[float(min(caps)), float(max(caps))],
                              mean_handlings=float(np.mean(mh)), peak_held_tonnes=float(np.mean(ph)),
                              swarm_tonnes=res["swarm_tonnes"])
                print(f"{key:55s} capt {np.mean(caps)*100:5.1f}%  handlings {np.mean(mh):.2f}  peak held {np.mean(ph):7.0f} t")
    # sensitivity to guide efficiency (median conditions, Ebb Window)
    for eg in (0.4, 0.5, 0.6, 0.7, 0.8, 0.9):
        caps = [simulate(N=N, system=True, eta_g=eg, phase0=p)[0]["captured_frac"] for p in (0, np.pi/2, np.pi, 3*np.pi/2)]
        R[f"eta_g={eg}"] = float(np.mean(caps)); print("eta_g", eg, f"{np.mean(caps)*100:.1f}%")
    # Ebb Window sweep: release-window fraction
    for wf in (0.1, 0.25, 0.5, 0.75, 1.0):
        out = [simulate(N=N, system=True, window=wf, phase0=p)[0] for p in (0, np.pi/2, np.pi, 3*np.pi/2)]
        R[f"window={wf}"] = dict(captured_frac=float(np.mean([o["captured_frac"] for o in out])),
                                 mean_handlings=float(np.mean([o["mean_handlings"] for o in out])),
                                 peak_held_tonnes=float(np.mean([o["peak_held_tonnes"] for o in out])))
        print("window", wf, R[f"window={wf}"])
    json.dump(R, open(os.path.join(OUT, "results.json"), "w"), indent=1)
