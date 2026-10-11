"""T04 - Structural loads: curtain (bay) drag vs blinding, membrane tension & mesh strength,
bottom-bar seating, drum torque/motor, wave loads on the curtain, Morison wave+current on piles,
wind on gantry, order-of-magnitude pile sizing, training-wall loads, seismic note.

Standards / sources used for coefficients (standard references, not web-verified tonight unless URL):
  - Morison equation + linear (Airy) wave theory; API RP 2A-WSD: Cd 0.65 smooth / 1.05 rough,
    Cm 1.6 smooth / 1.2 rough; WSD allowable bending 0.66 Fy.
  - Depth-limited breaking H_b = 0.78 h (McCowan; agent_ps_oceanography.md).
  - Standing-wave (clapotis) force on a vertical wall, linear: F = rho g H tanh(kh)/k per m.
  - Membrane: uniform pressure p, span l, sag d -> tension T = p l^2 / (8 d).
  - Wind: q = 0.5 rho_air V^2; Dubai basic 3-s gust 38 m/s (was 45 m/s) -
    https://gulfconstructiononline.com/Article/6032/BMT_to_provide_advice_on_design_wind_speed_changes ;
    Abu Dhabi (ADIBC) Western Region value NOT found -> both used. ERA5 site max gust 19.6 m/s.
  - Westergaard hydrodynamic pressure (seismic): F = 7/12 * alpha * rho g h^2 per m.
"""
import math, os
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from common import *

T = "T04"
h0 = 7.0; hH = h0 + 1.15; hL = h0 - 1.15         # MSL, HAT-ish, LAT-ish water depth in lane
bw = 10.0; A_w = bw * hH                           # wetted bay area at high water
zeta = zeta_perforated(0.5); Va = 0.10
ext = {}

# ---------- 1. curtain drag vs blinding ----------
cases = {"clean": 0.0, "50% blinded": 0.5, "90% blinded": 0.9}
dps = {k: zeta * RHO * (Va / (1 - b)) ** 2 / 2 for k, b in cases.items()}
dps.update({"trip 200 Pa": 200.0, "trip 1 kPa": 1000.0,
            "relief fails, 0.5 m drawdown": RHO * g * 0.5})
F_bay = {k: v * A_w / 1000 for k, v in dps.items()}
for k in dps:
    record(T, f"bay hydrodynamic load [{k}] (10 m x {hH} m wetted)", F_bay[k], "kN",
           "sizing result", "dp x A", "PASS", f"dp={dps[k]:.0f} Pa")
ext["bay_load_kN"] = F_bay

# ---------- 2. membrane tension & mesh strength ----------
# Curtain spans vertically drum -> bottom bar (side rails guide only, conservative for bar & drum).
sag = 0.05  # ASSUMPTION sag/span
def T_membrane(p, span): return p * span ** 2 / (8 * sag * span)   # N per m width
mesh_caps = {  # ASSUMPTIONS: woven wire 2 mm dia at 20 mm pitch (50 wires/m), UTS
    "2205 duplex woven 2 mm/20 mm (UTS 620 MPa)": 50 * math.pi * 1e-6 * 620e6 / 1000,
    "90/10 CuNi woven 2 mm/20 mm (UTS ~300 MPa)": 50 * math.pi * 1e-6 * 300e6 / 1000,
    "UHMWPE knotless net (~40 kN/m, typical aquaculture)": 40.0,
}
for k in ("trip 200 Pa", "trip 1 kPa", "90% blinded", "relief fails, 0.5 m drawdown"):
    Tm = T_membrane(dps[k], hH) / 1000
    for mname, cap in mesh_caps.items():
        sf = cap / Tm
        record(T, f"mesh safety factor [{k}; {mname}]", sf, "-", "SF >= 3 PASS; >= 1.5 MARGINAL (ASSUMPTION, fatigue/corrosion)",
               "membrane T = p l^2/(8d), d=0.05 l", verdict(sf, lambda v: v >= 3, lambda v: v >= 1.5),
               f"tension {Tm:.1f} kN/m")

