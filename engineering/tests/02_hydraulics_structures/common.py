"""Shared constants, site data and result logging for the JAZR Gate v3
hydraulics & structures test suite.

Every number here is either (a) a SITE FACT taken from the project files
(05_fact_check.md, agent_ps_oceanography.md, JAZR_GATE_v3.md), (b) a
STANDARD physical constant, or (c) an ASSUMPTION, labelled as such.
"""
import json, os, math
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
os.makedirs(OUT, exist_ok=True)

g = 9.81
# ---------------- seawater properties ----------------
RHO = 1025.0          # kg/m3 nominal seawater. At 35 C / 45 PSU EOS gives ~1027; 0.2% effect -> ignored
NU_20 = 1.05e-6       # m2/s kinematic viscosity seawater ~20 C (standard tables)
NU_35 = 0.76e-6       # m2/s ~35 C (standard tables)

# ---------------- SITE FACTS (project files) ----------------
SITE = dict(
    depth_nearshore=(3.0, 4.0),       # m, GEBCO, 1-3 km offshore (agent_ps_oceanography.md)
    channel_depth_MSL=(5.5, 9.5),     # m below MSL, NMDC dredged channels (05_fact_check #31)
    channel_assumed=(5.0, 7.0),       # m, task brief assumption for the JAZR lane
    cur_median=0.083, cur_p99=0.194, cur_max=0.306,   # m/s, Copernicus SMOC model cell (05 #39)
    Hs_median=0.22, Hs_p90=0.58, Hs_p99=0.84, Hs_max=1.36,  # m (offshore model cell)
    T_mean=(2.5, 3.0),                # s mean wave period (oceanography file)
    wind_p99=9.3, wind_max_hourly=13.2, gust_max=19.6,      # m/s ERA5 2015-2024
    T_water=(20.0, 35.8),             # C
    S=(38.0, 48.0),                   # PSU
    tide_range=(1.45, 2.3),           # m daily .. spring
    Q_unit=100.0, Q_unit_max=172.5,   # m3/s per unit (WNN / NS Energy)
    units=4,
    P_unit_gross_MW=1400.0, P_plant_gross_MW=5600.0, P_unit_net_MW=1345.0,
)

# ---------------- JAZR v3 DESIGN VALUES (JAZR_GATE_v3.md) ----------------
V3 = dict(
    Va=0.10,              # m/s approach velocity (NMFS 2022 tidal / >60 s exposure)
    theta_deg=11.0,       # screen angle to flow
    L_screen=(143.0, 200.0),  # m per unit (7 m and 5 m deep)
    lane_W=(28.0, 39.0),  # m
    bay_w=10.0,           # m bay width
    bay_h=(5.0, 7.0),     # m bay drop (v3 text)
    bypass_spacing=30.0,  # m
    Q_bypass=2.0,         # m3/s per line
    design_density=0.3,   # ind/m3
    pulse_limit_t=1.0,    # t per bay roll-up
    pipe_ID=1.2, pipe_L=(3000.0, 5000.0),
    head_tank=(5.0, 11.0),
)

# ---------------- JELLYFISH (C. mosaicus) ----------------
BELL = dict(
    d=0.375,              # m mid of 30-45 cm (brief)
    d_range=(0.30, 0.45),
    mass=3.0,             # kg wet (brief, ~96% water)
    vol=0.003,            # m3 (3 kg / ~1025 kg/m3)
    # ASSUMPTION: an impinged bell flattens to its bell diameter -> projected area
    a_face=math.pi * 0.375**2 / 4,   # 0.110 m2
    # ASSUMPTION: flattened bell protrudes ~0.12 m from the face -> side area for sweep drag
    a_side=0.375 * 0.12,
    Cd_side=1.0,          # ASSUMPTION bluff body
    mu_fric=(0.1, 0.3),   # ASSUMPTION wet gel-on-mesh friction coefficient (NO DATA; tank test item)
)

_RESULTS = []

def verdict(value, pass_if, marginal_if=None):
    """pass_if / marginal_if are callables value->bool."""
    if pass_if(value):
        return "PASS"
    if marginal_if is not None and marginal_if(value):
        return "MARGINAL"
    return "FAIL"

def record(test, check, value, unit, criterion, source, verdict_str, note=""):
    r = dict(test=test, check=check, value=(round(value, 4) if isinstance(value, (int, float)) else value),
             unit=unit, criterion=criterion, source=source, verdict=verdict_str, note=note)
    _RESULTS.append(r)
    print(f"[{verdict_str:8s}] {test} | {check}: {r['value']} {unit}  (crit: {criterion})")
    return r

def save(test_id, extra=None):
    path = os.path.join(OUT, f"{test_id}_results.json")
    with open(path, "w") as f:
        json.dump(dict(checks=[r for r in _RESULTS if r["test"].startswith(test_id)], extra=extra or {}),
                  f, indent=1, default=float)
    return path

# ---------------- small physics helpers ----------------
def wavenumber(T, h):
    """Linear dispersion: omega^2 = g k tanh(k h); Newton iteration."""
    w = 2 * math.pi / T
    k = w * w / g
    for _ in range(100):
        f = g * k * math.tanh(k * h) - w * w
        df = g * math.tanh(k * h) + g * k * h / math.cosh(k * h) ** 2
        k -= f / df
    return k

def colebrook(Re, rel_rough):
    if Re < 2300:
        return 64 / Re
    f = 0.02
    for _ in range(60):
        f = (-2.0 * math.log10(rel_rough / 3.7 + 2.51 / (Re * math.sqrt(f)))) ** -2
    return f

def zeta_perforated(f_open):
    """Idelchik (Handbook of Hydraulic Resistance, Diagram 8-1), thin sharp-edged
    perforated plate, Re>1e5, loss coefficient referred to the approach velocity."""
    return (0.707 * (1 - f_open) ** 0.375 + 1 - f_open) ** 2 / f_open ** 2

def zeta_wire_mesh(f_open):
    """Idelchik Diagram 8-6 woven wire screen (Re>1e3): zeta = 1.3(1-f) + (1/f - 1)^2."""
    return 1.3 * (1 - f_open) + (1 / f_open - 1) ** 2

def zeta_kirschmer(beta, s, b, alpha_deg):
    """Kirschmer bar-rack: h = beta (s/b)^(4/3) sin(alpha) v^2/2g."""
    return beta * (s / b) ** (4 / 3) * math.sin(math.radians(alpha_deg))
