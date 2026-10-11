"""T05 - Staged roll-up pulse: tonnes released when one bay rolls up.

Mass on a bay with coverage phi (random-sequential coverage, stacking allowed):
   N = -ln(1-phi) * A_bay / a_b ;  m = N * 3 kg
Coverage at the trip: the 200 Pa (v3) setpoint corresponds to a blockage b_trip (T02); a bay
that trips is the most loaded one, so phi_bay >= b_trip.  Also reads the dynamic pulses from T03.
Criterion: v3 claim "each pulse < 1 t" (JAZR_GATE_v3.md s.2).
"""
import math, os, json
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from common import *

T = "T05"
a_b = BELL["a_face"]; m = BELL["mass"]
zeta = zeta_perforated(0.5); Va = 0.10
def mass_t(phi, A): return -math.log(1 - phi) * A / a_b * m / 1000

t03 = json.load(open(os.path.join(OUT, "T03_results.json")))["extra"]["table"]
# steady coverage at design densities (static screen, mu=0.3) from T03
for row in t03:
    if row["config"] == "A static, mu=0.3":
        for w in (10.0, 5.0):
            A = w * 7.0
            mt = mass_t(min(row["phi_mean"], 0.99), A)
            record(T, f"routine roll-up pulse, {w:.0f} m bay, c={row['c']} ind/m3 (phi={row['phi_mean']*100:.0f}%)", mt, "t",
                   "< 1 t (v3)", "coverage->mass", verdict(mt, lambda v: v < 1.0, lambda v: v < 1.5))
# pulse at trip
for sp in (100.0, 200.0, 500.0):
    b = 1 - Va / math.sqrt(2 * sp / (RHO * zeta))
    for w in (10.0, 5.0, 3.0):
        A = w * 7.0; mt = mass_t(b, A)
        record(T, f"pulse when a bay trips at {sp:.0f} Pa (phi_bay>={b*100:.0f}%), {w:.0f} m bay", mt, "t",
               "< 1 t (v3)", "coverage->mass", verdict(mt, lambda v: v < 1.0, lambda v: v < 1.5))
# bay width needed for <1 t at the 200 Pa trip
b200 = 1 - Va / math.sqrt(2 * 200 / (RHO * zeta))
w_need = 1.0 * 1000 / m * a_b / (-math.log(1 - b200)) / 7.0
record(T, "max bay width for a <1 t pulse at a 200 Pa trip", w_need, "m", ">= 10 m (v3 bay) PASS; >= 5 m MARGINAL", "calc",
       verdict(w_need, lambda v: v >= 10, lambda v: v >= 5))
# dynamic max pulse from T03
for row in t03:
    if row["max_pulse_t"] > 0:
        record(T, f"T03 dynamic max relief pulse [{row['config']} @ {row['c']}]", row["max_pulse_t"], "t",
               "< 1 t (v3)", "T03 model", verdict(row["max_pulse_t"], lambda v: v < 1.0, lambda v: v < 1.5))
# full-face single-layer upper bound per bay and per unit
for w in (10.0,):
    full = 7.0 * w / a_b * m / 1000
    record(T, f"single-layer full cover of one {w:.0f} m x 7 m bay", full, "t", "< 1 t (v3)", "geometry",
           verdict(full, lambda v: v < 1.0, lambda v: v < 1.5), "stacking makes it larger")
# chart
phi = np.linspace(0.01, 0.95, 100)
fig, ax = plt.subplots(figsize=(7, 4))
for w in (3, 5, 10):
    ax.plot(phi * 100, [mass_t(p, w * 7.0) for p in phi], label=f"{w} m x 7 m bay")
ax.axhline(1.0, color="r", ls="--"); ax.axvline(b200 * 100, color="k", ls=":")
ax.text(b200 * 100 + 1, 3.5, "200 Pa trip\n(perforated f=0.5)", fontsize=8)
ax.set_xlabel("bay coverage at roll-up (%)"); ax.set_ylabel("biomass released (t)")
ax.set_title("T05 Roll-up pulse vs bay coverage"); ax.legend(); ax.grid(alpha=.3)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "T05_pulse.png"), dpi=130)
save(T, dict(b_trip_200=b200, w_need=w_need))