# ---------- 3. bottom-bar seating ----------
bar_t = 1.5  # ASSUMPTION: 1.5 t steel bottom bar per 10 m bay (150 kg/m)
W_bar_sub = bar_t * 1000 * g * (1 - RHO / 7850) / bw  # N/m submerged
p_lift = W_bar_sub / (T_membrane(1.0, hH))             # p at which vertical membrane pull = bar weight
record(T, "dp at which a 150 kg/m weighted bottom bar lifts off", p_lift, "Pa",
       "must exceed trip setpoint (200 Pa) or bells pass under the bar", "membrane vertical pull ~ T",
       verdict(p_lift, lambda v: v > 300, lambda v: v > 200),
       "=> a weighted bar alone does not seal; latch it into the floor rail and use the bar as a calibrated passive relief")
need = {k: T_membrane(dps[k], hH) * bw / g / (1 - RHO / 7850) / 1000 for k in ("trip 200 Pa", "trip 1 kPa")}
for k, v in need.items():
    record(T, f"bar mass needed to stay seated at [{k}]", v, "t per 10 m bay", "<= 3 t practical (ASSUMPTION)",
           "calc", verdict(v, lambda x: x <= 3, lambda x: x <= 6))
ext["bar_lift_Pa"] = p_lift

# ---------- 4. drum torque & motor ----------
r_drum = 0.40  # m outer radius with mesh wound (ASSUMPTION)
v_roll = 0.15  # m/s (ASSUMPTION, gives 60 s for 9 m)
W_mesh = 2.5 * bw * 9.7 * g * (1 - RHO / 7850)   # 2.5 kg/m2 woven mesh, submerged (N)
for k in ("clean", "trip 200 Pa", "trip 1 kPa", "90% blinded"):
    F = T_membrane(dps[k], hH) * bw + W_mesh + bar_t * 1000 * g + 0.25 * 0.3 * dps[k] * A_w  # + rail friction (30% of load to rails, mu 0.25)
    tq = F * r_drum / 1000; P = F * v_roll / 0.85 / 1000
    record(T, f"drum torque to roll up under load [{k}]", tq, "kN m", "sizing result (motor/gearbox/brake rating)",
           "statics", "PASS", f"line pull {F/1000:.0f} kN, motor {P:.1f} kW at 0.15 m/s")
ext["deploy_time_s"] = 9.7 / v_roll
record(T, "time to lower one bay (9.7 m at 0.15 m/s), all bays in parallel", 9.7 / v_roll / 60, "min",
       "<= 10 min (v3 claim)", "kinematics", verdict(9.7 / v_roll / 60, lambda v: v <= 10))

# ---------- 5. waves on the deployed curtain ----------
def wave_kin(H, Tp, h, z, phase):
    k = wavenumber(Tp, h); w = 2 * math.pi / Tp
    u = (H / 2) * w * np.cosh(k * (h + z)) / np.sinh(k * h) * np.cos(phase)
    a = -(H / 2) * w * w * np.cosh(k * (h + z)) / np.sinh(k * h) * np.sin(phase)
    return u, a, k

def curtain_wave_force(H, Tp, h, normal_factor, blinded):
    if blinded:   # clapotis on a near-solid wall, linear, amplitude per m width
        k = wavenumber(Tp, h)
        return RHO * g * H * math.tanh(k * h) / k * bw * normal_factor ** 2 / 1000
    z = np.linspace(-h, 0, 60); ph = np.linspace(0, 2 * np.pi, 72)
    best = 0
    for p_ in ph:
        u, a, k = wave_kin(H, Tp, h, z, p_)
        un = u * normal_factor + Va
        f = zeta * RHO * un * np.abs(un) / 2
        best = max(best, abs(np.trapezoid(f, z)) * bw)
    return best / 1000

wave_cases = [("p90 Hs 0.58, T 3.5", 0.58, 3.5), ("Hs max 1.36, T 4.5", 1.36, 4.5),
              ("Hmax=1.8xHs 2.45, T 4.5", 2.45, 4.5)]
nf = {"waves along channel (sin 11 deg)": math.sin(math.radians(11)), "waves normal to screen": 1.0}
for wl, H, Tp in wave_cases:
    for nl, f in nf.items():
        for bl in (False, True):
            F = curtain_wave_force(H, Tp, hH, f, bl)
            lab = f"{wl}; {nl}; {'blinded' if bl else 'clean'}"
            ref = F_bay["trip 1 kPa"]
            record(T, f"wave load on one curtain bay [{lab}]", F, "kN",
                   f"<= curtain design load at 1 kPa trip ({ref:.0f} kN) PASS; <= 2x MARGINAL", "linear wave theory",
                   verdict(F, lambda v: v <= ref, lambda v: v <= 2 * ref))
