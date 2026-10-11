"""A8. Screen-panel (roll-down mesh) check under differential pressure.

A roll-down mesh 10 m wide cannot act as a plate: it spans between the two pile guide rails as a
tensioned membrane (like a roller-shutter curtain with wind-locks). Checks:
  1. wire tension at the roll-up trigger x1.5 and at the stuck-drum accident dP (taut-elastic and
     assumed-sag cases),
  2. downstream bulge (sag) clearance,
  3. bending strain of the wire wrapping the drum (low-cycle fatigue on every roll-up),
  4. edge-retention (wind-lock) clip force,
  5. alternative: rigid wedge-wire panel as a simply supported plate strip (for comparison).
"""
import json, sys, pathlib
import numpy as np
from scipy.optimize import brentq
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from common import params as P

d, a = P.MESH_WIRE_D, P.MESH_APERTURE
p = a + d                                   # pitch
eps = (a / p) ** 2                           # open area fraction
A_w = np.pi * d**2 / 4
n_per_m = 1 / p
areal_mass = 2 * n_per_m * A_w * P.DUPLEX["rho"] * 1.05   # two wire directions, 5% crimp
L = P.BAY_W
fy = P.DUPLEX["fy"]                          # annealed 2205 wire, conservative (cold-drawn wire ~2x)
E_eff = 0.5 * P.DUPLEX["E"]                  # woven crimp halves apparent modulus [ENG]


def tension_sag(dp, sag_ratio=None):
    """Membrane tension per metre and sag. If sag_ratio None, solve elastic (crimp-softened) cable."""
    w = dp  # N/m per metre height
    EA = E_eff * A_w * n_per_m
    if sag_ratio is not None:
        f = sag_ratio * L
        return w * L**2 / (8 * f), f
    # extension of parabola: dL = 8 f^2/(3L); strain = T/EA, T = w L^2/(8f)
    g = lambda f: 8 * f**2 / (3 * L**2) - w * L**2 / (8 * f) / EA
    f = brentq(g, 1e-5, L)
    return w * L**2 / (8 * f), f


rows, verdicts = [], []
for label, dp, allow in (("op 1.5 x trip", 1.5 * P.DP_TRIP, 0.6 * fy), ("hard limit", P.DP_HARD, 0.8 * fy),
                         ("stuck-drum accident", P.DP_ACCIDENT, 0.91 * fy)):
    for sag_case in (None, P.MEMBRANE_SAG_RATIO):
        T, f = tension_sag(dp, sag_case)
        sig = T * p / A_w
        rows.append(dict(case=label, dp_Pa=dp, sag_model="elastic-taut" if sag_case is None else f"set sag {sag_case:.0%}",
                         T_kN_per_m=round(T / 1e3, 1), sag_m=round(f, 3), wire_stress_MPa=round(sig / 1e6, 0),
                         allow_MPa=round(allow / 1e6, 0), util=round(sig / allow, 2)))
for r in rows:
    v = "PASS" if r["util"] <= 0.9 else ("MARGINAL" if r["util"] <= 1 else "FAIL")
    verdicts.append(dict(test=f"A8 mesh wire tension, {r['case']} ({r['sag_model']})", value=r["util"],
                         criterion=f"wire stress <= {r['allow_MPa']} MPa", verdict=v,
                         detail=f"T={r['T_kN_per_m']} kN/m, sag {r['sag_m']} m"))

# sag clearance: mesh bulges downstream; need clearance to any downstream member/collector [ASM 0.6 m]
f_acc = tension_sag(P.DP_ACCIDENT, None)[1]
verdicts.append(dict(test="A8b mesh bulge vs 0.6 m downstream clearance (accident, elastic)", value=round(f_acc, 3),
                     criterion="sag <= 0.6 m [ASM]", verdict="PASS" if f_acc <= 0.6 else "FAIL"))

