"""Shared parameters for the 04_biology_wildlife_ops test pack.

Every number carries a tag:
  [DESIGN]  taken from JAZR_GATE_v3.md
  [SRC n]   literature, see SOURCES below (and README.md reference list)
  [ASSUME]  our assumption, NOT data -- must be replaced by measurement
  [DERIVED] computed here from the above
"""
import json, math, os

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
CH = os.path.join(HERE, "charts")
os.makedirs(RES, exist_ok=True)
os.makedirs(CH, exist_ok=True)

RHO = 1025.0          # kg/m3 seawater
NU_35C = 7.3e-7       # m2/s kinematic viscosity of seawater at ~35 C, S~40 [standard property tables]
MU_35C = RHO * NU_35C

# ---- JAZR design values [DESIGN] ----
Q_UNIT = 100.0        # m3/s per unit (ENEC ~6000 m3/min) ; max 172.5
Q_UNIT_MAX = 172.5
V_APPROACH = 0.10     # m/s through-screen
V_SWEEP = 0.50        # m/s along the screen
V_BYPASS = (0.4, 0.7) # m/s bypass mouth (NMFS >110% channel velocity)
ENTRANCE_SPACING = 30.0  # m
SCREEN_LEN = (143.0, 200.0)
BAY_WIDTH = 10.0      # m
Q_LINE = 2.0          # m3/s bypass flow per line
PIPE_D = 1.2          # m inside diameter
PIPE_L = (3000.0, 5000.0)
PIPE_KW = {3000.0: 195.0, 5000.0: 286.0}
SCREW_D = 3.05        # m, Red Bluff analogue [SRC 7]
SCREW_RPM = 26.5      # Red Bluff [SRC 7]
SCREW_FLIGHTS = 3     # [ASSUME] typical 3-flight Archimedes screw
BELL_D = (0.30, 0.45) # m [DESIGN/ENEC brief]
BELL_MASS = 3.0       # kg typical, 5 kg upper [SRC science pack, estimate]
DENSITY_DESIGN = 0.3  # ind/m3 [DESIGN]
DENSITY_RANGE = (0.1, 0.3, 1.0)
SST_MAX = 35.8        # C, the brief's thermal case (fact-check reproduced Aug mean 34.9)
UNITS = 4