# Hs at which a blinded curtain reaches the 1 kPa design load, for both incidences
def hs_limit(fac):
    for Hs in np.arange(0.1, 3.0, 0.02):
        if curtain_wave_force(Hs, 3.5 if Hs < 0.9 else 4.5, hH, fac, True) > F_bay["trip 1 kPa"]:
            return float(Hs)
    return 3.0
Hs_al = hs_limit(math.sin(math.radians(11))); Hs = hs_limit(1.0)
record(T, "Hs at which wave load on a BLINDED curtain = 1 kPa design load, waves along channel", Hs_al, "m",
       ">= Hs max 1.36 m PASS; >= p99 0.84 MARGINAL", "linear clapotis x sin^2(11 deg)",
       verdict(Hs_al, lambda v: v >= 1.36, lambda v: v >= .84))
record(T, "Hs at which wave load on a BLINDED curtain = 1 kPa design load, waves NORMAL to screen", Hs, "m",
       ">= Hs p99 0.84 m PASS; >= p90 0.58 MARGINAL", "linear clapotis", verdict(Hs, lambda v: v >= .84, lambda v: v >= .58),
       "=> rule: stow when channel Hs from the screen-normal sector exceeds this; screen faces must not face open fetch")
ext["Hs_stow"] = float(Hs)

# ---------- 6. Morison on piles ----------
def morison_pile(D, H, Tp, h, U, Cd, Cm):
    z = np.linspace(-h, 0, 80); best = (0, 0)
    for p_ in np.linspace(0, 2 * np.pi, 120):
        u, a, k = wave_kin(H, Tp, h, z, p_)
        uu = u + U
        f = 0.5 * RHO * Cd * D * uu * np.abs(uu) + RHO * Cm * math.pi * D ** 2 / 4 * a
        Fx = np.trapezoid(f, z); M = np.trapezoid(f * (z + h), z)
        if abs(Fx) > abs(best[0]): best = (Fx, M)
    return best[0] / 1000, best[1] / 1000

U_lane = 0.6  # m/s: lane velocity ~0.5-0.6 (T01) taken as current at pile (plant flow > ambient 0.31)
pile_cases = {
    "operating Hs p90 0.58 (H=1.04), T 3.5": (1.8 * 0.58, 3.5),
    "Hmax 2.45, T 4.5": (2.45, 4.5),
    "depth-limited storm H=0.78 h_HAT, T 7": (0.78 * hH, 7.0),
}
pile_res = {}
for D in (1.0, 1.5):
    for cl, (H, Tp) in pile_cases.items():
        F, M = morison_pile(D, H, Tp, hH, U_lane, 1.05, 1.2)
        pile_res[(D, cl)] = (F, M)
        record(T, f"Morison base shear, pile D={D} m [{cl}]", F, "kN", "input to pile sizing", "API RP 2A rough Cd1.05 Cm1.2",
               "PASS", f"mudline moment {M:.0f} kN m")
Fc = 0.5 * RHO * 1.05 * 1.0 * (U_lane + SITE["cur_max"]) ** 2 * hH / 1000
record(T, "current-only drag on D=1 m pile (0.6 lane + 0.31 ambient)", Fc, "kN", "minor vs waves", "drag", "PASS")

# ---------- 7. wind on gantry ----------
A_gantry = bw * 3.0  # m2 per bay: drum housing + deck fascia (ASSUMPTION 3 m high)
wind = {}
for V, lbl in ((19.6, "site max gust ERA5"), (38.0, "Dubai basic 3-s gust (current)"), (45.0, "Dubai basic (pre-revision)")):
    Fw = 0.5 * 1.225 * V ** 2 * 2.0 * A_gantry / 1000; wind[lbl] = Fw
    record(T, f"wind on gantry per bay [{lbl} {V} m/s, Cf 2.0]", Fw, "kN", "input to pile sizing", "q=0.5 rho V^2", "PASS")

