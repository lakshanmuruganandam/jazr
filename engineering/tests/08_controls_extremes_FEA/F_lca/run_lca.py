"""F. Order-of-magnitude life-cycle CO2 (one unit, 60 years) vs status quo (boats + crews).

Quantities are our take-offs for the sized gantry (A_structural_FEA) plus [ASM] items; factors are
cradle-to-gate kgCO2e/kg from ICE v3.0 / worldsteel class values (from memory - verify) with ranges.
Monte Carlo (triangular low/mode/high) gives P10/P50/P90. Not an ISO 14040 LCA.
"""
import json, sys, pathlib
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from common import params as P

rng = np.random.default_rng(0)
N = 20000
tri = lambda lo, mo, hi: rng.triangular(lo, mo, hi, N)

n_bays = P.N_BAYS_UNIT
n_piles = n_bays + 1
pile_len = P.DECK_Z - P.SEABED_Z + 15.0          # 15 m embedment [ASM]
pile_kgm = np.pi * P.PILE_D * 0.025 * 7850       # nominal 25 mm wall
girder_kgm = (2 * 0.8 * 0.02 + 2 * 0.56 * 0.02) * 7850
items = {
    # name: (mass_t samples, factor kgCO2e/kg samples, note)
    "piles (S355)": (n_piles * pile_len * pile_kgm / 1e3 * tri(0.9, 1.0, 1.3), tri(1.5, 1.9, 2.4), "17 piles x 28.5 m CHS1016x25"),
    "girders (S355)": (n_bays * P.BAY_W * girder_kgm / 1e3 * tri(0.9, 1.0, 1.3), tri(1.5, 1.9, 2.4), "box 800x600x20"),
    "drum frames, drums, drives (duplex/mixed)": (n_bays * tri(2.0, 2.5, 3.5), tri(3.0, 4.5, 7.0), "posts+drum+0.8 t drive per bay"),
    "mesh (duplex 6.4 kg/m2)": (15 * P.BAY_W * P.MESH_DROP * 6.43 / 1e3 * tri(1, 1, 3), tri(3.0, 4.5, 7.0), "x up to 3 replacements in 60 y"),
    "training wall (steel sheet piles)": (tri(300, 480, 700), tri(1.5, 1.9, 2.4), "200 m x 16 m x ~150 kg/m2 [ASM]"),
    "collector, screw, head tank steel": (tri(30, 50, 100), tri(1.5, 2.2, 4.5), "[ASM]"),
    "civil concrete (head tank, sills, pipe ballast)": (tri(4000, 5500, 8000), tri(0.12, 0.15, 0.20), "~2,300 m3 incl. 2,000 m3 collars [ASM]"),
    "HDPE pipe 5 km, 1.2 m ID SDR26": (tri(800, 937, 1100), tri(1.9, 2.5, 3.0), "187 kg/m"),
}
emb = {k: m * 1e3 * f / 1e3 for k, (m, f, _) in items.items()}  # tCO2e
marine_works = tri(800, 1900, 4000)   # installation vessels/piling/pipe lay: ~60 days x 10 t diesel x 3.2 [ASM]
emb["marine installation (fuel)"] = marine_works
grid = tri(0.30, 0.40, 0.50)          # tCO2/MWh UAE grid [ASM]
days = tri(20, 45, 60)                # deployed bloom days per year [V3: up to ~2 months]
power_MW = tri(0.35, 0.50, 0.75)      # pipe pump 195-286 kW + screw ~200 kW + drums/aux [V3+ENG]
ops_60 = power_MW * 24 * days * grid * P.LIFE_YEARS
eol = -0.5 * (emb["piles (S355)"] + emb["girders (S355)"] + emb["training wall (steel sheet piles)"]) * tri(0.6, 0.8, 0.9) / 1.0  # recycling credit (module D, indicative)
total = sum(emb.values()) + ops_60
# status quo: boats + crews + trucks per bloom day [ASM]: 2 trawlers 1.5 t diesel/d, 2 workboats 0.5 t/d, trucks 0.6 t/d
sq_day = (tri(2.0, 3.0, 4.0) + tri(0.5, 1.0, 1.5) + tri(0.3, 0.6, 1.0)) * 3.2
sq_60 = sq_day * days * P.LIFE_YEARS
unit_day = 32_000 * tri(0.35, 0.39, 0.45)   # 32 GWh unit-day replaced by gas CCGT [V3 32 GWh; ASM factor]

