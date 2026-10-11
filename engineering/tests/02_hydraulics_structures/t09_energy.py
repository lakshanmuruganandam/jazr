"""T09 - Energy balance per unit and for 4 units, as % of gross output (1,400 MWe/unit, 5,600 MWe plant).

Components: screw lift to a gravity head tank (from T08 heads), optional pump variant, bypass
dewatering return, drum motors (duty-cycled), extra CW-pump energy from screen head loss,
controls/cameras. Criterion: total < 0.1 % of unit gross output PASS (ASSUMPTION; the audit
quotes 0.02-0.04 % as acceptable), < 0.25 % MARGINAL.
"""
import os, csv, math
from common import *

T = "T09"
pipe = list(csv.DictReader(open(os.path.join(OUT, "T08_pipe_table.csv"))))
def H(L, Q, rough, phi):
    for r in pipe:
        if float(r["L"]) == L and float(r["Q"]) == Q and r["rough"].startswith(rough) and abs(float(r["phi_v"]) - phi) < 1e-9:
            return float(r["H"])
res = {}
for L in V3["pipe_L"]:
    for case, rough, phi in (("best (new pipe, clean water)", "new", 0.0), ("worst (aged, 13.5 % bells)", "aged", 0.135)):
        lift = H(L, 2.0, rough, phi) + 1.0 + 0.5     # + tank margin + screw inlet submergence
        P_screw = RHO * g * 2.0 * lift / 0.72 / 1000
        P_dewater = RHO * g * 16.0 * 0.3 / 0.80 / 1000   # return 16 m3/s of bypass excess over ~0.3 m (ASSUMED)
        P_drums = 14 * 10.0 * 0.3                        # 14 bays x 10 kW x 30 % duty (T04 motor at 200 Pa)
        dp_mean = 50.0 if "worst" in case else 22.0      # Pa mean screen loss (T02/T03)
        P_cw = SITE["Q_unit"] * dp_mean / 0.85 / 1000     # extra CW pumping
        P_ctrl = 10.0                                    # ASSUMED cameras, PLC, lighting
        tot = P_screw + P_dewater + P_drums + P_cw + P_ctrl
        pct = tot / (SITE["P_unit_gross_MW"] * 1000) * 100
        res[(L, case)] = dict(lift=lift, screw=P_screw, dewater=P_dewater, drums=P_drums, cw=P_cw, ctrl=P_ctrl, total=tot, pct=pct)
        record(T, f"total power per unit [{L/1000:.0f} km; {case}]", tot, "kW",
               "< 0.1 % of 1,400 MWe PASS; < 0.25 % MARGINAL (ASSUMED)", "sum of T04/T07/T08",
               verdict(pct, lambda v: v < 0.1, lambda v: v < 0.25),
               f"{pct:.3f} % of unit; screw {P_screw:.0f} (lift {lift:.1f} m), dewater {P_dewater:.0f}, drums {P_drums:.0f}, CW {P_cw:.1f}, ctrl {P_ctrl:.0f} kW")
w = res[(5000.0, "worst (aged, 13.5 % bells)")]
record(T, "4 units, 5 km, worst case", 4 * w["total"] / 1000, "MW", "< 0.1 % of 5,600 MWe", "calc",
       verdict(4 * w["total"] / (SITE["P_plant_gross_MW"] * 1000) * 100, lambda v: v < 0.1, lambda v: v < 0.25),
       f"{4*w['total']/(SITE['P_plant_gross_MW']*1000)*100:.3f} % of plant gross")
# energy per bloom season (60 days operation, ASSUMPTION)
E = 4 * w["total"] * 24 * 60 / 1e3
record(T, "energy per 60-day bloom season, 4 units, worst", E, "MWh", "vs one avoided unit-day = 32,280 MWh (1,345 MW x 24 h)",
       "16_FLAW_AUDIT #10", verdict(E, lambda v: v < 32280 * 0.1, lambda v: v < 32280), f"= {E/32280*100:.1f} % of one unit-day")
save(T, {f"{k[0]}|{k[1]}": v for k, v in res.items()})
