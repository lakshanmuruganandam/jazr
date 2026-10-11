"""T4 - Release ecology: outlet oxygen demand if animals die, benthic carcass loading,
beach stranding risk, exclusion zones and EAD permitting.
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from params import *

res = {}
# ---- decomposition O2 demand [DERIVED from SRC 8] ----
# Guy-Haim 2020: 25 g WW in 3.14 L, DO fell 5.9 umol/L/h vs control 0.7 -> net 5.2 umol/L/h * 3.14 L / 25 g
k_dec_umol_g_d = 5.2 * 3.14 / 25 * 24          # umol O2 / g WW / day
k_dec_kgO2_per_t_d = k_dec_umol_g_d * 32e-6 * 1e6 / 1e3   # kg O2 per tonne WW per day
decay_days = 5                                  # Higashi-Niigata net-cage decay ~5 d [SRC 24]
res["decomposition"] = dict(k_umol_per_gWW_per_day=k_dec_umol_g_d, kgO2_per_t_per_day=k_dec_kgO2_per_t_d,
                            decay_days=decay_days, note="lower bound: Guy-Haim cores ran out of O2 at 40 h")

# loads (t/day per unit) released at the outlet
loads = {"pilot (Shin Hanul worst day)": 200.0,
         "0.1/m3 x 0.9 capture": Q_UNIT*0.1*0.9*BELL_MASS*86400/1000,
         "0.3/m3 design x 0.9": Q_UNIT*0.3*0.9*BELL_MASS*86400/1000}
# receiving-water O2 supply: tidal exchange through a box at the outlet [ASSUME]
U_res = 0.08    # m/s median offshore model current (05_fact_check #39)
depth = 4.0     # m at 5 km [ASSUME from audit: 3-4 m at 3 km]
width = 1000.0  # m mixing width [ASSUME]
flush_m3_d = U_res*depth*width*86400
dDO_allow = 1.0   # mg/L allowable average depression [ASSUME criterion]
supply_t_O2_d = flush_m3_d*dDO_allow/1e6
tab = {}
for name, L in loads.items():
    for fd in (0.05, 0.2, 1.0):
        standing = L*fd*decay_days            # t WW decaying at any time (steady state)
        demand = standing*k_dec_kgO2_per_t_d/1000   # t O2/day
        tab[f"{name} | dead {int(fd*100)}%"] = dict(load_t_d=L, dead_t_d=L*fd, demand_tO2_d=demand,
                                                   ratio_to_flushing_supply=demand/supply_t_O2_d,
                                                   benthic_area_km2_for_0p1kg_m2=standing*1000/0.1/1e6)
res["oxygen_box"] = dict(flushing_m3_per_day=flush_m3_d, supply_tO2_per_day_at_1mgL=supply_t_O2_d, cases=tab,
                        benthic_reference="Rhopilema field stock ~1.3 kg/m2 (1.3 kt/km2) produced water-column hypoxia within 24 h in a flow-through mesocosm [SRC 8]")

# ---- stranding ----
dist = {"3 km": 3000.0, "5 km": 5000.0}
drift = {"residual onshore 3 cm/s": 0.03, "wind drift 4 cm/s": 0.04, "wind drift 10 cm/s": 0.10, "wind drift 17 cm/s": 0.17}
st = {d: {k: D/v/3600 for k, v in drift.items()} for d, D in dist.items()}
res["stranding_hours_to_shore"] = st
res["stranding_reference"] = "Keesing 2016: >90% of Catostylidae strandings 2 d after onshore winds; 14,172 t on 15 km of beach [SRC 13]; C. mosaicus does not beach itself (passive) [news, Gershwin 2017]"

res["exclusion_zones"] = [
  "the plant intake approach (twin: release within ~1 km returns)",
  "the plant discharge plume (+5 C limit zone; thermal stress, recirculation)",
  "ENEC artificial reef 3.8 km offshore (6,700 m2, 35 species) -- close to a 5 km outlet: carcass deposition and planula settlement risk [agent_enec_science.md]",
  "EAD/ENEC coral cultivation sites around the plant (500,000 colonies, 2025 partnership)",
  "Marawah Marine Biosphere Reserve / Bu Tinah and Al Yasat MPA (dugong, ~3,000 animals) -- distances to be measured in GIS",
  "Other intakes: Ruwais / Jebel Dhanna desalination and industry (~50 km E per audit)",
  "Public beaches and fishing grounds (stranding, stings)",
]
res["EAD"] = ("EAD's marine water quality executive regulation regulates liquid discharges to the sea and sets ambient standards in and outside "
              "MPAs (mediaoffice.abudhabi); numeric DO/BOD limits were NOT retrieved -> UNKNOWN. the plant already operates under an EAD "
              "Operational Environmental Permit; returning biomass is a new discharge needing EAD consent (and FANR/Nawah modification).")

V = {}
r = tab["pilot (Shin Hanul worst day) | dead 20%"]["ratio_to_flushing_supply"]
r2 = tab["0.3/m3 design x 0.9 | dead 100%"]["ratio_to_flushing_supply"]
V["T4a_live_release_O2"] = ("PASS", "live release adds only respiration (T1); at pilot load with 20%% dead, decay demand = %.3fx the assumed flushing supply" % r)
V["T4b_dead_release"] = ("FAIL", "releasing dead biomass at design density: water-column decay demand %.1fx the assumed flushing supply (lower-bound rate), but carcasses sink: standing carcasses would need %.0f km2 to stay <0.1 kg/m2 -> dead fraction must go to 'recover' (dewater/compost), never the outlet" %
                          (r2, tab["0.3/m3 design x 0.9 | dead 100%"]["benthic_area_km2_for_0p1kg_m2"]))
V["T4c_stranding"] = ("MARGINAL", "from 5 km: %.0f h at 3 cm/s residual, %.0f h at 10 cm/s wind drift -- inside the 72 h forecast window, so outlet choice must use wind; criterion: <5%% of forecast particles beach within 72 h, plus beach count survey" %
                      (st["5 km"]["residual onshore 3 cm/s"], st["5 km"]["wind drift 10 cm/s"]))
V["T4d_exclusion_artificial_reef"] = ("MARGINAL", "a 5 km outlet may sit within ~1-2 km of ENEC's 3.8 km artificial reef; set outlets >=2 km from reef/coral nurseries and verify with drift forecast")
V["T4e_EAD_compliance"] = ("UNKNOWN", "numeric limits not retrieved; needs EAD pre-consultation; plan DO/turbidity buoy at each outlet with auto-switch to recover mode")
res["verdicts"] = V
save("t4_release_ecology.json", res)

fig, ax = plt.subplots(figsize=(7, 3.6))
for d, row in st.items():
    ax.bar([f"{d}\n{k}" for k in row], list(row.values()), alpha=0.7)
ax.axhline(72, color="r", ls="--"); ax.text(0, 74, "72 h forecast horizon", fontsize=8, color="r")
ax.set_ylabel("hours to shore"); ax.tick_params(axis="x", labelsize=6)
ax.set_title("T4 time for released animals to drift back to shore (straight-line, no swimming)", fontsize=9)
fig.tight_layout(); fig.savefig(os.path.join(CH, "t4_stranding_time.png"), dpi=130)

if __name__ == "__main__":
    print("k_dec %.1f umol/g/d = %.3f kg O2/t/d; flushing supply %.1f t O2/d" % (k_dec_umol_g_d, k_dec_kgO2_per_t_d, supply_t_O2_d))
    for k, d in tab.items():
        print(f"{k:45s} demand {d['demand_tO2_d']:8.2f} tO2/d ratio {d['ratio_to_flushing_supply']:6.2f}")
    for k, (v, w) in V.items():
        print(f"{k:30s} {v:9s} {w}")
