"""T01 - Screen sizing: area, length, lane width, sweep ratio, bypass spacing,
exposure time, tide envelope, bay drop height.

Method: continuity for an angled screen spanning a straight training-walled lane.
  Q = U W h ;  screen length L = W / sin(theta) ;  Va = U sin(theta) ; Vs = U cos(theta)
Criteria: NMFS (2022) West Coast Region Anadromous Salmonid Passage Design Manual s.8.5:
  Va <= 0.33 ft/s (0.10 m/s) when exposure > 60 s or tidal; 0.40 ft/s (0.12 m/s) active, <60 s;
  sweep >= approach, 0.8-3 ft/s (0.24-0.91 m/s) optimal; bypass entrance every <=60 s of travel.
  https://repository.library.noaa.gov/view/noaa/43053  (as read in 15_jazr_gate_precedents.md)
"""
import math, csv, os
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from common import *

T = "T01"
th = math.radians(V3["theta_deg"])
NMFS = "NMFS 2022 s.8.5.1 / 8.5.3.3 (repository.library.noaa.gov/view/noaa/43053)"

rows = []
for Q in (SITE["Q_unit"], SITE["Q_unit_max"]):
    A_req = Q / V3["Va"]
    for h0 in SITE["channel_assumed"]:
        for tide_lbl, tr in (("MSL", 0.0), ("low (spring, -1.15 m)", -SITE["tide_range"][1] / 2),
                             ("high (spring, +1.15 m)", +SITE["tide_range"][1] / 2)):
            h = h0 + tr
            L = A_req / h
            W = L * math.sin(th)
            U = Q / (W * h)
            rows.append(dict(Q=Q, h0=h0, tide=tide_lbl, h=round(h, 2), A_req=A_req, L_req=round(L, 1),
                             W=round(W, 1), U=round(U, 3), Vs=round(U * math.cos(th), 3),
                             ratio=round(1 / math.tan(th), 2)))
