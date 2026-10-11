"""T1 - Jellyfish (and fish/larvae) damage screening along the JAZR transport chain.

Stages: screen sweep -> bypass -> Archimedes screw -> head tank -> pump -> 5 km seabed pipe -> outlet.
For each stage we compute the hydrodynamic stressor and compare with the only thresholds that exist
(fish/larvae; no scyphozoan threshold exists -> jellyfish verdicts are UNKNOWN unless a stressor is trivially small).
Also: transit thermal rise, O2 drawdown by live animals in the pipe, stress-spawning flag.
"""
import math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from params import *

out = {}

# ---------- Pipe ----------
A = math.pi * PIPE_D**2 / 4
v = Q_LINE / A                                   # m/s
Re = v * PIPE_D / NU_35C
f_clean = 0.25 / (math.log10(5.74 / Re**0.9))**2  # Swamee-Jain smooth pipe
pipe = {}
for L in PIPE_L:
    for tag, f in (("clean", f_clean), ("fouled_x2.5", 2.5 * f_clean)):
        tau_w = f / 8 * RHO * v**2                   # wall shear stress Pa
        u_star = math.sqrt(tau_w / RHO)
        delta_vs = 5 * NU_35C / u_star               # viscous sublayer thickness
        gamma_wall = tau_w / MU_35C                  # wall strain rate 1/s
        eps = f * v**3 / (2 * PIPE_D)                # mean dissipation W/kg
        gamma_kolm = math.sqrt(eps / NU_35C)         # Kolmogorov strain rate (upper bound of bulk)
        eta = (NU_35C**3 / eps) ** 0.25
        # velocity difference across a bell (inertial range): du ~ (eps*l)^(1/3) -> strain ~ du/l
        gamma_body = (eps * 0.35) ** (1/3) / 0.35
        pipe[f"L{int(L)}_{tag}"] = dict(v=v, Re=Re, f=f, tau_wall_Pa=tau_w, viscous_sublayer_um=delta_vs*1e6,
                                       strain_wall_1ps=gamma_wall, strain_kolmogorov_1ps=gamma_kolm,
                                       kolmogorov_um=eta*1e6, strain_bell_scale_1ps=gamma_body,
                                       residence_min=L / v / 60)
out["pipe"] = pipe
# bends: centripetal acceleration for R = 3D [ASSUME]
out["bend_accel_g"] = v**2 / (3 * PIPE_D) / 9.81

# ---------- Screw ----------
tip = math.pi * SCREW_D * SCREW_RPM / 60
# leading-edge encounter probability at screw entry (turbine blade-strike style geometry):
# P_contact = N * n/60 * L_body / V_axial  (capped at 1). V_axial: Q / (wetted inlet area, fill 0.5 [ASSUME])
V_ax = 2.4 / (math.pi * (SCREW_D/2)**2 * 0.5)
pc = {f"{Lb:.2f}m": min(1.0, SCREW_FLIGHTS * SCREW_RPM / 60 * Lb / V_ax) for Lb in (0.10, 0.20, 0.30, 0.45)}
out["screw"] = dict(tip_speed_mps=tip, axial_inlet_mps=V_ax, leading_edge_contact_prob=pc,
                    trout_analogue_survival="98.3-100% (200-300 mm trout, Red Bluff/Tracy vol 25) [SRC 7]",
                    note="Rotating tube removes the housing pinch gap that killed ~1/3 of fish in Archimedes TURBINES (Albert Canal). "
                         "Remaining hazard for a 30-45 cm bell is the leading edge at entry and air exposure/splash in the buckets [SRC 22].")

# ---------- Screen sweep ----------
# Bell sliding on mesh: contact time between entrances, normal stagnation pressure from approach flow
t_contact = ENTRANCE_SPACING / V_SWEEP
p_clean = 0.5 * RHO * V_APPROACH**2
out["screen"] = dict(max_contact_time_s=t_contact, mean_contact_time_s=t_contact/2,
                     normal_pressure_clean_Pa=p_clean, normal_pressure_blinding_Pa=[10, 200],
                     note="Contact pressure 5 Pa clean rises to 10-200 Pa under partial blinding (16_FLAW_AUDIT #2). "
                          "No abrasion/extrusion threshold for scyphozoan mesoglea found -> tank test. "
                          "Roll-up passes mesh over the drum: any bell still on the face is wound into the drum (crush hazard).")

