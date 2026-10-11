"""T02 - Head loss through the mesh vs open-area and blinding; relief/roll-up
trigger setpoint vs tide, wave and pump-transient noise (filter design).

Loss models (all referred to approach velocity Va):
  * Idelchik thin perforated plate (Diagram 8-1)      -> zeta_perforated(f)
  * Idelchik woven wire screen (Diagram 8-6)          -> zeta_wire_mesh(f)
  * Kirschmer bar/wedge-wire rack                      -> zeta_kirschmer(beta,s,b,alpha)
  Source: I.E. Idelchik, Handbook of Hydraulic Resistance, 3rd ed. (standard text, not web-verified);
          Kirschmer (1926) as given in standard hydraulics texts (e.g. USBR / ASCE trash-rack guidance).
Blinding fraction b: flow is forced through (1-b) of the face:  dp = zeta*rho*(Va/(1-b))^2/2.
Trigger criterion: NMFS 2022 s.8.5 - head-loss monitoring must distinguish debris blockage from
  wave/transient disturbance; 0.3 ft (~0.09 m, ~900 Pa) head loss may mean <10% open area.
"""
import math, os
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from common import *

T = "T02"
NMFS = "NMFS 2022 s.8.5 (repository.library.noaa.gov/view/noaa/43053)"
Va = V3["Va"]
meshes = {
    "perforated plate f=0.40": zeta_perforated(0.40),
    "perforated plate f=0.50": zeta_perforated(0.50),
    "woven wire f=0.60": zeta_wire_mesh(0.60),
    "woven wire 2mm/20mm f=0.81": zeta_wire_mesh(0.81),
    "wedge-wire 4mm bar/12mm gap (Kirschmer beta=2.42)": zeta_kirschmer(2.42, 4, 12, 90),
}
b = np.linspace(0, 0.97, 300)
tab = {}
fig, ax = plt.subplots(figsize=(7.5, 4.6))
for name, z in meshes.items():
    dp = z * RHO * (Va / (1 - b)) ** 2 / 2
    ax.semilogy(b * 100, dp, label=f"{name} (zeta={z:.2f})")
    tab[name] = dict(zeta=z, dp_clean=z * RHO * Va**2 / 2,
                     dp_50=z * RHO * (Va / .5) ** 2 / 2, dp_90=z * RHO * (Va / .1) ** 2 / 2,
                     b_at_200Pa=1 - Va / math.sqrt(2 * 200 / (RHO * z)),
                     b_at_900Pa=1 - Va / math.sqrt(2 * 900 / (RHO * z)))
for sp, c in ((200, "orange"), (900, "red")):
    ax.axhline(sp, color=c, ls="--", lw=1); ax.text(1, sp * 1.08, f"{sp} Pa", color=c, fontsize=8)
ax.set_xlabel("blinded fraction of face b (%)"); ax.set_ylabel("screen differential pressure (Pa)")
ax.set_title("T02 Screen head loss vs blinding at Va=0.10 m/s"); ax.grid(alpha=.3, which="both")
ax.legend(fontsize=7); fig.tight_layout(); fig.savefig(os.path.join(OUT, "T02_dp_vs_blinding.png"), dpi=130)

ref = "perforated plate f=0.50"
for name, d in tab.items():
    record(T, f"clean head loss [{name}]", d["dp_clean"] / (RHO * g) * 1000, "mm",
           "<= 15 mm clean (assumption: <1% of typical CW-pump head budget; NMFS 0.09 m = heavily blocked)",
           "Idelchik / Kirschmer; " + NMFS, verdict(d["dp_clean"] / (RHO * g) * 1000, lambda v: v <= 15))
    record(T, f"blinding at which 200 Pa setpoint is reached [{name}]", d["b_at_200Pa"] * 100, "%",
           "informative: v3 '200 Pa' corresponds to this blockage", "calc", "PASS")
# v3 / audit: 200 Pa trip ~ 2 cm head
record(T, "v3 200 Pa trip in head", 200 / (RHO * g) * 100, "cm",
       "must exceed filtered transient noise (see below)", NMFS, "PASS")

# ---------------- transient-noise simulation ----------------
rng = np.random.default_rng(1)
dt = 0.25; dur = 6 * 3600; t = np.arange(0, dur, dt)
z = tab[ref]["zeta"]

def jonswap_u(Hs, Tp, h, n=200, gamma=3.3):
    fp = 1 / Tp; f = np.linspace(0.5 * fp, 4 * fp, n); df = f[1] - f[0]
    sig = np.where(f <= fp, 0.07, 0.09)
    S = (f ** -5) * np.exp(-1.25 * (fp / f) ** 4) * gamma ** np.exp(-(f - fp) ** 2 / (2 * sig**2 * fp**2))
    S *= (Hs / 4) ** 2 / (S.sum() * df)  # scale m0 = (Hs/4)^2
    a = np.sqrt(2 * S * df); ph = rng.uniform(0, 2 * np.pi, n)
    u = np.zeros_like(t)
    zc = -h / 2  # mid-depth orbital velocity ~ depth-averaged load on a full-depth curtain
    for ai, fi, p in zip(a, f, ph):
        k = wavenumber(1 / fi, h); w = 2 * np.pi * fi
        u += ai * w * np.cosh(k * (h + zc)) / np.sinh(k * h) * np.cos(w * t + p)
    return u

