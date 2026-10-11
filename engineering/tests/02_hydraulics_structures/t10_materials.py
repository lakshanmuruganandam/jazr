"""T10 - Materials, corrosion and fouling at 35.8 C max, 38-48 PSU, Arabian Gulf.

Checks:
 * PREN = %Cr + 3.3 %Mo + 16 %N (nominal mid compositions, standard grades).
   Criterion: PREN >= 40 for seawater-wetted stainless (industry rule of thumb, e.g. NORSOK M-001;
   standard reference, not web-verified tonight).
 * Crevice margin: CCT(natural seawater) - T_max. SAF 2507 CCT 64 C in natural seawater at +150 mV SCE
   (Alleima datasheet https://www.alleima.com/en/technical-center/material-datasheets/tube-and-pipe-seamless/saf-2507/ ).
   6Mo+N 61 C (same source). 2205: no seawater CCT number found tonight (L.J. Star note: "used successfully in
   seawater where kept free of deposits" https://www.ljstar.com/wp-content/uploads/2019/11/duplex-2205-over-316L.pdf).
   Criterion: CCT >= T_max + 15 K PASS (ASSUMED margin for chlorination/biofilm ennoblement).
 * PE100 at 35.8 C: ISO 13761:2017 pressure reduction applies above 20 C (factor table not retrieved;
   https://www.pe100plus.com/PE-Pipes/Technical-guidance/model/Design/Lifetime/factors-i243.html ).
 * the plant condenser already uses titanium + stainless tubes (WNN, 05_fact_check #28).
"""
import os, csv
from common import *

T = "T10"
Tmax = SITE["T_water"][1]
grades = {  # nominal mid compositions (wt %), standard grade data
    "316L": (17.0, 2.1, 0.05, None),
    "2205 duplex (S32205)": (22.5, 3.1, 0.17, None),
    "2507 super duplex (S32750)": (25.0, 4.0, 0.28, 64.0),
    "6Mo (S31254 / 6Mo+N)": (20.0, 6.1, 0.20, 61.0),
}
rows = []
for gname, (cr, mo, n, cct) in grades.items():
    pren = cr + 3.3 * mo + 16 * n
    rows.append(dict(material=gname, PREN=round(pren, 1), CCT_seawater_C=cct))
    record(T, f"PREN {gname}", pren, "-", ">= 40 seawater rule of thumb (NORSOK M-001 style)", "composition",
           verdict(pren, lambda v: v >= 40, lambda v: v >= 34))
    if cct:
        record(T, f"crevice margin CCT - T_max ({gname})", cct - Tmax, "K", ">= 15 K PASS; >= 5 K MARGINAL (ASSUMED)",
               "Alleima SAF 2507 datasheet", verdict(cct - Tmax, lambda v: v >= 15, lambda v: v >= 5))
    else:
        record(T, f"crevice margin ({gname})", "no data", "", "CCT >= T_max + 15 K", "not found tonight",
               "FAIL" if pren < 30 else "MARGINAL",
               "316L pits/crevices in warm Gulf seawater; 2205 only for free-draining, flow-cleaned, non-crevice parts")

# qualitative/standard selections (recorded as design decisions with stated basis)
sel = [
    ("Guide rails, bottom-bar seat, drum shafts (permanently wetted crevices)", "2507 super duplex or titanium Gr2; GRP/UHMWPE liner in rail slots",
     "crevice at 35.8 C needs CCT margin; 2205 marginal", "PASS"),
    ("Curtain mesh", "2205/2507 woven wire OR UHMWPE net; 90/10 CuNi only if electrically isolated from SS/CP",
     "CuNi antifouling works only while freely corroding; galvanically coupled to SS or CP it loses Cu-ion release; stored dry 10 months so antifouling value is limited", "MARGINAL"),
    ("Piles / gantry steel", "S355 with coating + sacrificial-anode CP + corrosion allowance in splash zone",
     "standard marine practice; splash zone is the critical zone (allowance to be set from local data, not available)", "PASS"),
    ("Export pipe", "PE100 SDR17 (not SDR26: vacuum/collapse, T08), carbon-black UV-stabilised for breakwater crossing",
     "PE100 rated to 40 C with ISO 13761 de-rating", "PASS"),
    ("Archimedes screw / head tank", "2205 or coated carbon steel with CP; rotating tube in 2205; bearings water-lubricated, non-metallic",
     "free-draining between seasons; inspectable", "PASS"),
    ("Fasteners in mesh/rails", "2507 or titanium; never 316/A4 in submerged crevices", "316 crevice corrodes in warm seawater", "PASS"),
]
for part, choice, basis, v in sel:
    record(T, f"material selection: {part}", choice, "", "fit for 35.8 C / 48 PSU, 60-yr plant life (with replacement)",
           "see module docstring", v, basis)
# fouling exposure while deployed
for days in (30, 90):
    record(T, f"fouling exposure of curtain per season ({days} d deployed)", days, "days",
           "<= 60 d before first clean (ASSUMED: barnacle/mussel settlement within weeks at 30+ C, audit #16)",
           "16_FLAW_AUDIT #16", verdict(days, lambda v: v <= 60, lambda v: v <= 90),
           "brush pass at each roll-up keeps mesh clean; rails/slots need a pre-season brush pig")
with open(os.path.join(OUT, "T10_materials.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
save(T, dict(rows=rows))