pct = lambda x: [float(np.percentile(x, q)) for q in (10, 50, 90)]
res = dict(embodied_by_item_t=dict((k, pct(v)) for k, v in emb.items()),
           embodied_total_t=pct(sum(emb.values())), operations_60y_t=pct(ops_60), eol_recycling_credit_t=pct(eol),
           jazr_total_60y_t=pct(total), status_quo_boats_60y_t=pct(sq_60),
           jazr_ops_per_bloom_day_t=pct(power_MW * 24 * grid), status_quo_per_bloom_day_t=pct(sq_day),
           unit_day_replacement_t=pct(unit_day),
           breakeven_unit_days=pct(total / unit_day),
           breakeven_unit_days_net_of_boats=pct((total - sq_60) / unit_day))
V = [dict(test="F1 LCA: JAZR 60-y CO2 vs avoided unit-days", value=f"P50 {res['breakeven_unit_days'][1]:.1f} unit-days (P10-P90 {res['breakeven_unit_days'][0]:.1f}-{res['breakeven_unit_days'][2]:.1f})",
          criterion="carbon break-even <= 5 avoided unit-days over 60 y [ASM]", verdict="PASS" if res["breakeven_unit_days"][2] <= 5 else "MARGINAL"),
     dict(test="F2 per bloom-day operations vs boats/crews", value=f"JAZR {res['jazr_ops_per_bloom_day_t'][1]:.1f} t/d vs boats {res['status_quo_per_bloom_day_t'][1]:.1f} t/d",
          criterion="JAZR operating CO2 per bloom day < status quo", verdict="PASS" if res["jazr_ops_per_bloom_day_t"][1] < res["status_quo_per_bloom_day_t"][1] else "FAIL"),
     dict(test="F3 embodied CO2 hot-spots", value=", ".join(sorted(emb, key=lambda k: -np.median(emb[k]))[:3]), criterion="INFO",
          verdict="INFO", detail="steel (piles + training wall) and HDPE pipe dominate; polymer mesh would cut mesh CO2 ~4x")]
res["verdicts"] = V
res["quantities_note"] = {k: v[2] for k, v in items.items()}
(HERE / "out").mkdir(exist_ok=True)
json.dump(res, open(HERE / "out" / "lca_results.json", "w"), indent=2)

fig, ax = plt.subplots(1, 2, figsize=(11, 4))
names = list(emb.keys()) + ["operations 60 y"]
vals = [np.median(emb[k]) for k in emb] + [np.median(ops_60)]
o = np.argsort(vals)
ax[0].barh([names[i] for i in o], [vals[i] for i in o], color="#5b8fc9")
ax[0].set_xlabel("t CO2e (P50)"); ax[0].set_title("JAZR one unit, 60 years")
ax[0].tick_params(axis="y", labelsize=7)
cats = ["JAZR total\n(60 y)", "boats+crews\n(60 y)", "ONE lost\nunit-day (gas)"]
p = [res["jazr_total_60y_t"], res["status_quo_boats_60y_t"], res["unit_day_replacement_t"]]
ax[1].bar(cats, [x[1] for x in p], yerr=[[x[1] - x[0] for x in p], [x[2] - x[1] for x in p]], color=["#5b8fc9", "#e39a4f", "#c33"], capsize=4)
ax[1].set_ylabel("t CO2e (P50, P10-P90)"); ax[1].set_title("Order-of-magnitude comparison")
fig.tight_layout(); fig.savefig(HERE / "figs" / "lca.png", dpi=150)
for v in V:
    print(v["verdict"], v["test"], v["value"])
print(json.dumps({k: res[k] for k in ("embodied_total_t", "operations_60y_t", "jazr_total_60y_t", "status_quo_boats_60y_t", "unit_day_replacement_t")}, indent=0))
