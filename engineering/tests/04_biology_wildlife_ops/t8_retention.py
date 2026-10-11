"""T8 - Retention: JAZR closed-floor screen/collector vs an open-skirted barrier (boom-type).

Analogues: oil-boom escape velocity ~0.35 m/s irrespective of skirt depth [SRC 14]; C. mosaicus mostly in the top 1 m
(Lake Illawarra) but rhizostomes may sink on the ebb and damaged bells sink (science pack); reference model:
open 2 m skirt keeps 0-55% at 0.2 m/s, closed bag 84-100% [SRC 15, context only].
Monte Carlo over vertical distribution, current, depth. Parameters [ASSUME] unless tagged.
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from params import *

rng = np.random.default_rng(8)
N = 20000
H = rng.uniform(5.5, 9.5 + 2.3, N)           # water depth incl. tide (channel -5.5..-9.5 MSL, range up to 2.3 m)
U = rng.uniform(0.1, 0.6, N)                 # relative velocity across the barrier
dists = {
  "surface (mean 1 m)": lambda: rng.exponential(1.0, N),
  "mixed (uniform)": lambda: rng.uniform(0, 1, N) * H,
  "ebb-sinking (mean 0.6H)": lambda: np.clip(rng.normal(0.6, 0.2, N), 0, 1) * H,
}
def entrain(u):     # fraction of above-skirt animals swept under once u exceeds the boom escape velocity [SRC 14 analogue]
    return np.clip((u - 0.35) / 0.35, 0, 1) * 0.5
res = {}
for dn, f in dists.items():
    z = np.minimum(f(), H - 0.05)
    out = {}
    for skirt in (2.0, 5.0):
        below = z > skirt
        keep = (~below) * (1 - entrain(U))
        out[f"open skirt {skirt:.0f} m"] = float(keep.mean())
    # closed floor: bells reaching the floor gap (within 0.5 m of bed) may extrude through seal gap g
    near_bed = (H - z) < 0.5
    g = rng.uniform(0.0, 0.10, N)            # seal gap from sediment/fouling
    p_ext = np.clip(g / 0.10, 0, 1) * 0.3    # up to 30% extrusion at a 10 cm gap [ASSUME]
    wave_over = 0.005                        # crest >= HAT + 0.5 m; wave overtopping [ASSUME]
    keep_c = 1 - near_bed * p_ext - wave_over
    out["JAZR closed floor (seal gap 0-10 cm)"] = float(keep_c.mean())
    keep_c_bad = 1 - near_bed * 0.3 - wave_over
    out["JAZR closed floor, unseated bar (10 cm everywhere)"] = float(keep_c_bad.mean())
    res[dn] = out
res["reference_context"] = "public reference model: open 2 m skirt 0-55% at 0.2 m/s; closed bag 84-100%"
worst_closed = min(v["JAZR closed floor, unseated bar (10 cm everywhere)"] for k, v in res.items() if isinstance(v, dict))
worst_open = min(v["open skirt 2 m"] for k, v in res.items() if isinstance(v, dict))
res["verdicts"] = {
  "T8a_closed_vs_open_model": ("PASS (model)", "closed floor keeps >= %.1f%% even with an unseated bar vs open 2 m skirt down to %.0f%% -- consistent with a public 84-100%% vs 0-55%%" % (100*worst_closed, 100*worst_open)),
  "T8b_floor_seal_physical": ("UNKNOWN", "retention depends on the bottom bar seating in a rail that collects sand/barnacles; needs seat sensor + tank test with sand in rail and bells at the bed"),
  "T8c_mesh_extrusion": ("UNKNOWN", "bells/fragments extruding through mesh under dP not modelled (16_FLAW_AUDIT #5) -> tank test at 2 densities"),
}
save("t8_retention.json", res)

fig, ax = plt.subplots(figsize=(8, 3.8))
keys = list(res["surface (mean 1 m)"].keys())
x = np.arange(len(keys))
for i, dn in enumerate(dists):
    ax.bar(x + i*0.27, [res[dn][k]*100 for k in keys], 0.27, label=dn)
ax.set_xticks(x + 0.27); ax.set_xticklabels(keys, fontsize=7); ax.set_ylabel("retained (%)")
ax.set_title("T8 retention: closed floor vs open skirt (Monte Carlo, analogue-based)", fontsize=9); ax.legend(fontsize=7)
fig.tight_layout(); fig.savefig(os.path.join(CH, "t8_retention.png"), dpi=130)
if __name__ == "__main__":
    for k, v in res.items(): print(k, v)