# ---------- 8. pile sizing (cantilever to fixity at 5D below seabed) ----------
Fy = 355e6; allow = 0.66 * Fy; E = 210e9
deck_z = hH + 2.5  # deck/drum axis above seabed
def size_pile(F_h_list):
    """F_h_list: list of (force kN, lever above seabed m). returns D, t for D/t=40."""
    for D in np.arange(0.6, 3.01, 0.05):
        t = D / 40; Lf = 5 * D
        M = sum(F * 1000 * (z + Lf) for F, z in F_h_list)
        I = math.pi / 64 * (D ** 4 - (D - 2 * t) ** 4); S = I / (D / 2)
        if M / S <= allow:
            Ftot = sum(F for F, _ in F_h_list) * 1000
            defl = Ftot * (deck_z + Lf) ** 3 / (3 * E * I)
            return D, t, M / 1000, defl
    return None
combos = {
    "OPERATING: curtain at 1 kPa trip + Hs p90 pile waves + 20 m/s wind":
        [(F_bay["trip 1 kPa"], hH / 2), (pile_res[(1.0, 'operating Hs p90 0.58 (H=1.04), T 3.5')][0], hH * 0.6), (wind["site max gust ERA5"], deck_z)],
    "RELIEF FAILS: curtain 0.5 m drawdown + operating waves":
        [(F_bay["relief fails, 0.5 m drawdown"], hH / 2), (pile_res[(1.0, 'operating Hs p90 0.58 (H=1.04), T 3.5')][0], hH * 0.6), (wind["site max gust ERA5"], deck_z)],
    "BLINDED + Hs 1.36 along channel + 1 kPa + 20 m/s wind":
        [(F_bay["trip 1 kPa"] + curtain_wave_force(1.36, 4.5, hH, math.sin(math.radians(11)), True), hH / 2),
         (pile_res[(1.0, 'Hmax 2.45, T 4.5')][0], hH * 0.6), (wind["site max gust ERA5"], deck_z)],
    "STOWED STORM: depth-limited waves + 45 m/s wind":
        [(pile_res[(1.5, 'depth-limited storm H=0.78 h_HAT, T 7')][0], hH * 0.7), (wind["Dubai basic (pre-revision)"], deck_z)],
}
pile_sizes = {}
for cname, fl in combos.items():
    r = size_pile(fl); pile_sizes[cname] = r
    record(T, f"steel pile OD needed (S355, D/t=40, fixity 5D) [{cname}]", r[0], "m",
           "<= 1.5 m PASS (normal marine piling); <= 2.5 m MARGINAL", "WSD 0.66 Fy cantilever",
           verdict(r[0], lambda v: v <= 1.5, lambda v: v <= 2.5),
           f"t={r[1]*1000:.0f} mm, M={r[2]:.0f} kN m, deck deflection {r[3]*1000:.0f} mm")
ext["pile_sizes"] = {k: list(v) for k, v in pile_sizes.items()}

# ---------- 9. training wall ----------
for dh in (0.1, 0.3, 1.0):
    Fw = RHO * g * dh * hH / 1000  # kN/m (uniform differential head over depth)
    M = Fw * hH / 2
    S_req = M * 1000 / (0.66 * 355e6) * 1e6  # cm3/m
    record(T, f"training wall differential-head load, dh={dh} m between lanes", Fw, "kN/m",
           "sizing result; S_req listed", "hydrostatic", "PASS", f"cantilever M={M:.0f} kNm/m, S_req~{S_req:.0f} cm3/m (sheet pile)")

# ---------- 10. seismic (illustrative only) ----------
for alpha in (0.1, 0.3):
    Fs = 7 / 12 * alpha * RHO * g * hH ** 2 / 1000
    record(T, f"Westergaard hydrodynamic force on a wall per m, PGA {alpha} g (ILLUSTRATIVE)", Fs, "kN/m",
           "qualitative: structures near safety intakes are Seismic Cat II/I (must not collapse onto SSCs)",
           "Westergaard 1933; site SSE NOT public (APR1400 standard design uses 0.3 g)", "PASS",
           "compare with curtain 1 kPa design load 8 kN/m: seismic + hydrodynamic mass governs the gantry")

# chart: bay load components
fig, ax = plt.subplots(figsize=(8, 4.2))
labels = list(F_bay.keys()); vals = [F_bay[k] for k in labels]
ax.barh(labels, vals, color="#4c72b0"); ax.set_xscale("log"); ax.set_xlabel("load per 10 m bay (kN)")
ax.set_title("T04 Hydrodynamic load on one curtain bay"); ax.grid(alpha=.3, axis="x")
fig.tight_layout(); fig.savefig(os.path.join(OUT, "T04_bay_loads.png"), dpi=130)
save(T, ext)
