"""T03 - Time-dependent blinding model of one unit's JAZR screen (per-bay).

Model (lumped per 10 m bay, dt = 2 s, 3 h runs):
  arrivals      R = c * Q bells/s, split between bays in proportion to the flow each bay passes
                (passive particles follow the flow); 2 % (Q_bypass/Q) goes straight to the bypass.
  coverage      phi_i = 1 - exp(-N_i a_b / A_bay)  (random-sequential coverage, allows stacking)
  hydraulics    bay conductance C_i = A_bay (1-phi_i)/sqrt(zeta) (down) or A_bay/sqrt(zeta_open) (up);
                dp = rho/2 (Q_screen / sum C_i)^2  (all bays share head-water/tail-water)
  sliding       an impinged bell is pushed onto the mesh with N = dp*a_b and swept along by
                F = 1/2 rho Cd a_side (Vs - v)^2.  Coulomb friction mu N  =>
                v_slide = max(0, Vs - sqrt(2 mu dp a_b / (rho Cd a_side)))
                bells leave to a bypass at rate N_i v_slide / (s/2)  (mean distance to next entrance)
  cycling       bays roll up (60 s) / dwell (10 s) / roll down (60 s); bells on the bay at roll-up go to
                a trough with probability cf, the rest are released to the plant; bells arriving at a
                raised bay pass to the plant.
  relief        if dp > setpoint, the most loaded bay rolls up for 300 s (staged, >=120 s apart),
                its bells are released to the plant (the "pulse").
All biology/friction parameters are ASSUMPTIONS (common.BELL) - no data exist for C. mosaicus on mesh.
Pass criteria (ours, stated): PASS  mean phi<=0.25, capture>=90 %, no relief trips;
                              MARGINAL phi<=0.5, capture>=75 %, all pulses<1 t;   else FAIL.
The 0.25 coverage limit keeps local through-velocity <= Va/(1-phi) = 0.133 m/s (NMFS 0.12-0.13 band).
"""
import math, os, json, csv
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from common import *

T = "T03"
# geometry: v3 design point, 7 m channel, 140 m = 14 bays x 10 m, Q=100
Q = SITE["Q_unit"]; QB = V3["Q_bypass"]; QS = Q - QB
h = 7.0; nb = 14; bw = 10.0; A_bay = bw * h
th = math.radians(11); Va = QS / (nb * A_bay); Vs = Va / math.tan(th)
zeta = zeta_perforated(0.5); zeta_open = 0.3   # ASSUMPTION: frame/rail loss of a raised bay
a_b, a_s, Cd = BELL["a_face"], BELL["a_side"], BELL["Cd_side"]
s_half = V3["bypass_spacing"] / 2
T_ROLL, T_DWELL = 60.0, 10.0   # ASSUMPTION drum speed 0.15 m/s over ~9 m
dt = 2.0; T_END = 3 * 3600

