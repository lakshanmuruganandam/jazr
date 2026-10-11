"""T06 - Bypass hydraulics: entrance velocity, entrance size vs bells, required bypass flow,
collector channel, bell volume fraction.

Criteria: NMFS 2022 s.8.6 (as read in 15_jazr_gate_precedents.md s.1a):
   bypass entrance velocity > 110 % of max canal velocity; full depth (floor to surface);
   >= 18 in (0.46 m) wide; no deceleration along the bypass; entrance every <= 60 s of travel.
Bell clearance: ASSUMPTION entrance and collector >= 2 x max bell diameter (0.9 m) to avoid
   bridging of 45 cm bells (two-abreast rule of thumb; no jellyfish data).
Bell volume fraction <= 5 % (16_FLAW_AUDIT #9 suggestion for slurry transport; ASSUMPTION).
"""
import math, os, csv
import numpy as np
from common import *

T = "T06"
NMFS = "NMFS 2022 s.8.6 (repository.library.noaa.gov/view/noaa/43053)"
th = math.radians(11)
rows = []
for h0, L in ((7.0, 143.0), (7.0, 171.0), (5.0, 200.0), (5.0, 260.0)):
    n_ent = max(1, round(L / V3["bypass_spacing"]))
    for Q in (100.0, 172.5):
        for tl, tr in (("MSL", 0.0), ("LAT", -1.15)):
            h = h0 + tr
            U = Q / (L * h) / math.sin(th)
            v_ent = 1.1 * U
            q_ent_v3 = V3["Q_bypass"] / n_ent
            w_v3 = q_ent_v3 / (v_ent * h)           # width that 2 m3/s allows at full depth
            for wmin, lbl in ((0.46, "NMFS 0.46 m"), (0.9, "2 x bell 0.9 m")):
                Qb = n_ent * wmin * h * v_ent
                rows.append(dict(h0=h0, L=L, n_ent=n_ent, Q=Q, tide=tl, U=U, v_ent=v_ent, w_allowed_by_2m3s=w_v3,
                                 w_min=wmin, rule=lbl, Qbypass_required=Qb, pct_of_Q=Qb / Q * 100))
with open(os.path.join(OUT, "T06_bypass_table.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)

base = [r for r in rows if r["h0"] == 7.0 and r["L"] == 143.0 and r["Q"] == 100.0 and r["tide"] == "MSL"]
r0 = base[0]
record(T, "required entrance velocity (1.1 x channel U), v3 7 m design", r0["v_ent"], "m/s", ">110% of channel velocity", NMFS, "PASS")
record(T, "entrance width that v3's 2 m3/s allows (5 full-depth entrances)", r0["w_allowed_by_2m3s"], "m",
       ">= 0.46 m NMFS and >= 0.9 m for 45 cm bells", NMFS + "; bell-size assumption",
       verdict(r0["w_allowed_by_2m3s"], lambda v: v >= 0.9, lambda v: v >= 0.46),
       "2 m3/s cannot feed full-depth entrances at the NMFS velocity")
for r in base:
    record(T, f"bypass flow required per unit [{r['rule']}]", r["Qbypass_required"], "m3/s",
           "<= 2 m3/s (v3 lift sizing) PASS; <= 5 m3/s MARGINAL", NMFS,
           verdict(r["Qbypass_required"], lambda v: v <= 2.0, lambda v: v <= 5.0), f"{r['pct_of_Q']:.1f}% of plant flow")
worst = max((r for r in rows if r["rule"] == "2 x bell 0.9 m"), key=lambda r: r["Qbypass_required"])
record(T, "worst-case bypass flow (0.9 m entrances, 172.5 m3/s, LAT)", worst["Qbypass_required"], "m3/s",
       "<= 2 m3/s PASS; <= 5 MARGINAL", NMFS, verdict(worst["Qbypass_required"], lambda v: v <= 2, lambda v: v <= 5),
       f"L={worst['L']}, h0={worst['h0']}")

# Option: partial-depth slot entrances + secondary dewatering to 2 m3/s
# A 0.9 m wide x full-depth slot at 0.57 m/s per entrance = 3.6 m3/s; 5 entrances = 18 m3/s;
# a secondary inclined dewatering screen (like Tracy secondary louvres) returns ~16 m3/s to the forebay.
Qb = base[1]["Qbypass_required"]
record(T, "secondary dewatering ratio needed to bring bypass to 2 m3/s for the lift", Qb / 2.0, "x",
       "<= 10x is normal for fish facilities (ASSUMPTION; Tracy uses primary+secondary louvres)", "15_ precedents s.1c",
       verdict(Qb / 2.0, lambda v: v <= 10, lambda v: v <= 20))

# collector channel (closed floor), accumulating flow, keep v >= entrance velocity (no deceleration)
for Qc, lbl in ((2.0, "v3 2 m3/s"), (Qb, f"NMFS-compliant {Qb:.0f} m3/s")):
    v_c = 1.0  # m/s design collector velocity (>= 0.57 entrance, no deceleration)
    A = Qc / v_c; wc = max(0.9, A / 3.0)
    record(T, f"collector channel at outlet end [{lbl}], v=1.0 m/s, 3 m deep", wc, "m wide",
           ">= 0.9 m (2 x bell)", "continuity", verdict(wc, lambda v: v >= 0.9), f"area {A:.1f} m2")

# bell volume fraction in the 2 m3/s lift flow
for c in (0.1, 0.3, 1.0, 2.0):
    for cap in (0.9,):
        n = c * 100 * cap  # bells/s
        vf = n * BELL["vol"] / 2.0
        record(T, f"bell volume fraction in 2 m3/s lift flow, c={c}/m3 (90% capture)", vf * 100, "%",
               "<= 5 % (slurry/plugging guide, 16_FLAW_AUDIT #9) PASS; <= 10 % MARGINAL", "mass balance",
               verdict(vf * 100, lambda v: v <= 5, lambda v: v <= 10), f"{n*3*3.6:.0f} t/h")
save(T, dict(rows=rows))