# drum wrap bending: sigma = E d / D
D_core = P.DRUM_D
sig_b = P.DUPLEX["E"] * d / D_core
D_req = P.DUPLEX["E"] * d / (0.4 * fy)   # keep wrap stress <= 0.4 fy for >1e5 cycles [ENG, wire-rope practice]
cycles_60y = 60 * 30 * 24 * 1.3          # one roll-up cycle ~ every 45 min (16 bays, one at a time), 30 bloom days/yr [ASM]
verdicts.append(dict(test="A8c wire bending on drum wrap (roll-up fatigue)", value=round(sig_b / 1e6),
                     criterion=f"E*d/D <= 0.4 fy = {0.4*fy/1e6:.0f} MPa (~{cycles_60y:.0f} wraps in 60 y)",
                     verdict="PASS" if sig_b <= 0.4 * fy else "FAIL",
                     detail=f"D_core={D_core} m, d={d*1e3} mm -> need D >= {D_req:.2f} m or d <= {0.4*fy*D_core/P.DUPLEX['E']*1e3:.2f} mm, "
                            "or hinged link/balanced-weave belt (no wire bending)"))

# wind-lock / edge retention clip force at 0.25 m pitch
T_acc = tension_sag(P.DP_ACCIDENT, P.MEMBRANE_SAG_RATIO)[0]
clip = T_acc * 0.25
verdicts.append(dict(test="A8d edge retention clip load @0.25 m (accident, 3% sag)", value=round(clip / 1e3, 1),
                     criterion="INFO: size clips; or make them shear-release above hard limit (passive fail-open)",
                     verdict="INFO"))

# rigid wedge-wire alternative: plate strip spanning 10 m impossible; spanning between vertical stiffeners @1 m
# bar 3 mm x 6 mm deep wedge wire, simply supported span 1.0 m between support rods, load dp * pitch
bar_b, bar_h, pitch_ww = 0.003, 0.006, 0.003 + 0.010
I = bar_b * bar_h**3 / 12
Mmax = P.DP_ACCIDENT * pitch_ww * 1.0**2 / 8
sig_ww = Mmax / (I / (bar_h / 2))
verdicts.append(dict(test="A8e rigid wedge-wire alternative (bars span 1 m), accident", value=round(sig_ww / 1e6),
                     criterion=f"<= 0.91 fy = {0.91*fy/1e6:.0f} MPa", verdict="PASS" if sig_ww <= 0.91 * fy else "FAIL",
                     detail="rigid panels cannot roll; listed only to show the membrane choice is forced by roll-up"))

out = dict(mesh=dict(wire_d_mm=d * 1e3, aperture_mm=a * 1e3, porosity=round(eps, 3), areal_mass_kg_m2=round(areal_mass, 2),
                     strength_basis="annealed 2205 fy 450 MPa (cold-drawn wire would be ~2x)"),
           rows=rows, verdicts=verdicts)
(HERE / "out").mkdir(exist_ok=True)
json.dump(out, open(HERE / "out" / "mesh_check.json", "w"), indent=2)

dps = np.linspace(50, 3500, 80)
fig, ax = plt.subplots(figsize=(7, 3.8))
for sr, ls in ((None, "-"), (0.02, "--"), (0.03, "-."), (0.05, ":")):
    s = [tension_sag(x, sr)[0] * p / A_w / 1e6 for x in dps]
    ax.plot(dps, s, ls, label="elastic taut" if sr is None else f"sag {sr:.0%}")
for lab, val in (("0.6 fy", 0.6 * fy), ("fy", fy)):
    ax.axhline(val / 1e6, color="k", lw=0.8); ax.text(60, val / 1e6 + 8, lab, fontsize=8)
for x, lab in ((P.DP_TRIP, "trip"), (P.DP_HARD, "hard"), (P.DP_ACCIDENT, "stuck drum")):
    ax.axvline(x, color="#c33", lw=0.8); ax.text(x, 20, lab, rotation=90, fontsize=8, color="#c33")
ax.set_xlabel("differential pressure across bay (Pa)"); ax.set_ylabel("wire stress (MPa)")
ax.set_title(f"Roll-down mesh as membrane: {d*1e3:.1f} mm 2205 wire, {a*1e3:.0f} mm aperture, 10 m span")
ax.legend(fontsize=8); fig.tight_layout(); fig.savefig(HERE / "figs" / "mesh_membrane.png", dpi=150)
for v in verdicts:
    print(f"{v['verdict']:9s} {v['test']}: {v['value']} [{v['criterion']}] {v.get('detail','')}")
print(out["mesh"])