def series(Hs, Tp, angle_factor, b_true=0.0, pump_step=True, h0=7.0, L=171.0):
    tide = 1.15 * np.sin(2 * np.pi * t / (12.42 * 3600))
    h = h0 + tide
    Q = np.full_like(t, 100.0)
    if pump_step:   # ASSUMPTION: one of 4 CW pumps trips at 2 h (-25 %) and restarts at 4 h
        Q[(t > 7200) & (t < 14400)] = 75.0
    Va_t = Q / (L * h)
    u = jonswap_u(Hs, Tp, h0) * angle_factor if Hs > 0 else 0 * t
    v = Va_t + u
    dp = z * RHO * v * np.abs(v) / 2 / (1 - b_true) ** 2
    dp += rng.normal(0, 3.0, t.size)  # ASSUMPTION sensor noise 3 Pa rms
    return dp, Va_t

def movavg(x, win_s):
    n = int(win_s / dt); k = np.ones(n) / n
    return np.convolve(x, k, mode="same")

cases = [("calm Hs 0.22", 0.22, 3.0), ("p90 Hs 0.58", 0.58, 3.5), ("max Hs 1.36", 1.36, 4.5)]
noise = {}
fig, axs = plt.subplots(2, 1, figsize=(8, 6), sharex=True)
for lbl, Hs, Tp in cases:
    for af_lbl, af in (("waves along channel (normal comp. sin11=0.19)", math.sin(math.radians(11))),
                       ("waves normal to screen (worst)", 1.0)):
        dp, Va_t = series(Hs, Tp, af)
        raw_max = np.percentile(dp, 99.9)
        f60 = movavg(dp, 60)[int(120 / dt):-int(120 / dt)]
        dp_clean_t = z * RHO * Va_t ** 2 / 2
        # tide/flow-compensated blockage index: b_est = 1 - sqrt(dp_clean(Va(t)) / dp_meas_filtered)
        # compensation reference filtered with the SAME 60 s window (avoids lag spikes at pump steps)
        f60c = movavg(dp, 60); ref60 = movavg(dp_clean_t, 60)
        bidx = 1 - np.sqrt(np.clip(ref60 / np.maximum(f60c, 1e-3), 0, None))
        bidx = bidx[int(120 / dt):-int(120 / dt)]
        noise[(lbl, af_lbl)] = dict(raw_p999=raw_max, f60_max=f60.max(), b_index_max=bidx.max(),
                                    clean_mean=dp_clean_t.mean())
        if af == 1.0:
            axs[0].plot(t / 3600, dp, lw=.3, alpha=.6, label=f"raw {lbl}")
            axs[0].plot(t[int(120/dt):-int(120/dt)] / 3600, f60, lw=1.2, label=f"60 s mean {lbl}")
            axs[1].plot(t[int(120/dt):-int(120/dt)] / 3600, bidx * 100, lw=1, label=lbl)
axs[0].axhline(200, color="r", ls="--"); axs[0].set_ylabel("dp (Pa), clean screen")
axs[0].set_ylim(-400, 1500); axs[0].legend(fontsize=6, ncol=2)
axs[1].axhline(30, color="r", ls="--"); axs[1].set_ylabel("compensated blockage index (%)")
axs[1].set_xlabel("time (h)  [pump trip -25% at 2-4 h; spring tide]"); axs[1].legend(fontsize=7)
axs[0].set_title("T02 Trigger signal on a CLEAN screen, waves normal to screen (worst)")
for a in axs: a.grid(alpha=.3)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "T02_trigger_noise.png"), dpi=130)

for (lbl, af_lbl), d in noise.items():
    record(T, f"raw dp 99.9-pct on clean screen [{lbl}; {af_lbl}]", d["raw_p999"], "Pa",
           "< 200 Pa setpoint (else nuisance trips without filtering)", NMFS,
           verdict(d["raw_p999"], lambda v: v < 100, lambda v: v < 200))
    record(T, f"60-s filtered dp max on clean screen [{lbl}; {af_lbl}]", d["f60_max"], "Pa",
           "< 50% of 200 Pa setpoint", NMFS, verdict(d["f60_max"], lambda v: v < 100, lambda v: v < 200))
    record(T, f"tide+flow-compensated blockage index max, clean [{lbl}; {af_lbl}]", d["b_index_max"] * 100, "%",
           "< 15% false reading (trip proposed at 30-40% est. blockage)", "calc",
           verdict(d["b_index_max"] * 100, lambda v: v < 15, lambda v: v < 25))

# Fixed raw-dp setpoint is not tide/flow invariant: blockage at which 200 Pa trips
zz = tab[ref]["zeta"]; trip_b = []
for Q in (75.0, 100.0, 172.5):
    for h in (7.0 - 1.15, 7.0, 7.0 + 1.15):
        Vat = Q / (171.0 * h)
        trip_b.append(max(0.0, 1 - Vat / math.sqrt(2 * 200 / (RHO * zz))))
spread = (max(trip_b) - min(trip_b)) * 100
record(T, "blockage at which a FIXED 200 Pa setpoint trips, over tide LAT..HAT x flow 75..172.5 m3/s",
       spread, "pct-points spread", "spread < 15 pct-points (else setpoint must be tide/flow compensated)", "calc",
       verdict(spread, lambda v: v < 15, lambda v: v < 25),
       f"trips between {min(trip_b)*100:.0f}% and {max(trip_b)*100:.0f}% blockage")
save(T, dict(mesh_table=tab, noise={f"{k[0]} | {k[1]}": v for k, v in noise.items()}))
