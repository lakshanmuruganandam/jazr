"""T08 - Export pipe: Colebrook-White friction, head & power, bell-slurry effect, transit time,
turbulent shear, minimum velocity, surge (Joukowsky) and column separation, HDPE collapse,
on-bottom stability (DNV-RP-F109-style simplified absolute static), buoyancy/ballast, thermal expansion.

Sources / standard references:
 - Colebrook-White; HDPE roughness 0.0015-0.007 mm new (manufacturer tables); ASSUMED 0.25 mm aged with biofilm.
 - Thomas (1965) relative viscosity mu_r = 1 + 2.5 phi + 10.05 phi^2 + 0.00273 exp(16.6 phi).
 - Durand limit-deposit velocity V_L = F_L sqrt(2 g D (s-1)), F_L ~1.3.
 - Jelly carcass sinking 500-1600 m/day (Lebrato et al. 2013, L&O 58:1113) -
   https://www.geomar.de/en/news/article/fast-sinking-jellyfish-could-boost-the-oceans-uptake-of-carbon-dioxide
   => s-1 ~ 0.005-0.02 for damaged bells (ASSUMPTION derived from this).
 - Joukowsky dp = rho a dv; a = sqrt(K/rho / (1 + K D/(E e))). PE100 short-term E ~0.8-1.0 GPa (lower at 35 C).
 - PE100 pressure de-rating with temperature: ISO 13761:2017 (factor table not retrieved; 0.8 at ~35 C ASSUMED)
   https://www.pe100plus.com/PE-Pipes/Technical-guidance/model/Design/Lifetime/factors-i243.html
 - Pipe ring buckling P_cr = 2E/(1-nu^2) (1/(SDR-1))^3.
 - On-bottom stability: DNV-RP-F109 / older RP-E305 style quasi-static: gamma_sc (F_D + F_I) + mu F_L <= mu W_s,
   C_D 0.9, C_L 0.9, C_M 3.29 (E305 classical), mu 0.6 sand, gamma_sc 1.1 (ASSUMED, not code-checked).
 - Juvenile salmon shear-injury threshold strain rate ~500 1/s (Neitzel et al., PNNL) - fish proxy only.
"""
import math, os, csv
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from common import *

T = "T08"
ID = V3["pipe_ID"]
SDR = 17.0
OD = ID * SDR / (SDR - 2); e = (OD - ID) / 2
rows = []
def head(Q, L, eps, nu, phi_v=0.0, K=6.0):
    A = math.pi * ID ** 2 / 4; v = Q / A
    mu_r = 1 + 2.5 * phi_v + 10.05 * phi_v ** 2 + 0.00273 * math.exp(16.6 * phi_v)
    Re = v * ID / (nu * mu_r)
    f = colebrook(Re, eps / ID)
    hf = f * L / ID * v ** 2 / (2 * g)
    hm = K * v ** 2 / (2 * g)  # entrance 0.5 + exit 1.0 + ~10 bends 0.3 + outlet valve/diffuser 1.5
    return v, Re, f, hf, hm

for L in V3["pipe_L"]:
    for Q in (1.0, 2.0, 3.0):
        for eps, el in ((0.007e-3, "new HDPE"), (0.25e-3, "aged+biofilm (ASSUMED)")):
            for phi_v in (0.0, 0.05, 0.135):
                v, Re, f, hf, hm = head(Q, L, eps, NU_20, phi_v)
                H = hf + hm
                P = RHO * (1 + 0 * phi_v) * g * Q * H / 0.75 / 1000
                rows.append(dict(L=L, Q=Q, rough=el, phi_v=phi_v, v=v, Re=Re, f=f, hf=hf, hminor=hm, H=H,
                                 P_kW_eta075=P, transit_min=L / v / 60))