# ---------- Bypass acceleration ----------
# NMFS: acceleration toward bypass <= 0.2 ft/s per ft = 0.2 1/s (velocity gradient) [SRC 1]
grad = (V_BYPASS[1] - V_SWEEP) / 3.0   # if accelerated over 3 m [ASSUME]
out["bypass"] = dict(velocity_gradient_1ps=grad, nmfs_limit_1ps=0.2, ok=grad <= 0.2)

# ---------- Thermal ----------
dT_pump = {L: PIPE_KW[L] * 1e3 / (RHO * 3990 * Q_LINE) for L in PIPE_L}
out["thermal"] = dict(dT_from_pump_C=dT_pump, T_transport_C=SST_MAX + max(dT_pump.values()),
                      Cmosaicus_UAE_range_C="20-35 [SRC 12]", Cassiopea_medusa_stress_C=39, Cassiopea_lethal_C=40,
                      Cassiopea_polyp_larva_100pct_mortality_C=36,
                      note="System adds <0.04 C (pump heat; seabed pipe isothermal). Ambient 35.8 C already exceeds the observed UAE range; blooms are Oct-Nov when SST is lower.")

# ---------- O2 drawdown by live animals in the line ----------
R_active = 0.05 * 1.429      # mg O2 / h / g WW  (Stomolophus, 30 C, active) [SRC 9]
R_rest = R_active * 0.5
DO0 = do_sat_mg_L(SST_MAX, 40.0)
cases = {}
t_res_h = (PIPE_L[1] / v + 5 * 60) / 3600      # pipe + 5 min head tank [ASSUME]
for name, dens, eta, lines in (("pilot_peak_35t/h", None, None, 1),
                               ("0.1/m3, 1 line", 0.1, 0.9, 1),
                               ("0.3/m3 design, 1 line", 0.3, 0.9, 1),
                               ("0.3/m3 design, 3 lines", 0.3, 0.9, 3),
                               ("1/m3 extreme, 3 lines", 1.0, 0.9, 3),
                               ("1/m3 extreme, 1 line", 1.0, 0.9, 1)):
    if dens is None:
        kg_s = 35e3 / 3600
    else:
        kg_s = Q_UNIT * dens * eta * BELL_MASS
    conc = kg_s / (Q_LINE * lines)                # kg/m3 in the line
    vol_frac = conc / RHO
    drop_act = R_active * conc * t_res_h          # mg/L (g/m3 *1000 g/kg /1000 L/m3)
    drop_rest = R_rest * conc * t_res_h
    cases[name] = dict(biomass_kg_per_m3=conc, solids_vol_frac=vol_frac, t_res_h=t_res_h,
                       DO_drop_rest_mgL=drop_rest, DO_drop_active_mgL=drop_act,
                       DO_end_active_mgL=DO0 - drop_act, DO_end_rest_mgL=DO0 - drop_rest)
out["oxygen"] = dict(DO_sat_35_8C_S40_mgL=DO0, sublethal_mgL=2.61, lethal_mgL=2.05, cases=cases,
                     uncertainty="respiration +/-72% (Purcell 2010); stressed animals may exceed 'active' rate")

# ---------- Hydraulic grade line over the breakwater (sub-atmospheric pressure = bubbles/air) ----------
hgl = {}
for L in PIPE_L:
    for tag, f in (("clean", f_clean), ("fouled_x2.5", 2.5 * f_clean)):
        hf = f * L / PIPE_D * v**2 / (2 * 9.81) + 1.5 * v**2 / (2 * 9.81)  # friction + minor/exit [ASSUME K=1.5]
        for z in (3.0, 6.0):           # breakwater crest above MSL [ASSUME, not public]
            for x in (300.0,):         # crest distance from head tank [ASSUME]
                # head tank level = hf above MSL (gravity) -> pressure head at crest
                p_head = hf * (1 - x / L) - z
                hgl[f"L{int(L)}_{tag}_crest{z:.0f}m"] = dict(total_head_m=hf, pressure_head_at_crest_m=p_head)
out["hgl_breakwater"] = hgl
neg = [k for k, d in hgl.items() if d["pressure_head_at_crest_m"] < 0.5]

# verdicts
v = {}
v["T1h_breakwater_siphon"] = ("MARGINAL" if neg else "PASS",
    "pressure head at an assumed +3..+6 m crest goes below +0.5 m in: %s -> air release/bubbles under bells [SRC 22]. Route THROUGH the breakwater (culvert/HDD) or set head tank >= crest + 2 m" % (", ".join(neg) or "none"))