def run(c, mu=0.3, cycling=False, cf=0.0, duplex=False, setpoint=200.0, relief=True, trig_phi=0.10,
        max_moving=1, keep_ts=False):
    N = np.zeros(nb); state = np.zeros(nb, int); timer = np.zeros(nb)   # 0 down,1 up-moving,2 dwell,3 down-moving,4 relief-up
    openfrac = np.zeros(nb)
    arr = cap = leak = 0.0; pulses = []; last_relief = -1e9; trips = 0
    ts = []; acc_phi = acc_dp = 0.0; nacc = 0; dpmax = 0.0
    R = c * Q
    for k in range(int(T_END / dt)):
        t = k * dt
        phi = 1 - np.exp(-N * a_b / A_bay)
        # bay open fraction from state
        for i in range(nb):
            if state[i] == 1: openfrac[i] = min(1, timer[i] / T_ROLL)
            elif state[i] in (2, 4): openfrac[i] = 1
            elif state[i] == 3: openfrac[i] = max(0, 1 - timer[i] / T_ROLL)
            else: openfrac[i] = 0
        # duplex: a second curtain stays down behind a CLEANING bay; relief (state 4) raises both
        of = np.where(state == 4, openfrac, 0.0) if duplex else openfrac
        C = A_bay * ((1 - of) * (1 - phi) / math.sqrt(zeta) + of / math.sqrt(zeta_open))
        Csum = max(C.sum(), 1e-6)
        dp = RHO / 2 * (QS / Csum) ** 2
        q = C / Csum * QS
        # arrivals
        a_tot = R * dt; arr += a_tot
        cap += a_tot * QB / Q
        a_bay = a_tot * (QS / Q) * q / QS
        leak += (a_bay * of).sum()
        N += a_bay * (1 - of)
        # sliding removal
        v = max(0.0, Vs - math.sqrt(2 * mu * dp * a_b / (RHO * Cd * a_s)))
        rem = N * min(1.0, v / s_half * dt)
        N -= rem; cap += rem.sum()
        # state machine
        timer += dt
        for i in range(nb):
            if state[i] == 1 and timer[i] >= T_ROLL: state[i], timer[i] = 2, 0
            elif state[i] == 2 and timer[i] >= T_DWELL: state[i], timer[i] = 3, 0
            elif state[i] == 3 and timer[i] >= T_ROLL: state[i], timer[i] = 0, 0
            elif state[i] == 4 and timer[i] >= 300: state[i], timer[i] = 3, 0
        # relief (fail-safe)
        if relief and dp > setpoint and t - last_relief >= 120:
            cand = [i for i in range(nb) if state[i] == 0]
            if cand:
                i = max(cand, key=lambda j: N[j])
                pulses.append(N[i] * BELL["mass"] / 1000); leak += N[i]; N[i] = 0
                state[i], timer[i] = 4, 0; last_relief = t; trips += 1
        # routine cycling (on demand: most-loaded bay above trig_phi; or continuous if trig_phi=0)
        if cycling and (state != 0).sum() < max_moving:
            cand = [i for i in range(nb) if state[i] == 0 and phi[i] >= trig_phi]
            if cand:
                i = max(cand, key=lambda j: N[j])
                cap += N[i] * cf; leak += N[i] * (1 - cf); N[i] = 0
                state[i], timer[i] = 1, 0
        if t >= T_END - 3600:
            acc_phi += phi.mean(); acc_dp += dp; nacc += 1; dpmax = max(dpmax, dp)
        if keep_ts and k % 5 == 0:
            ts.append((t, phi.mean(), dp, leak, cap, arr))
    return dict(c=c, mu=mu, cycling=cycling, cf=cf, duplex=duplex, phi_mean=acc_phi / nacc, dp=acc_dp / nacc, dp_max=dpmax,
                v_slide=v, capture=cap / arr if arr else 1, leak_frac=leak / arr if arr else 0,
                leak_t_per_h=leak * BELL["mass"] / 1000 / (T_END / 3600), trips=trips,
                max_pulse_t=max(pulses) if pulses else 0.0, ts=ts)

def classify(r):
    if r["phi_mean"] <= 0.25 and r["capture"] >= 0.90 and r["trips"] == 0:
        return "PASS"
    if r["phi_mean"] <= 0.5 and r["capture"] >= 0.75 and r["max_pulse_t"] < 1.0:
        return "MARGINAL"
    return "FAIL"

configs = {
    "A static, mu=0.3":                    dict(mu=0.3),
    "B static, mu=0.1":                    dict(mu=0.1),
    "C cycling, roll-up releases (cf=0)":  dict(mu=0.3, cycling=True, cf=0.0),
    "D cycling, bucket lip/trough (cf=0.8)": dict(mu=0.3, cycling=True, cf=0.8),
    "E duplex curtain + trough (cf=0.8)":  dict(mu=0.3, cycling=True, cf=0.8, duplex=True),
    "F v3 as written: 30% bays cycling (4 of 14), cf=0": dict(mu=0.3, cycling=True, cf=0.0, max_moving=4, trig_phi=0.0),
    "G duplex + trough, 4 bays cycling on demand": dict(mu=0.3, cycling=True, cf=0.8, duplex=True, max_moving=4, trig_phi=0.10),
}
print(f"Va={Va:.3f} m/s  Vs={Vs:.3f} m/s  zeta={zeta:.2f}  clean dp={zeta*RHO*Va**2/2:.1f} Pa")
dens = [0.1, 0.3, 1.0, 2.0]
table = []
for cname, kw in configs.items():
    for c in dens:
        r = run(c, **kw); r["config"] = cname; v = classify(r); r["verdict"] = v
        table.append({k: r[k] for k in ("config", "c", "phi_mean", "dp", "dp_max", "v_slide", "capture", "leak_frac",
                                         "leak_t_per_h", "trips", "max_pulse_t", "verdict")})
        record(T, f"{cname} @ {c} ind/m3", r["phi_mean"] * 100, "% face covered (mean of hour 3)",
               "PASS phi<=25%, capture>=90%, no trips; MARGINAL phi<=50%, capture>=75%, pulses<1 t",
               "model (assumptions in common.BELL)", v,
               f"dp mean/max={r['dp']:.0f}/{r['dp_max']:.0f} Pa, capture={r['capture']*100:.0f}%, leak={r['leak_t_per_h']:.1f} t/h, "
               f"trips={r['trips']}, max pulse={r['max_pulse_t']:.2f} t")