with open(os.path.join(OUT, "T08_pipe_table.csv"), "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
def pick(L, Q, rough, phi): return [r for r in rows if r["L"] == L and r["Q"] == Q and r["rough"].startswith(rough) and r["phi_v"] == phi][0]

for L in V3["pipe_L"]:
    r = pick(L, 2.0, "new", 0.0); r2 = pick(L, 2.0, "aged", 0.135)
    record(T, f"total head, 2 m3/s, {L/1000:.0f} km, new pipe, water", r["H"], "m",
           "<= head tank 5-11 m (v3)", "Colebrook", verdict(r["H"], lambda v: v <= 11, lambda v: v <= 13),
           f"f={r['f']:.4f}, v={r['v']:.2f} m/s, P={r['P_kW_eta075']:.0f} kW (eta .75)")
    record(T, f"total head, 2 m3/s, {L/1000:.0f} km, aged+biofilm, 13.5% bells", r2["H"], "m",
           "<= 11 m head tank PASS; <= 13 MARGINAL", "Colebrook + Thomas", verdict(r2["H"], lambda v: v <= 11, lambda v: v <= 13),
           f"f={r2['f']:.4f}, P={r2['P_kW_eta075']:.0f} kW")
    r3 = pick(L, 3.0, "aged", 0.05)
    record(T, f"total head, 3 m3/s, {L/1000:.0f} km, aged, 5% bells", r3["H"], "m",
           "<= 11 m PASS; <= 13 MARGINAL", "Colebrook", verdict(r3["H"], lambda v: v <= 11, lambda v: v <= 13),
           f"v={r3['v']:.2f} m/s, P={r3['P_kW_eta075']:.0f} kW")
    record(T, f"transit time {L/1000:.0f} km at 2 m3/s", r["transit_min"], "min",
           "informative (Huon salmon precedent: 0.95 km, ~8 min)", "15_ s.4", "PASS")
record(T, "v3 claim check: 195 kW @3 km / 286 kW @5 km (2 m3/s, 1.2 m ID)",
       pick(3000, 2.0, "new", 0.0)["P_kW_eta075"], "kW at 3 km (eta .75)", "within +-20% of v3 195 kW",
       "Colebrook", verdict(pick(3000, 2.0, "new", 0.0)["P_kW_eta075"], lambda v: abs(v / 195 - 1) <= .2, lambda v: abs(v / 195 - 1) <= .4),
       f"5 km: {pick(5000, 2.0, 'new', 0.0)['P_kW_eta075']:.0f} kW")

# gravity vs pump: head tank as the driver
r = pick(5000, 2.0, "aged", 0.135)
record(T, "head-tank elevation for GRAVITY flow (5 km, aged, 13.5% bells) + 1 m margin", r["H"] + 1, "m above MSL",
       "<= 11 m (v3 upper) -> pump redundant", "calc", verdict(r["H"] + 1, lambda v: v <= 11, lambda v: v <= 13),
       "v3 has screw->head tank AND pump: choose one (gravity from head tank removes the pump and its shear)")

# pipe ID needed for 3 m3/s within an 11 m head tank (5 km, aged, 5 % bells)
for IDt in np.arange(1.2, 2.01, 0.05):
    A_ = math.pi * IDt ** 2 / 4; v_ = 3.0 / A_
    f_ = colebrook(v_ * IDt / NU_20, 0.25e-3 / IDt)
    H_ = (f_ * 5000 / IDt + 6.0) * v_ ** 2 / (2 * g)
    if H_ <= 10.0: break
record(T, "pipe ID needed for 3 m3/s at 5 km within 10 m head (aged, + 1 m margin to 11 m)", IDt, "m",
       "<= 1.2 m (v3) PASS; <= 1.4 m MARGINAL", "Colebrook", verdict(IDt, lambda x: x <= 1.2, lambda x: x <= 1.4))

# HGL vs pipe crest where the line crosses the breakwater (ASSUMED crest +5 / +7 m MSL, 300 m from tank)
for crest in (5.0, 7.0):
    for L in V3["pipe_L"]:
        r = pick(L, 2.0, "aged", 0.135)
        tank = r["H"] + 1.0
        hgl = tank - 0.5 * 2.0 ** 2 / (math.pi * ID ** 2 / 4) ** 2 / (2 * g) - r["hf"] * 300 / L
        ph = hgl - (crest + OD)
        record(T, f"pressure head at breakwater crest +{crest:.0f} m, {L/1000:.0f} km, gravity line", ph, "m",
               ">= +2 m (no sub-atmospheric pressure, no air release; bubbles harm jellyfish - Raskoff 2003)",
               "HGL", verdict(ph, lambda x: x >= 2, lambda x: x >= 0), f"tank {tank:.1f} m")
a_ = math.sqrt(2.34e9 / RHO / (1 + 2.34e9 * 15 / 0.7e9))  # SDR17, E 0.7 GPa
down = a_ * (2.0 / (math.pi * ID ** 2 / 4)) / g
ph_crest = pick(3000, 2.0, "aged", 0.135)["H"] + 1.0 - 5.0 - OD
record(T, "pump-trip down-surge minus pressure head at +5 m crest (pump-driven option, 3 km)", down - ph_crest, "m",
       "<= 0 PASS; <= 10 m MARGINAL (sub-atmospheric, air release); > 10 m FAIL (vapour -> column separation)", "Joukowsky",
       verdict(down - ph_crest, lambda x: x <= 0, lambda x: x <= 10), "pump option needs surge vessel/air valves or slow-closing check valve; gravity option avoids it")

# minimum velocity
for sm1 in (0.005, 0.02):
    VL = 1.3 * math.sqrt(2 * g * ID * sm1)
    for Q in (1.0, 2.0):
        v = Q / (math.pi * ID ** 2 / 4)
        record(T, f"velocity vs deposit limit (s-1={sm1}), Q={Q}", v / VL, "x V_L", ">= 1.5 PASS; >= 1.0 MARGINAL",
               "Durand; Lebrato 2013 sinking", verdict(v / VL, lambda x: x >= 1.5, lambda x: x >= 1.0),
               f"v={v:.2f}, V_L={VL:.2f} m/s")
# bell/pipe size ratio
record(T, "bell-to-pipe diameter ratio d/D", 0.45 / ID, "-", "<= 0.33 (large-particle plug/bridging guide, ASSUMPTION)",
       "geometry", verdict(0.45 / ID, lambda x: x <= 0.33, lambda x: x <= 0.4), "45 cm bell in 1.2 m ID")

# shear in pipe
r = pick(3000, 2.0, "new", 0.0)
eps_d = r["f"] * r["v"] ** 3 / (2 * ID)
tau_w = r["f"] / 8 * RHO * r["v"] ** 2
strain_bulk = math.sqrt(eps_d / NU_20)
record(T, "bulk turbulent strain rate sqrt(eps/nu), 2 m3/s", strain_bulk, "1/s",
       "< 500 1/s (juvenile salmon injury threshold; fish proxy) PASS", "Neitzel et al. (PNNL), fish proxy",
       verdict(strain_bulk, lambda x: x < 500), f"wall shear {tau_w:.1f} Pa; NO jellyfish threshold exists")

# ---------- surge ----------
K = 2.34e9
for E, el in ((1.0e9, "PE100 E=1.0 GPa (20 C)"), (0.7e9, "PE100 E~0.7 GPa (35 C, ASSUMED)")):
    for sdr in (17.0, 26.0):
        a = math.sqrt(K / RHO / (1 + K * (sdr - 2) / E))
        dv = 2.0 / (math.pi * ID ** 2 / 4)
        dH = a * dv / g
        PN = (10.0 if sdr == 17 else 6.3) * 0.8   # bar, 35 C derated (ASSUMED 0.8)
        steady = 1.0  # bar max steady at head tank end (~10 m)
        record(T, f"Joukowsky surge, instant stop [{el}, SDR{sdr:.0f}]", dH, "m",
               "steady+surge <= 2.0 x derated PN (PE occasional-surge allowance, PPI/industry; ASSUMED)",
               "Joukowsky", verdict(steady + dH / 10.2, lambda x: x <= 2 * PN, lambda x: x <= 2.5 * PN),
               f"a={a:.0f} m/s, peak {steady + dH/10.2:.1f} bar vs 2xPN {2*PN:.1f}; down-surge {dH:.0f} m -> vacuum/column separation at high points")
# column separation & ring collapse under full vacuum
for sdr in (17.0, 26.0, 33.0):
    for E in (0.7e9, 0.2e9):
        Pcr = 2 * E / (1 - 0.45 ** 2) * (1 / (sdr - 1)) ** 3 / 1e5
        record(T, f"HDPE ring-buckling pressure SDR{sdr:.0f}, E={E/1e9:.1f} GPa", Pcr, "bar",
               ">= 2 x 1.0 bar (full vacuum, SF 2) PASS; >= 1 MARGINAL", "P_cr formula",
               verdict(Pcr, lambda x: x >= 2.0, lambda x: x >= 1.0), "E=0.2 GPa ~ long-term creep modulus at 35 C (ASSUMED)")
# gravity line deceleration time vs 2L/a
for L in V3["pipe_L"]:
    v = 1.77; Hd = pick(L, 2.0, "new", 0.0)["H"]
    Tdec = L * v / (g * Hd); Tw = 2 * L / 300
    record(T, f"gravity-line run-down time vs 2L/a ({L/1000:.0f} km)", Tdec / Tw, "x", ">1 => slow (rigid-column) transient, not Joukowsky",
           "rigid column", verdict(Tdec / Tw, lambda x: x > 1), f"run-down ~{Tdec:.0f} s; 2L/a {Tw:.0f} s")

# ---------- on-bottom stability ----------
rho_pe = 958.0
m_pipe = math.pi / 4 * (OD ** 2 - ID ** 2) * rho_pe
buoy = math.pi / 4 * OD ** 2 * RHO
m_cont = math.pi / 4 * ID ** 2 * RHO
Ws_full = (m_pipe + m_cont - buoy) * g
Ws_empty = (m_pipe - buoy) * g
record(T, "submerged weight, water-filled, no ballast", Ws_full / 1000, "kN/m", "> 0 (sinks)", "Archimedes",
       verdict(Ws_full, lambda x: x > 0), f"OD {OD:.2f} m SDR17, pipe {m_pipe:.0f} kg/m")
record(T, "submerged weight, air-filled, no ballast", Ws_empty / 1000, "kN/m", "> 0", "Archimedes",
       verdict(Ws_empty, lambda x: x > 0), "air ingress at the head tank would float the line")

def stab_req(Hs, Tp, h, U, D=OD, CD=0.9, CL=0.9, CM=3.29, mu=0.6, gam=1.1, Hfac=1.86):
    H = min(Hfac * Hs, 0.78 * h)
    k = wavenumber(Tp, h); w = 2 * math.pi / Tp
    ub = H / 2 * w / math.sinh(k * h); ab = ub * w
    req = 0
    for ph in np.linspace(0, 2 * math.pi, 180):
        u = ub * math.cos(ph) + U; a = -ab * math.sin(ph)
        FD = 0.5 * RHO * CD * D * u * abs(u); FI = RHO * CM * math.pi * D ** 2 / 4 * a
        FL = 0.5 * RHO * CL * D * u ** 2
        req = max(req, gam * abs(FD + FI) / mu + FL)
    return req, H, ub

stab = []
for (h, lbl) in ((3.5, "nearshore 3-4 m"), (7.0, "5 km out ~7-9 m")):
    for Hs, Tp, U, cl in ((0.84, 4.0, SITE["cur_p99"], "p99 Hs + p99 current"),
                          (1.36, 4.5, SITE["cur_max"], "max Hs + max current"),
                          (3.0, 7.0, SITE["cur_max"], "storm, depth-limited")):
        req, H, ub = stab_req(Hs, Tp, h, U)
        ballast = max(0, req - Ws_full)
        conc = ballast / ((2400 - RHO) * g)  # m3 concrete per m
        stab.append(dict(h=h, case=cl, H=H, u_bottom=ub, Ws_req=req, ballast=ballast, concrete_m3_per_m=conc))
        record(T, f"on-bottom stability: required submerged weight [{lbl}; {cl}]", req / 1000, "kN/m",
               "ballast <= 1.0 m3 concrete per m (practical collar) PASS; <= 2 MARGINAL",
               "DNV-RP-F109-style simplified (E305 coeffs)", verdict(conc, lambda x: x <= 1.0, lambda x: x <= 2.0),
               f"H={H:.2f} m, u_b={ub:.2f} m/s, concrete {conc:.2f} m3/m (~{conc*2.4:.1f} t/m)")
with open(os.path.join(OUT, "T08_stability.csv"), "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=stab[0].keys()); w.writeheader(); w.writerows(stab)
# ballast to keep pipe down when 50% air-filled
need_air = -(m_pipe + 0.5 * m_cont - buoy) * g
record(T, "ballast to keep the line down if half air-filled", need_air / 1000, "kN/m",
       "covered by stability ballast? (compare row above)", "Archimedes", "PASS",
       f"= {need_air/((2400-RHO)*g):.2f} m3 concrete/m")

# ---------- thermal ----------
alpha = 2.0e-4
for dT, lbl in ((15.8, "seasonal water 20->35.8 C"), (40.0, "exposed on breakwater, sun 25->65 C (ASSUMED)")):
    for L in ((V3["pipe_L"]) if dT < 20 else (200.0,)):
        dL = alpha * L * dT
        record(T, f"free thermal length change [{lbl}], {L/1000:.1f} km", dL, "m", "must be restrained/anchored",
               "alpha=2e-4 /K (PE)", "PASS" if dT < 20 else "MARGINAL")
    for E in (0.8e9, 0.3e9):
        sig = E * alpha * dT / 1e6
        record(T, f"fully-restrained thermal stress [{lbl}], E={E/1e9:.1f} GPa", sig, "MPa",
               "<= 8 MPa PE100 design stress (MRS10/1.25) PASS; <= 10 MARGINAL", "E alpha dT",
               verdict(sig, lambda x: x <= 8, lambda x: x <= 10), "short-term E overestimates (creep relaxes)")

# chart: power vs Q
fig, ax = plt.subplots(figsize=(7, 4))
Qs = np.linspace(0.5, 3.5, 40)
for L in V3["pipe_L"]:
    for eps, phi_v, ls, lab in ((0.007e-3, 0, "-", "new, water"), (0.25e-3, 0.135, "--", "aged, 13.5% bells")):
        P = [RHO * g * q * sum(head(q, L, eps, NU_20, phi_v)[3:5]) / 0.75 / 1000 for q in Qs]
        ax.plot(Qs, P, ls, label=f"{L/1000:.0f} km, {lab}")
ax.axvline(2.0, color="grey", ls=":"); ax.set_xlabel("flow (m3/s)"); ax.set_ylabel("hydraulic power at eta 0.75 (kW)")
ax.set_title("T08 Export pipe (1.2 m ID) power"); ax.legend(fontsize=8); ax.grid(alpha=.3)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "T08_pipe_power.png"), dpi=130)
save(T, dict(OD=OD, e=e, m_pipe=m_pipe, stab=stab))
