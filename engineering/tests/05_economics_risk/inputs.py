"""All model inputs, each with a range and a source label.

Labels:
  VERIFIED   - read from a primary/secondary source this session or in 13_/14_ files
  DOC        - stated in JAZR_GATE_v3.md / 16_FLAW_AUDIT.md (team or auditor estimate)
  MODEL      - output of the team's toy twin (ranking only, not a prediction)
  ASSUMED    - engineering/economic assumption, NOT verified; change it if you know better
Triangular (low, mode, high) unless stated.
"""
AED_PER_USD = 3.6725  # fixed peg (VERIFIED, public)

PLANT = dict(
    units=4,
    net_mwe=1337.0,           # VERIFIED: WNA reactor database, each the plant unit 1337 MWe net
    load_factor=(0.837, 0.86, 0.896),  # VERIFIED: WNA 2024 load factors U2 85.2%, U3 85.9%, U4 83.7%; U1 2023 89.6%
    site_site_years_observed=5.5,   # VERIFIED-derived: U1 commercial Apr 2021 -> Oct 2026, 0 public events (13_ §J)
)

ECON = dict(
    # USD/MWh value of a lost MWh (replacement power). the plant PPA price is NOT public (VERIFIED: ENEC/WNN describe
    # PPA structure only). Low anchor: Fujairah F3 CCGT tariff bids 2019 ~16.8 fils/kWh = ~US$46/MWh (VERIFIED, MEED,
    # own conversion). Mode: AED 184/MWh = US$50 (v3 doc, UNVERIFIED) rounded up for gas-fuel replacement.
    # High: LNG-priced fuel at $10-14/MMBtu x 6.5-7 MMBtu/MWh ~ $65-98 (ASSUMED).
    value_usd_per_mwh=(46.0, 60.0, 100.0),
    # Fixed cost per outage event (repairs, extra crews, restart, regulator reporting), USD M. ASSUMED.
    fixed_cost_per_event_musd=(0.1, 0.5, 2.0),
    # Today's site bloom-response spend (boats/crews/watch), USD M per site-year. Anchor: Gravelines ~EUR 1.5 M over
    # 3 years + EUR 30k/yr observation (VERIFIED in 13_ §K) -> ~US$0.55 M/yr. Range ASSUMED.
    response_cost_musd_per_site_yr=(0.2, 0.55, 1.5),
    # Fraction of today's response spend JAZR removes (crew-hours table, v3 §3). ASSUMED.
    response_cost_saved_frac=(0.3, 0.6, 0.9),
    discount_rates=(0.03, 0.06, 0.08, 0.10),
    horizon_years=30,          # ASSUMED marine-structure design life (plant licence is longer)
    build_years=2,             # ASSUMED: capex spent years 0-1, benefits from year 2
)

JAZR = dict(
    # Fraction of swarm reaching the intake WITH JAZR. MODEL (v3 §4 twin, toy): 5.5% median conditions,
    # 12% onshore drift, 13% 10-day bloom, 28% inner screen only 50% efficient. Today = 95-100%.
    reach_frac=(0.055, 0.12, 0.28),
    reach_frac_today=0.95,
    # Probability JAZR is deployed and working when a bloom arrives (availability). ASSUMED.
    availability=(0.85, 0.95, 0.99),
)

# ---- CAPEX per unit, USD M ----
# Case A ("v3 stated"): AED 30-80 M per unit (16_FLAW_AUDIT row 10 / v3 §5) -> USD 8.2-21.8 M.
CAPEX_CASE_A_AED_M = (30.0, 50.0, 80.0)
# Case B ("bottom-up"): components below. ALL unit rates ASSUMED [ENG], except HDPE outfall rate which is the
# auditor's [ENG] USD 1.5-3 k/m (16_ row 10). Cross-check: Glenn-Colusa (GCID) fish screen project ~US$75 M (1998-2001,
# 3,000 cfs ~85 m3/s, ~1,100 ft flat-plate screen + river gradient facility; VERIFIED, Water Education Foundation GCID
# briefing PDF) ~ US$145 M in 2025 dollars (US CPI ratio ~1.93, approximate).
CAPEX_COMPONENTS_MUSD = {
    "training_wall_150-200m":       (1.5, 4.0, 10.0),   # sheet-pile/caisson wall, 10-50 k$/m ASSUMED
    "piled_gantry_150-200m":        (3.0, 6.0, 15.0),   # pile trestle + deck + rails, 20-75 k$/m ASSUMED
    "mesh_bays_drums_rails_motors": (2.0, 4.0, 8.0),    # 15-20 bays ASSUMED
    "bypass_camera_screw_headtank_pump": (2.0, 4.0, 8.0),  # ASSUMED
    "seabed_HDPE_pipe_5km_1.2mID":  (7.5, 10.0, 15.0),  # 1.5-3 k$/m x 5 km (auditor [ENG])
    "outlets_x2_diffusers":         (0.5, 1.0, 3.0),    # ASSUMED
    "controls_OS_sensors_share":    (0.03, 0.07, 0.27), # < AED 1 M site (v3 §5) / 4 units
}
CAPEX_MARKUPS = {
    "engineering_nuclearQA_licensing_seismic": (0.20, 0.30, 0.40),  # fraction of direct, ASSUMED
    "contingency": (0.20, 0.35, 0.50),                               # fraction of direct+eng, ASSUMED
}
# Outer guide line (Stage 2, site-wide): not costed in v3 ("sized after the pilot"). Excluded from base; ASSUMED range
# for sensitivity only.
OUTER_GUIDE_MUSD_SITE = (10.0, 25.0, 60.0)

