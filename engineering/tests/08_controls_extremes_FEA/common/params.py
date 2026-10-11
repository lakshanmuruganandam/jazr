"""Shared design basis for TESTS/08 (controls, extremes, FEA).

Every number carries a tag:
  [V3]   taken from JAZR_GATE_v3.md / 16_FLAW_AUDIT.md
  [DATA] computed from TESTS/00_data/raw (Open-Meteo ERA5 / marine, 2015-2025 / 2022-2025)
  [LIT]  literature value, source in SOURCES below
  [ASM]  our assumption (no the plant-specific data is public) -> change here, re-run
  [ENG]  standard engineering practice value (textbook / code typical), not site-verified
Units: SI (N, m, s, kg, Pa) unless the name says otherwise.
"""
import math

RHO_W = 1025.0          # seawater density [ENG]
G = 9.81
RHO_AIR = 1.20          # [ENG] (hot air ~1.13 at 45 C; 1.20 conservative-ish)

# ---------------- geometry (one gantry bay) ----------------
BAY_W = 10.0            # m, bay width [V3: bays ~10 m x 5-7 m]
SEABED_Z = -7.5         # m MSL, design channel bed [ASM within V3/audit -5.5 to -9.5 m MSL]
HAT_Z = +1.2            # m MSL, highest astronomical tide ~ half of 2.3 m range [ASM from audit tide 1.5-2.3 m]
LAT_Z = -1.2            # m MSL [ASM symmetric]
DECK_Z = +6.0           # m MSL, top of pile / gantry girder centroid [ASM; checked in C_extremes air-gap]
DECK_SOFFIT_Z = +5.6    # m MSL, underside of girder [ASM]
DRUM_Z = +7.5           # m MSL, drum axle [ASM]
PILE_FIXITY_DEPTH_D = 5.0  # equivalent fixity depth below seabed in pile diameters [ENG 3-7D range; sensitivity run]
MESH_DROP = DRUM_Z - SEABED_Z  # m, mesh hangs drum -> floor sill (always full height) [V3 closed bottom]

# ---------------- sections (none given in v3 -> sized here) [ASM] ----------------
STEEL = dict(E=210e9, G=81e9, rho=7850.0, fy=355e6, name="S355 carbon steel (piles, girder), coated + CP")
DUPLEX = dict(E=200e9, G=77e9, rho=7800.0, fy=450e6, name="Duplex 2205 (UNS S32205) frame/drum")
SDUPLEX = dict(E=200e9, G=77e9, rho=7800.0, fy=550e6, name="Super-duplex 2507 (UNS S32750)")
PILE_D, PILE_T = 1.016, 0.022     # CHS 1016 x 25 nominal minus 3 mm corrosion allowance [ASM]
GIRDER_H, GIRDER_B, GIRDER_T = 0.80, 0.60, 0.020   # welded box girder [ASM]
POST_B, POST_T = 0.30, 0.012      # SHS 300x12 duplex drum-frame posts [ASM]
DRUM_D, DRUM_T = 0.610, 0.010     # drum core CHS 610x10 duplex [ASM]
MARINE_GROWTH = 0.05              # m thickness on permanently wet piles [ENG, DNV-RP-C205 typical Gulf 50-100 mm]

# ---------------- masses / gravity loads ----------------
MESH_AREAL_MASS = 8.0             # kg/m2 woven 2205 mesh, 2.5 mm wire, 10 mm aperture (computed in mesh_check) [ASM]
BOTTOM_BAR_MASS_PER_M = 60.0      # kg/m weighted bottom bar [ASM]
DRIVE_MASS = 800.0                # kg motor + gearbox + brake + load cell frame at one post [ASM]
DECK_FURNITURE = 1.5e3            # N/m grating + handrail + cable tray on girder [ENG]
LIVE_WALKWAY = 3.0e3              # N/m (2.5 kPa x 1.2 m walkway) [ENG]

