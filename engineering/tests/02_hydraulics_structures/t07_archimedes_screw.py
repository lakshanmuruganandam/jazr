"""T07 - Archimedes screw lift sizing (2 m3/s per line, head tank 5-11 m), rotating-tube variant.

Method:
 * Speed limit (Nagel 1968, via Rorres 2000 J. Hydraul. Eng.): n_max = 50 / D^(2/3) rpm.
   https://math.nyu.edu/Archimedes/Screw/optimal/screw.pdf
 * Throughput calibrated on Red Bluff Research Pumping Plant (USBR): D = 3.05 m, 26.5 rpm,
   2.4-2.5 m3/s per screw, max lift 5.9 m  (15_jazr_gate_precedents.md s.3, REPORTED from USBR pages)
   -> Q = k D^3 n/60 with k = 0.196.
 * Tip speed limit: Red Bluff tip speed (pi D n) ~4.2 m/s passed 200-300 mm trout at ~100 % survival
   (USBR Tracy vol.25, VERIFIED in 15_); fish strike literature: ~5 m/s "safe" for rainbow trout
   (patent/lab literature, e.g. Watson et al. 2020 doi:10.1080/24705357.2020.1768166). No jellyfish data.
 * Flight depth: (R_o - R_i) with R_i = 0.5 R_o -> D/4 ; ASSUMPTION need >= 1.5 x 45 cm bell = 0.68 m.
 * Inclination 30 deg (typical 22-38 deg); length = lift / sin(30) + 2 m inlet/outlet.
 * Power = rho g Q H / eta, eta 0.70 (open trough) / 0.75 (rotating tube, no gap leakage) - ASSUMPTIONS
   within typical 0.65-0.80 screw-pump range.
"""
import math, os, csv
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from common import *

T = "T07"
k = 2.45 / (3.05 ** 3 * 26.5 / 60)
rows = []
for D in (2.0, 2.5, 3.0, 3.5, 4.0):
    nmax = 50 / D ** (2 / 3)
    Qmax = k * D ** 3 * nmax / 60
    tip = math.pi * D * nmax / 60
    n_tip42 = 4.23 * 60 / (math.pi * D)               # rpm for Red Bluff tip speed
    n_use = min(nmax, n_tip42)
    Q_use = k * D ** 3 * n_use / 60
    nscrew = math.ceil(2.0 / Q_use)
    rows.append(dict(D=D, n_max_Nagel=nmax, tip_at_nmax=tip, n_used=n_use, Q_per_screw=Q_use,
                     screws_for_2m3s=nscrew, flight_depth=D / 4))
with open(os.path.join(OUT, "T07_screw_table.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
for r in rows:
    record(T, f"screw D={r['D']} m: Q per screw at min(Nagel, 4.2 m/s tip)", r["Q_per_screw"], "m3/s",
           ">= 2 m3/s with one duty screw PASS; 2 screws MARGINAL", "Nagel/Rorres; Red Bluff calibration",
           verdict(r["screws_for_2m3s"], lambda v: v == 1, lambda v: v == 2),
           f"n={r['n_used']:.1f} rpm, screws needed {r['screws_for_2m3s']}")
    record(T, f"screw D={r['D']} m: flight depth vs 45 cm bell", r["flight_depth"], "m", ">= 0.68 m (1.5 x bell, ASSUMPTION)",
           "geometry", verdict(r["flight_depth"], lambda v: v >= 0.68, lambda v: v >= 0.45))
sel = [r for r in rows if r["D"] == 3.0][0]
record(T, "selected D=3.0 m tip speed", math.pi * 3.0 * sel["n_used"] / 60, "m/s",
       "<= 4.2 m/s (Red Bluff, trout ~100% survival) PASS; <= 5 m/s MARGINAL", "USBR Tracy vol.25; strike literature",
       verdict(math.pi * 3.0 * sel["n_used"] / 60, lambda v: v <= 4.25, lambda v: v <= 5.0),
       "NO scyphozoan data - tank test #4")

# lift / length / power
for H in (5.0, 7.0, 11.0):
    Ls = H / math.sin(math.radians(30)) + 2
    for eta, var in ((0.70, "open trough"), (0.75, "rotating tube")):
        P = RHO * g * 2.0 * H / eta / 1000
        record(T, f"screw power, 2 m3/s, lift {H} m [{var}]", P, "kW", "sizing result", "rho g Q H/eta", "PASS",
               f"screw length {Ls:.0f} m at 30 deg")
    record(T, f"single-stage lift {H} m vs Red Bluff proven max 5.9 m", H, "m",
           "<= 5.9 m PASS (proven); <= 9 m MARGINAL (vendor range, unproven for fish/jelly); else FAIL -> 2 stages",
           "15_ precedents s.3", verdict(H, lambda v: v <= 5.9, lambda v: v <= 9.0), f"length {Ls:.0f} m")

# rotating tube mass (order of magnitude)
D, Ls = 3.0, 11 / 0.5 + 2
m_tube = math.pi * D * Ls * 0.012 * 7850 / 1000
m_flights = 3 * Ls / D * (math.pi * D) * (D / 4) * 0.010 * 7850 / 1000 * 1.0  # 3 flights, pitch D, approx
m_water = 0.3 * math.pi * D ** 2 / 4 * Ls * RHO / 1000
record(T, "rotating-tube screw (D3 m, 11 m lift) rotating mass incl. water", m_tube + m_flights + m_water, "t",
       "<= 80 t per bearing pair (ASSUMPTION: large screw pumps are tens of t)", "geometry",
       verdict(m_tube + m_flights + m_water, lambda v: v <= 80, lambda v: v <= 120),
       f"tube {m_tube:.0f} t, flights {m_flights:.0f} t, water {m_water:.0f} t; long span -> deflection, consider 2 stages")

# NMFS-compliant bypass (18 m3/s, T06) without dewatering
nsc = math.ceil(18.0 / sel["Q_per_screw"])
record(T, "screws needed if the full NMFS-style bypass (18 m3/s) is lifted without dewatering", nsc, "screws/unit",
       "<= 2 PASS; <= 4 MARGINAL", "T06 + this test", verdict(nsc, lambda v: v <= 2, lambda v: v <= 4),
       "=> dewater the bypass before the lift")

fig, ax = plt.subplots(figsize=(7, 4))
Ds = np.linspace(1.5, 4.5, 50)
ax.plot(Ds, 50 / Ds ** (2 / 3), label="Nagel n_max")
ax.plot(Ds, 4.23 * 60 / (math.pi * Ds), label="Red Bluff tip speed 4.2 m/s")
ax.plot(Ds, 2.0 * 60 / (k * Ds ** 3), label="n for 2 m3/s (one screw)")
ax.scatter([3.05], [26.5], color="k", zorder=5, label="Red Bluff (3.05 m, 26.5 rpm)")
ax.set_ylim(0, 80); ax.set_xlabel("screw diameter D (m)"); ax.set_ylabel("rpm")
ax.set_title("T07 Archimedes screw speed envelope"); ax.legend(fontsize=8); ax.grid(alpha=.3)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "T07_screw_envelope.png"), dpi=130)
save(T, dict(k=k, rows=rows))