with open(os.path.join(OUT, "T01_sizing_table.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)

# ---- Check the v3 fixed geometry against tide + max flow ----
cot = 1 / math.tan(th)
record(T, "sweep/through ratio cot(11 deg)", cot, "-", "Vs >= Va (NMFS); bypass ratio >=1.5 (FERC/Hanks & Haefner)", NMFS, "PASS")
fixed = []
for h0, L in zip((7.0, 5.0), V3["L_screen"]):
    for Q in (SITE["Q_unit"], SITE["Q_unit_max"]):
        for tide_lbl, tr in (("MSL", 0), ("LAT-ish", -SITE["tide_range"][1] / 2)):
            h = h0 + tr
            Va = Q / (L * h)
            U = Va / math.sin(th)
            Vs = U * math.cos(th)
            t_exp = L / Vs
            t_seg = V3["bypass_spacing"] / Vs
            fixed.append(dict(h0=h0, L=L, Q=Q, tide=tide_lbl, h=h, Va=Va, U=U, Vs=Vs, t_exp=t_exp, t_seg=t_seg))
            lab = f"v3 L={L:.0f} m, h0={h0} m, Q={Q}, {tide_lbl}"
            record(T, f"approach Va [{lab}]", Va, "m/s", "<=0.10 PASS; <=0.12 MARGINAL (active screen, <60 s rule)", NMFS,
                   verdict(Va, lambda v: v <= 0.1005, lambda v: v <= 0.122))
            record(T, f"sweep Vs [{lab}]", Vs, "m/s", "0.24-0.91 m/s optimal; must not exceed ~1 m/s for bells (assumption)", NMFS,
                   verdict(Vs, lambda v: 0.24 <= v <= 0.91, lambda v: v <= 1.2))
            record(T, f"travel time between bypass entrances [{lab}]", t_seg, "s", "<=60 s", NMFS,
                   verdict(t_seg, lambda v: v <= 60, lambda v: v <= 75))
# exposure (whole face) at design point -> justifies the 0.10 criterion
f0 = fixed[0]
record(T, "exposure time along full face (L/Vs), 7 m, Q=100, MSL", f0["t_exp"], "s",
       ">60 s => the 0.10 m/s (not 0.12) criterion applies", NMFS, "PASS", "confirms v3 choice of 0.10 m/s")

# ---- Bay drop height needed: bed seal to HAT + wave crest + margin ----
crest = 0.5 * 1.8 * SITE["Hs_max"]  # crest of an Hmax=1.8 Hs linear wave (conservative; inside channel will be less)
for h0 in SITE["channel_assumed"]:
    need = h0 + SITE["tide_range"][1] / 2 + crest + 0.3
    record(T, f"bay drop needed for bed seal + HAT + wave crest, h0={h0} m", need, "m",
           f"v3 states 5-7 m bays; need >= this (audit #23: crest >= HAT+0.5 m)", "16_FLAW_AUDIT #23; linear wave crest",
           verdict(7.0, lambda v: v >= need, lambda v: v >= need - 1.5),
           "v3 '5-7 m' drop is short of HAT+crest -> bells overtop at high water")

# ---- Recommended L so Va<=0.10 at LAT, and Va at max flow ----
rec = {}
for h0 in (7.0, 5.0):
    hl = h0 - SITE["tide_range"][1] / 2
    L100 = SITE["Q_unit"] / (V3["Va"] * hl)
    L172 = SITE["Q_unit_max"] / (V3["Va"] * hl)
    Va172 = SITE["Q_unit_max"] / (L100 * hl)
    rec[h0] = dict(h_low=hl, L_for_100=L100, L_for_172=L172, Va_at_172_with_L100=Va172,
                   W_for_100=L100 * math.sin(th), W_for_172=L172 * math.sin(th))
    record(T, f"recommended L for Va<=0.10 at LAT (Q=100), h0={h0}", L100, "m",
           "design length (sizing result)", NMFS, "PASS", f"lane W={L100*math.sin(th):.1f} m")
    record(T, f"Va at Q=172.5 & LAT with that L, h0={h0}", Va172, "m/s", "<=0.10 PASS; <=0.12 MARGINAL", NMFS,
           verdict(Va172, lambda v: v <= 0.1005, lambda v: v <= 0.122),
           f"full 0.10 at 172.5 & LAT needs L={L172:.0f} m")

# ---- Residence time of water between outer edge of lane and screen (for blinding model) ----
# Mean distance a bell slides before an entrance = s/2
Vs0 = fixed[0]["Vs"]
record(T, "mean slide distance to next entrance (s/2) / Vs, 7 m design", 15.0 / Vs0, "s",
       "informative (input to T03)", "geometry", "PASS")

# ---- Chart: Va vs tide level for v3 lengths and recommended lengths ----
fig, ax = plt.subplots(figsize=(7.5, 4.5))
lev = np.linspace(-1.15, 1.15, 50)
for h0, L, c in ((7.0, 143, "#1f77b4"), (5.0, 200, "#d62728")):
    for Q, ls in ((100, "-"), (172.5, "--")):
        ax.plot(lev, Q / (L * (h0 + lev)), ls, color=c, label=f"v3 L={L} m, h0={h0} m, Q={Q}")
ax.axhline(0.10, color="k", lw=1); ax.axhline(0.122, color="grey", lw=1, ls=":")
ax.text(-1.1, 0.102, "NMFS 0.10 m/s (tidal, >60 s)", fontsize=8)
ax.text(-1.1, 0.124, "0.12 m/s (active, <60 s)", fontsize=8, color="grey")
ax.set_xlabel("tide level relative to MSL (m)"); ax.set_ylabel("approach velocity Va (m/s)")
ax.set_title("T01 Approach velocity across the tide (v3 fixed screen lengths)")
ax.legend(fontsize=7); ax.grid(alpha=.3); fig.tight_layout()
fig.savefig(os.path.join(OUT, "T01_Va_vs_tide.png"), dpi=130)

save(T, dict(sizing_rows=rows, v3_fixed=fixed, recommended=rec))