with open(os.path.join(OUT, "T03_density_table.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=table[0].keys()); w.writeheader(); w.writerows(table)

# failure-density sweep
sweep = np.round(np.logspace(-1.5, 0.6, 16), 3)
fail_density = {}
fig, ax = plt.subplots(1, 2, figsize=(11, 4.3))
for cname, kw in configs.items():
    phis, caps = [], []; fd = None; md = None
    for c in sweep:
        r = run(c, **kw); v = classify(r)
        phis.append(r["phi_mean"]); caps.append(r["capture"])
        if v != "PASS" and md is None: md = c
        if v == "FAIL" and fd is None: fd = c
    fail_density[cname] = dict(first_non_pass=md, first_fail=fd)
    ax[0].semilogx(sweep, np.array(phis) * 100, "o-", ms=3, label=cname)
    ax[1].semilogx(sweep, np.array(caps) * 100, "o-", ms=3, label=cname)
    record(T, f"density where it stops PASSING [{cname}]", md if md else 99, "ind/m3",
           ">= 0.3 ind/m3 v3 design density => PASS; >=0.1 MARGINAL", "model",
           verdict(md if md else 99, lambda x: x > 0.31, lambda x: x > 0.1))
    record(T, f"density where it FAILS [{cname}]", fd if fd else 99, "ind/m3",
           ">= 1 ind/m3 (v3 'high-flux' claim) => PASS; >=0.3 MARGINAL", "model",
           verdict(fd if fd else 99, lambda x: x > 1.0, lambda x: x > 0.3))
for a in ax:
    for d in dens: a.axvline(d, color="grey", lw=.5, ls=":")
    a.grid(alpha=.3); a.set_xlabel("bloom density at the screen (ind/m3)")
ax[0].set_ylabel("face coverage, mean of hour 3 (%)"); ax[0].axhline(25, color="g", ls="--"); ax[0].axhline(50, color="r", ls="--")
ax[1].set_ylabel("capture to bypass (%)"); ax[1].axhline(90, color="g", ls="--"); ax[1].axhline(75, color="r", ls="--")
ax[1].legend(fontsize=7); fig.suptitle("T03 Blinding model: coverage and capture vs density (one unit, v3 geometry)")
fig.tight_layout(); fig.savefig(os.path.join(OUT, "T03_failure_density.png"), dpi=130)

# time series at design density 0.3 and 1.0
fig, ax = plt.subplots(2, 1, figsize=(8, 6), sharex=True)
for cname in ("A static, mu=0.3", "C cycling, roll-up releases (cf=0)", "E duplex curtain + trough (cf=0.8)"):
    for c, ls in ((0.3, "-"), (1.0, "--")):
        r = run(c, keep_ts=True, **configs[cname]); ts = np.array(r["ts"])
        ax[0].plot(ts[:, 0] / 60, ts[:, 1] * 100, ls, label=f"{cname} @ {c}")
        ax[1].plot(ts[:, 0] / 60, ts[:, 2], ls)
ax[0].set_ylabel("mean coverage (%)"); ax[1].set_ylabel("dp (Pa)"); ax[1].set_yscale("log")
ax[1].axhline(200, color="r", ls=":"); ax[1].set_xlabel("time since bloom arrival (min)")
ax[0].legend(fontsize=6); [a.grid(alpha=.3) for a in ax]
fig.tight_layout(); fig.savefig(os.path.join(OUT, "T03_timeseries.png"), dpi=130)

# stick threshold
for mu in BELL["mu_fric"]:
    dps = RHO * Cd * a_s * Vs**2 / (2 * mu * a_b)
    record(T, f"dp at which impinged bells stop sliding (mu={mu})", dps, "Pa",
           "must exceed relief setpoint (200 Pa) for bells to clear before a trip", "force balance",
           verdict(dps, lambda v: v > 400, lambda v: v > 200))
save(T, dict(Va=Va, Vs=Vs, zeta=zeta, table=table, fail_density=fail_density))