SOURCES = {
 1: "NMFS (2022) Anadromous Salmonid Passage Design Manual s8.5 (via 15_jazr_gate_precedents.md)",
 2: "Neitzel et al. 2004 Trans Am Fish Soc 133:447 -- no significant injury below strain rate ~500 1/s (juvenile fish) https://doi.org/10.1577/02-021",
 3: "Marine & Freshwater Research 70 (2019) larval fish shear: protect most larvae if strain <600 1/s, <400 1/s for early Murray cod larvae (via search abstract; MF18116 https://publish.csiro.au/MF/MF18116)",
 4: "Kinoshita, Fukuoka, Narazaki, Niizuma & Sato (2021) J Exp Biol 224 jeb236216 'Analysis of why sea turtles swim slowly': measured cruising 0.27-0.50 m/s (15 loggerhead, 9 green) https://cob.silverchair.com/jeb/article-pdf/1817605/jeb236216.pdf",
 5: "Juvenile hawksbill satellite tracking, Gulf of Thailand (Kyoto Univ. SEASTAR2000 proceedings): 0.45-0.57 km/h = 0.125-0.16 m/s net https://repository.kulib.kyoto-u.ac.jp/dspace/handle/2433/44178",
 6: "Sirenian movement review (Movement Behavior of Manatees and Dugongs II, JCU): cruising ~2-4 km/h (0.6-1.1 m/s), sprint to ~30 km/h https://portfolio.jcu.edu.au/publications/JCU178608",
 7: "USBR Red Bluff Research Pumping Plant & Tracy Series vol 25 (Archimedes lift 3.05 m, 26.5 rpm, trout 98-100% survival; Hidrostal 96 h 88-94%) via 15_jazr_gate_precedents.md",
 8: "Guy-Haim et al. 2020 Biogeosciences 17:5489 Rhopilema nomadica carcass decomposition: DO 261 umol/L to zero in 40 h at 27-28 C https://bg.copernicus.org/articles/17/5489/2020/",
 9: "Stomolophus meleagris (rhizostome) respiration: 0.05 mL O2/h/g WW active at 30 C, inactive 50% less (search record); Purcell et al. 2010 Hydrobiologia: temperature 7-30 C not significant, +/-72% error https://doi.org/10.1007/s10750-010-0240-9",
 10: "Vaquer-Sunyer & Duarte 2008 PNAS 105:15452 thresholds of hypoxia: mean sublethal 2.61 mg/L, lethal 2.05 mg/L (as reported by later review) https://pmc.ncbi.nlm.nih.gov/articles/PMC2556360",
 11: "Cassiopea xamachana thermal tolerance, Frontiers Mar Sci 2020 7:93: medusae stressed by 39 C, lethal ~40 C; polyps/larvae ~100% mortality at 36 C https://www.frontiersin.org/articles/10.3389/fmars.2020.00093",
 12: "Aravind, Henderson & Hamza 2023 COSE: C. mosaicus UAE 20-35 C, year-round, Abu Dhabi blooms Oct-Nov https://doi.org/10.53256/COSE_230102",
 13: "Keesing et al. 2016 Hydrobiologia (Crambione mastigophora, Catostylidae): 14,172 t stranded on 15 km Cable Beach; >90% of strandings 2 d after onshore winds https://pure.ecnu.edu.cn/en/publications/role-of-winds-and-tides-in-timing-of-beach-strandings-occurrence-/",
 14: "UVM Sea Grant TIP3 'Use of booms in oil pollution response': escape velocity ~0.35 m/s (0.7 kn) irrespective of skirt depth https://uvm.edu/seagrant/sites/default/files/uploads/TIP3UseofBoomsinOilPollutionResponse.pdf",
 15: "Public bubble-curtain study (context only): open 2 m skirt keeps 0-55% at 0.2 m/s; closed bag 84-100% (model) ",
 16: "US EPA 316(b) 2014 existing-facility rule: impingement BTA option max through-screen velocity 0.5 ft/s (0.15 m/s) https://www.sargentlundy.com/?p=10260",
 17: "Turtle detection: YOLOv7 green turtle (drone) precision 0.848 recall 0.853, submerged turtles poorly counted (Ecological Informatics 2025) https://doaj.org/article/1261f064f75d443aaa3c073f9a950951 ; underwater tiny-YOLOv4 P 0.80 R 0.83 (ASU poster) https://sensip.engineering.asu.edu/wp-content/uploads/2021/06/Elevator-Pitches-MASTER_removed-2-2.pdf",
 18: "NMFS shrimp-trawl tow-time limits 55 min (Apr-Oct) / 75 min (Nov-Mar) as TED alternative (Federal Register 1998) https://www.govinfo.gov/content/pkg/FR-1998-10-14/html/98-27408.htm ; green turtles failed to tolerate 2 h forced submergence (Schwartz, URI dissertation) https://digitalcommons.uri.edu/oa_diss/1794",
 19: "Indo-Pacific humpback dolphin Xiamen Bay 2025: mean dive 20.4 s (n=4408) https://natureconservation.pensoft.net/article_preview.php?id=162175",
 20: "14_global_solutions_deployed.md / 13_global_incidents.md: Hanbit gate crew 7-8 -> 20; Paiton 15 staff + fishers 24/7; Gravelines 3 -> 7 boats 24/7; Kori 24 h contractor crews; Shin Hanul 202 t/day",
 21: "St. Lucie NPP: 2018 497 turtles removed from canal, 95.4% alive; jellyfish/algae loading raised net velocity and risked pinning turtles (NRC docs, via 15_ file)",
 22: "Raskoff et al. 2003 (Monterey Bay Aquarium) gelatinous husbandry: wide-bore siphons, avoid air bubbles (tissue embolism) (via 15_ file)",
 23: "AZA Jellyfish Care Manual: stressed jellies release gametes; planulae found in transport water https://assets.speakcdn.com/assets/2332/aza_jellyfish_care_manual.pdf (via agent_enec_science.md)",
 24: "Higashi-Niigata thermal plant: live jellyfish pumped into net-cage tanks decay in ~5 days; ammonia/COD needed control (14_ file, JP5859541B2)",
}


def save(name, obj):
    p = os.path.join(RES, name)
    with open(p, "w") as f:
        json.dump(obj, f, indent=2, default=float)
    return p


def do_sat_mg_L(T, S):
    """Garcia & Gordon (1992) O2 solubility (Benson-Krause fit), umol/kg -> mg/L."""
    Ts = math.log((298.15 - T) / (273.15 + T))
    A = [5.80871, 3.20291, 4.17887, 5.10006, -9.86643e-2, 3.80369]
    B = [-7.01577e-3, -7.70028e-3, -1.13864e-2, -9.51519e-3]
    C0 = -2.75915e-7
    lnC = (A[0] + A[1]*Ts + A[2]*Ts**2 + A[3]*Ts**3 + A[4]*Ts**4 + A[5]*Ts**5
           + S*(B[0] + B[1]*Ts + B[2]*Ts**2 + B[3]*Ts**3) + C0*S**2)
    umol_kg = math.exp(lnC)
    return umol_kg * 1e-6 * 32.0 * 1e3 * RHO / 1000.0  # mg/L