# ---------------- hydraulics / operation ----------------
Q_UNIT = 100.0                    # m3/s per unit nominal [V3]
Q_UNIT_MAX = 172.5                # m3/s per unit max [V3/audit]
LANE_W = 28.0                     # m lane width at 7 m depth [V3]
SCREEN_AREA = 1000.0              # m2 per unit [V3]
V_APPROACH_SCREEN = 0.10          # m/s design through-screen approach velocity [V3, NMFS]
V_LANE = 0.5                      # m/s [V3]
MESH_WIRE_D = 0.0025              # m [ASM]
MESH_APERTURE = 0.010             # m clear (audit: 10-20 mm) [ASM]
DP_TRIP = 500.0                   # Pa, per-bay roll-up trigger (v3 gives no number; audit 200 Pa is inside wave noise) [ASM]
DP_HARD = 1500.0                  # Pa, local hard-wired roll-up independent of PLC/comms [ASM]
DP_ACCIDENT = 3000.0              # Pa, stuck-drum fully blinded bay (~0.3 m head across line) [ASM]
MEMBRANE_SAG_RATIO = 0.03         # sag/span of mesh spanning between pile rails [ASM; sensitivity 2-8 %]
RAIL_FRICTION = 0.3               # mesh edge in guide rail during roll-up under DP [ENG]
PULSE_LIMIT_KG = 1000.0           # [V3: each pulse < 1 t]
BELL_MASS = 3.0                   # kg [V3]
DESIGN_DENSITY = 0.3              # ind/m3 [V3]
N_BAYS_UNIT = 16                  # 1000 m2 / (10 m x ~7 m) ~ 14.3 -> 15 screen bays + 1 relief bay [V3-derived]
DRUM_LINE_SPEED = 0.10            # m/s mesh lowering/raising (roller-shutter class) [ASM]
DEPLOY_CLAIM_S = 600.0            # [V3: whole line in ~10 min]

# ---------------- metocean ----------------
WIND_SURVIVAL_GUST = 45.0         # m/s 3-s gust @10 m, 50-yr: Dubai legacy basic wind speed (BMT/Dubai Municipality); Abu Dhabi value not found [LIT]
WIND_OPERATE_GUST = 20.0          # m/s 3-s gust limit for roll-down/roll-up [ASM]
HS100 = 4.0                       # m, 100-yr Hs at 9-16 m depth: 3.0-4.5 m (Neelamani et al., WAM 1993-2004) upper-mid [LIT]
TP100 = 8.0                       # s, storm peak period (fetch-limited Gulf shamal) [ASM; data max mean period 6.25 s]
SURGE100 = 0.6                    # m storm surge (no UAE-specific value found; Jebel Ali 1:100 total level 2.71 mCD incl. SLR to 2058) [ASM]
SLR_2085 = {"SSP2-4.5 median": 0.45, "SSP5-8.5 median": 0.61, "SSP5-8.5 likely-high": 0.82, "low-confidence high-end": 1.5}  # m, linear interp AR6 2050->2100 [LIT/ASM]
CURRENT_SURV = 1.0                # m/s storm current [DATA: near-site model max 1.4 km/h... see C_extremes] [ASM]
CD_PILE, CM_PILE = 1.05, 2.0      # rough (marine growth) [ENG DNV-RP-C205]
SST_MAX_DESIGN = 38.0             # C [brief 36-38; DATA max 35.9-36.3 at 0.04 deg grid]
AIR_MAX = 41.2                    # C [DATA ERA5 2015-2025 max at 23.75N 52.25E grid; inland UAE >48 C]

LIFE_YEARS = 60                   # [V3]
DEPLOYED_FRACTION = 2.0 / 12.0    # [V3: rolled up ~10 months/year]