# ---- OPEX per unit per year ----
OPEX = dict(
    maintenance_frac_of_direct=(0.02, 0.03, 0.04),   # ASSUMED (marine civil + mechanical)
    staff_drills_musd=(0.05, 0.15, 0.30),            # 1-2 operators seasonal + drills, ASSUMED
    pigging_inspection_musd=(0.05, 0.15, 0.30),      # pipe pigging, pre-season inspection, ASSUMED
    operating_hours=(300.0, 800.0, 1440.0),          # alert-driven hours/yr; max = 2 months stored-wet (v3) ASSUMED
)

# ---- Power draw per line (kW) ----
POWER = dict(
    pipe_pump_kw=(195.0, 240.0, 286.0),   # DOC v3 §2: 195 kW @3 km, 286 kW @5 km (2 m3/s, 1.2 m ID)
    screw_head_m=(5.0, 8.0, 11.0),        # DOC v3 §2 head tank 5-11 m
    screw_eff=(0.70, 0.75, 0.80),         # ASSUMED typical Archimedes screw efficiency
    flow_m3s=2.0,                         # DOC v3 §2
    aux_kw=(20.0, 35.0, 50.0),            # drums, cameras, sprays, ASSUMED
)

# ---- Emissions factors ----
EMIS = dict(
    # Marginal grid factor for displaced electricity (gas). VERIFIED range: UAE grid 0.359 (LowCarbonPower 2023) to
    # 0.468 kgCO2/kWh (Ember/OWID 2024 via inzonex); DEWA 2020 0.404.
    grid_kg_per_kwh=(0.359, 0.404, 0.468),
    diesel_kg_per_l=2.68,                 # standard IPCC/DEFRA combustion factor (well known; not re-fetched)
    # Embodied carbon, tCO2e per tonne. ICE database (Hammond & Jones, v3) order-of-magnitude values recalled, NOT
    # re-fetched tonight -> treat as ASSUMED.
    steel_t_per_t=(1.4, 1.9, 2.5),
    hdpe_t_per_t=(1.9, 2.5, 3.0),
    concrete_t_per_t=(0.10, 0.13, 0.20),
    # Material quantities per unit, tonnes. ASSUMED [ENG] except HDPE (166 kg/m SDR26, 16_ audit row 4).
    steel_t=(1000.0, 1600.0, 2500.0),
    hdpe_t=(600.0, 830.0, 1200.0),
    concrete_ballast_t=(2500.0, 5000.0, 7500.0),
    marine_install_tco2=(200.0, 500.0, 1500.0),    # vessel fuel for installation, ASSUMED
    # Status quo boats: Gravelines 3 boats 24/7 (Jun-Aug 2026) and 7 boats 24/7 (wave 2) (VERIFIED 13_/14_).
    boats=(3.0, 4.0, 7.0),
    boat_days_per_bloom=(5.0, 10.0, 15.0),         # ASSUMED
    boat_l_per_h=(20.0, 40.0, 60.0),               # small trawler, ASSUMED
    blooms_per_year=(1.0, 2.0, 5.0),               # alerts with arrival, ASSUMED
    # Bubble curtain (public figures): 135 kW (our 03_ file, earlier README) / 440 kW and 12.6 tCO2 per event on gas grid,
    # 31 MWh per long event (current public README, VERIFIED 11 Oct 2026).
    bubblecurtain_kw_old=135.0,
    bubblecurtain_kw_new=440.0,
    bubblecurtain_mwh_per_event=31.0,
    bubblecurtain_tco2_per_event_reported=12.6,
)

# ---- Unit-day energy ----
def unit_day_mwh(net_mwe=PLANT["net_mwe"]):
    return net_mwe * 24.0
