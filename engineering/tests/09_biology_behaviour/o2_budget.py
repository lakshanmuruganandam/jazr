"""Oxygen budget for live jellyfish in the JAZR release pipe (3 h, 10.5 km).

All inputs are sourced; see README.md section B3. Output: o2_budget.csv.
Run: python3 o2_budget.py
"""
import csv
import math
import os

RHO = 1028.0  # kg/m3 seawater (approx.; same convention as 04 params.py)


def do_sat_mg_L(T, S):
    """Garcia & Gordon (1992) O2 solubility (Benson-Krause), umol/kg -> mg/L
    (same function as TESTS/04_biology_wildlife_ops/params.py)."""
    Ts = math.log((298.15 - T) / (273.15 + T))
    A = [5.80871, 3.20291, 4.17887, 5.10006, -9.86643e-2, 3.80369]
    B = [-7.01577e-3, -7.70028e-3, -1.13864e-2, -9.51519e-3]
    C0 = -2.75915e-7
    lnC = (A[0] + A[1]*Ts + A[2]*Ts**2 + A[3]*Ts**3 + A[4]*Ts**4 + A[5]*Ts**5
           + S*(B[0] + B[1]*Ts + B[2]*Ts**2 + B[3]*Ts**3) + C0*S**2)
    return math.exp(lnC) * 1e-6 * 32.0 * 1e3 * RHO / 1000.0


ML_TO_MG = 1.42  # 1 ml O2 = 1.42 mg O2 (Purcell et al. 2010, Methods)

# Per-animal respiration, mg O2 / h, for a wet mass in g.
def rr_srr(ww_g, c_pct_ww):
    """Purcell et al. 2010 scyphomedusan regression: RR (ml O2/d) = 83.37 * gC^0.94.
    c_pct_ww: carbon as % of wet weight. No Catostylus value exists; rhizostome
    values in Purcell Table 3: R. pulmo 0.34 %, P. punctata 0.46 %, N. nomurai 0.6 %."""
    gc = ww_g * c_pct_ww / 100.0
    return 83.37 * gc ** 0.94 * ML_TO_MG / 24.0


def rr_stomolophus_active(ww_g):
    """Larson 1987 (Can J Zool 65:2690): active S. meleagris 0.05 ml O2/h/g WW at 30 C."""
    return 0.05 * ww_g * ML_TO_MG


CASES = {
    "SRR low (C=0.34%WW)": lambda w: rr_srr(w, 0.34),
    "SRR high (C=0.60%WW)": lambda w: rr_srr(w, 0.60),
    "Stomolophus active (Larson 1987)": rr_stomolophus_active,
    "Stomolophus active x2 (handling-stress margin, ASSUMED)": lambda w: 2 * rr_stomolophus_active(w),
}
MASSES = {"mean 0.33 kg (Hashemi 2025, n=503)": 330.0,
          "Nov UAE bell 11.8 cm ~0.13 kg (00_data)": 130.0,
          "max 1.7 kg (Hashemi 2025)": 1700.0}
DENSITIES = [1, 5, 10, 20, 50, 100]  # animals per m3 of pipe water
TRANSIT_H = 3.0
T, S = 34.0, 42.0  # deg C, ppt (the plant Oct worst-case-ish; Abu Dhabi 40-50 ppt)


def main():
    sat = do_sat_mg_L(T, S)
    rows = []
    for mname, w in MASSES.items():
        for cname, f in CASES.items():
            r = f(w)  # mg/h per animal
            for d in DENSITIES:
                drop = r * d * TRANSIT_H / 1000.0  # mg/L over transit
                rows.append({
                    "mass_case": mname, "resp_case": cname,
                    "mgO2_per_h_per_animal": round(r, 2),
                    "mgO2_per_g_per_h": round(r / w, 4),
                    "density_per_m3": d,
                    "DO_drop_mg_L_3h": round(drop, 2),
                    "DO_sat_mg_L_34C_42ppt": round(sat, 2),
                    "DO_end_if_start_100pct": round(sat - drop, 2),
                    "DO_end_pct_sat": round(100 * (sat - drop) / sat, 1),
                })
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "o2_budget.csv")
    with open(out, "w", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        wr.writeheader()
        wr.writerows(rows)
    print(f"DO saturation at {T} C, {S} ppt = {sat:.2f} mg/L")
    for r in rows:
        if r["mass_case"].startswith("mean") and r["density_per_m3"] in (1, 10, 50):
            print(r["resp_case"], r["density_per_m3"], r["mgO2_per_h_per_animal"],
                  r["DO_drop_mg_L_3h"], r["DO_end_pct_sat"])
    for r in rows:
        if r["mass_case"].startswith("max") and r["density_per_m3"] == 50:
            print("1.7kg", r["resp_case"], r["DO_drop_mg_L_3h"], r["DO_end_pct_sat"])


if __name__ == "__main__":
    main()