SOURCES = {
    "Irfan2012": "Irfan M., Khan Z.H., El-Emam M., Abdalla J. (2012) Seismic Hazard Assessment and Spectral Accelerations for UAE, 15WCEE Lisbon, paper 5594, Table 4 (ABD 2475-yr rock: PGA 0.074 g, Ss 0.178 g, S1 0.075 g). https://www.iitk.ac.in/nicee/wcee/article/WCEE2012_5594.pdf (copy in B_seismic/)",
    "Neelamani": "Neelamani S., Rakha K., Al-Salem K. - Extreme waves in the Arabian Gulf (WAM hindcast 1993-2004, 38 sites): 100-yr Hs 3.0-4.5 m at 9-16 m depth, 5-7 m offshore. https://iahr.org/library/info?pid=20019",
    "Varghese2016": "Varghese T., Nayak S., Bhat G. (2016) Estimation of extremes in the southern Arabian Gulf, J. Oceanogr. Mar. Sci. 7(3):24-32 - Jebel Ali 1:50/1:100/1:250 water levels 2.64/2.71/2.79 mCD with SLR to 2058. https://repository.ias.ac.in/103599",
    "AR6": "IPCC AR6 WG1 Ch.9: GMSL 2100 vs 1995-2014 likely 0.44-0.76 m (SSP2-4.5), 0.63-1.01 m (SSP5-8.5); medians 0.56/0.77 m, 2050 medians 0.20/0.23 m (Table 9.9, medians from memory - verify). https://www.ipcc.ch/report/ar6/wg1/chapter/chapter-9/",
    "DubaiWind": "Dubai Municipality / BMT: basic 3-s gust 45 m/s reducible to 38 m/s; Dubai temporary buildings 32 m/s 50-yr. Abu Dhabi code (ADIBC, IBC2009/ASCE 7-05) keeps municipal values (not found). https://gulfconstructiononline.com/Article/6032/",
    "ENEC_Fukushima": "ENEC/FANR Fukushima response (2012): the plant is a dry site; elevations chosen vs surge, tsunami and combinations; dust: penetrations >6 m above grade. https://www.mofa.go.jp/policy/energy/fukushima_2012/pdfs/ws_2_06.pdf",
    "DNV_C203": "DNV-RP-C203 Fatigue design of offshore steel structures: S-N curve D in seawater with CP (log a1=11.764 m=3, N<=1e6; log a2=15.606 m=5), free corrosion D (log a=11.687, m=3); DFF 3 for non-inspectable submerged [ENG, values from standard, verify edition]",
    "DNV_C205": "DNV-RP-C205 Environmental conditions and loads: Morison Cd 0.65 smooth / 1.05 rough, Cm 1.6-2.0 [ENG]",
    "ASCE7": "ASCE 7-05/IBC 2009 design spectrum: SDS=2/3 Fa Ss, SD1=2/3 Fv S1, Site Class D Fa=1.6 (Ss<=0.25), Fv=2.4 (S1<=0.1) [ENG]",
    "APR1400": "APR1400 standard design (US NRC DC) certified seismic design response spectra anchored at 0.3 g PGA [ENG, verify; the plant site-specific SSE not public]",
    "ISA18.2": "ANSI/ISA-18.2-2016 & EEMUA 191: ~1 alarm/10 min manageable (<=6/h), >10 alarms/10 min per operator = alarm flood [ENG]",
    "IEC62443": "IEC 62443-3-3 foundational requirements FR1-FR7; IAEA NSS 17-T (2021) computer security for nuclear facilities; US NRC RG 5.71 defensive architecture (one-way to safety levels) [ENG]",
    "NMFS2022": "NMFS (2022) Anadromous Salmonid Passage Design: active-screen approach 0.40 ft/s (0.12 m/s) [V3/audit]",
    "ICE3": "Circular Ecology ICE database v3.0 (2019) embodied carbon factors [ENG, values from memory - verify]",
    "worldsteel": "worldsteel 2023 sustainability indicators ~1.9 t CO2/t crude steel [ENG, verify]",
}