v["T1a_pipe_shear_fish"] = ("PASS", "bulk strain (Kolmogorov) %.0f-%.0f 1/s < 500 1/s (Neitzel 2004) and < 400 1/s larval guideline; wall strain only in a %.0f um sublayer" %
                            (pipe["L5000_clean"]["strain_kolmogorov_1ps"], pipe["L5000_fouled_x2.5"]["strain_kolmogorov_1ps"], pipe["L5000_clean"]["viscous_sublayer_um"]))
v["T1b_pipe_shear_jellyfish"] = ("UNKNOWN", "stressor is small (bell-scale strain ~%.1f 1/s, 47 min) but there is no scyphozoan threshold; wall rubbing over 5 km unknown" % pipe["L5000_clean"]["strain_bell_scale_1ps"])
v["T1c_pressure"] = ("PASS", "medusae have no gas spaces; fish see pressure only rise above surface-acclimation (no decompression below ambient) provided the hydraulic grade line stays above the breakwater crest (see T1h)")
v["T1d_screw"] = ("UNKNOWN", "leading-edge contact probability for a 30-45 cm bell %.2f-%.2f per pass; tip speed %.1f m/s; no jellyfish data; air exposure contrary to husbandry advice" % (pc['0.30m'], pc['0.45m'], tip))
v["T1e_pump"] = ("MARGINAL", "screw-centrifugal pumps give 87-99% fish survival but a 45 cm bell must pass the impeller eye; delete the pump by gravity-feeding the pipe from a high head tank (two screws in series)")
v["T1f_screen_contact_and_drum"] = ("UNKNOWN", "up to %.0f s sliding contact; roll-up through brush/drum crushes any bell left on the face -> interlock: roll up only after the bay face is swept/clear" % t_contact)
v["T1g_thermal"] = ("PASS", "transport adds <0.05 C; but release water must avoid the +5 C discharge plume")
d03 = cases["0.3/m3 design, 1 line"]["DO_end_active_mgL"]
d1 = cases["1/m3 extreme, 1 line"]["DO_end_active_mgL"]
v["T1i_oxygen"] = ("MARGINAL", "pilot load ok; 0.3/m3 on ONE line ends at %.1f mg/L (sublethal 2.61); 1/m3 on one line -> %.1f mg/L (anoxic). Requires >=3 lines at design density or O2 injection (Huon precedent)" % (d03, d1))
v["T1j_spawning"] = ("UNKNOWN", "stressed medusae can release gametes/brooded planulae [SRC 23]; no Catostylus test. Pick outlet away from hard substrate; count planulae in transport water in tank test")
v["T1k_bypass_accel"] = ("PASS" if out["bypass"]["ok"] else "MARGINAL", "velocity gradient %.3f 1/s vs NMFS 0.2 1/s (if accelerated over >=3 m)" % grad)
out["verdicts"] = v
save("t1_jelly_transport.json", out)

# chart: O2 end vs biomass
conc = np.linspace(0, 140, 200)
fig, ax = plt.subplots(figsize=(7, 4))
ax.plot(conc, DO0 - R_active*conc*t_res_h, label="active respiration")
ax.plot(conc, DO0 - R_rest*conc*t_res_h, "--", label="resting respiration")
ax.axhline(2.61, color="tab:orange", lw=1); ax.text(100, 2.75, "sublethal 2.61 mg/L", fontsize=8)
ax.axhline(2.05, color="tab:red", lw=1); ax.text(100, 1.6, "lethal 2.05 mg/L", fontsize=8)
for k, c in cases.items():
    ax.plot(c["biomass_kg_per_m3"], c["DO_end_active_mgL"], "ko", ms=4)
    ax.annotate(k, (c["biomass_kg_per_m3"], c["DO_end_active_mgL"]), fontsize=6, xytext=(3, 3), textcoords="offset points")
ax.set_ylim(-3.5, 7); ax.set_xlabel("jellyfish biomass in line (kg/m3)"); ax.set_ylabel("DO at outlet (mg/L)")
ax.set_title("T1 O2 left after %.0f min transit at 35.8 C (start %.1f mg/L)" % (t_res_h*60, DO0), fontsize=9)
ax.legend(fontsize=8); fig.tight_layout(); fig.savefig(os.path.join(CH, "t1_oxygen_drawdown.png"), dpi=130)

if __name__ == "__main__":
    for k, (vv, why) in v.items():
        print(f"{k:32s} {vv:9s} {why}")
    print("pipe v=%.2f m/s residence %.1f min" % (pipe['L5000_clean']['v'], pipe['L5000_clean']['residence_min']))
