"""T5 - FMEA (S/O/D/RPN), two fault trees, and common-mode (beta-factor) analysis across 4 units.

Ratings are ENGINEERING JUDGEMENT on a 1-10 scale (AIAG-style): S severity, O occurrence per bloom season,
D detection (10 = cannot detect before effect). Basic-event probabilities in the fault trees are [ASSUME]
placeholders to be replaced by pilot data; the structure and the ranking are the deliverable.
"""
import csv
from params import *

F = [
# component, failure mode, effect, cause, S, O, D, current control, recommended action
("Gantry/piles", "Structural failure / collapse", "Debris into intake lane; possible UHS blockage", "Seismic, storm, ship impact", 10, 1, 3, "Seismic II/I design", "Seismic II/I + debris-load case; inspection each season"),
("Drum + motor", "Fails to roll DOWN on deploy", "Gap in screen -> leakage of that bay", "Motor/brake/VFD fault, cold-start", 4, 4, 2, "Load-cell/encoder status", "Pre-season test run; spare drive; accept 1-bay gap"),
("Drum + motor", "Fails to roll UP on high dP", "Bay blinds; local velocity rises; turtle pinning; loads on gantry", "Motor/brake fault, jam by fouling", 8, 3, 3, "Load cell alarm", "Gravity/shear-pin release of bottom bar independent of motor (fail-open)"),
("Drum + motor", "Uncommanded roll-up", "Pulse of impinged bells to plant screens", "Spurious trip, PLC fault", 6, 3, 2, "<1 t staged pulse", "2oo3 voting (2 load cells + lane dP)"),
("Mesh", "Tear / hole", "Leakage; mesh fragments to plant screens", "Abrasion, debris, overload", 6, 4, 5, "Visual on roll-up", "Camera inspection on each roll cycle; mesh strength > blinding load"),
("Mesh", "Animal entanglement (turtle flipper, fish)", "Wildlife injury/death", "Mesh opening ~ limb size", 9, 2, 6, "None", "Specify knotless rigid mesh, opening <= 25 mm or >= limb-free; underwater camera per 3 bays"),
("Bottom bar / floor rail", "Bar does not seat (sediment, fouling)", "Under-gap leakage of bells (retention loss)", "Sand in rail, barnacles", 5, 5, 6, "None", "Rail jetting before deploy; seat sensor; T8 test"),
("Load cell", "Drift / failed low", "Blinding not detected -> FATAL3-type over-load", "Seawater ingress, drift", 8, 3, 6, "Single cell", "2 cells per drum + lane dP cross-check; weekly zero check"),
("Load cell", "Failed high (spurious)", "Nuisance roll-up, pulse", "Electrical fault, wave transient", 5, 4, 3, "Filter", "Time filter + voting"),
("Brush/spray cleaner", "Brush fails", "Faster blinding; more roll-ups", "Wear", 4, 4, 4, "Cycle count", "Spare brush cassette"),
("Brush/drum", "Bell wound into drum", "Bell crushed; tissue smear fouls mesh", "Roll-up while bells on face", 4, 6, 5, "None", "Interlock: pre-sweep pause before roll-up"),
("Bypass entrance", "Blocked by bell pile", "Bypass loses flow; bells accumulate on face", "Density > design", 7, 5, 4, "Camera counts", "Entrance >= 1.0 m; flow sensor per entrance; add lines"),
("Camera diverter", "Camera misses turtle (turbidity/night/occlusion)", "Turtle enters screw/pipe -> death", "Visibility, model recall ~0.85", 10, 4, 9, "Single camera", "2 independent sensors (optical + imaging sonar) + physical deformable-pass grid + push door"),
("Camera diverter", "Diverter gate fails to move", "Turtle not diverted", "Actuator jam, fouling", 10, 2, 5, "Position switch", "Fail-to-divert position default; proof test per shift"),
("Camera diverter", "False positives (bells as turtles)", "Screw stops repeatedly -> bypass backs up", "Low precision", 5, 6, 2, "Operator review", "Precision target >= 0.9 at recall 0.999; auto-restart"),
("Archimedes screw", "Stops / bearing failure", "Lift lost -> bells accumulate -> roll-ups -> leakage", "Bearing, gearbox, motor", 7, 3, 2, "Motor current", "N+1 screws per unit"),
("Archimedes screw", "Leading-edge damage to bells/fish", "Mortality, fragments", "Blade strike", 5, 7, 7, "None", "Rubber/rounded leading edge; low rpm; tank test"),
("Head tank", "Overflow", "Animals spilled on deck; DO loss", "Pump trip", 4, 3, 2, "Level switch", "Overflow weir back to channel"),
("Pump", "Impeller damage to bells/fish", "Mortality", "Passage < bell size", 6, 6, 7, "None", "Delete pump: gravity head tank (2 screws in series)"),
("Pump", "Trip", "Line stops; head tank floods", "Electrical", 5, 3, 2, "Status", "Duty/standby"),
("5 km pipe", "Plug (bell slurry / bend)", "Lift line out for hours-days", "Solids > 4% vol, low velocity", 6, 4, 4, "dP along line", "Keep solids <2%; pig launcher; backflush"),
("5 km pipe", "Low DO in line", "Animals and fish die in transit -> dead release", "High biomass", 7, 5, 6, "None", "DO sensor at outlet; O2 injection; split lines"),
("5 km pipe", "Air at breakwater high point", "Bubbles under bells (embolism)", "HGL below crest", 5, 4, 6, "None", "Route through breakwater or head tank >= crest + 2 m"),
("5 km pipe", "Anchor/ship damage, leak", "Release near shore", "Shipping, anchoring", 6, 2, 4, "Charted zone", "Burial/armour; pressure monitoring"),
("Outlets", "Wrong outlet chosen (forecast error)", "Drift-back, stranding, hits MPA/intake", "Wind not forecast", 6, 5, 6, "72 h forecast", "Ensemble forecast with wind; drifters; beach survey"),
("Outlets", "Dead biomass released", "Benthic hypoxia, odour", "Transit mortality", 7, 4, 6, "None", "Damage scoring camera at head tank -> auto recover mode"),
("Recover mode", "Dewatering/compost capacity exceeded", "Biomass backlog; must stop lift", "Design density", 6, 4, 3, "Storage level", "Size for pilot worst day; contract haulage"),
("Bloom Incident OS", "Software fault / wrong state", "Not deployed or wrong roll-up across all units", "Bug, update", 8, 3, 4, "Human approval", "Per-unit independent PLC; manual local panel; diverse software"),
("Bloom Incident OS", "Late/absent alert", "Not deployed before arrival", "Forecast miss (Gravelines)", 8, 4, 7, "Alert lead 4-6 h", "Auto Ready on camera/sonar counts; deploy in 10 min"),
("Operators", "Approval delayed (night, workload)", "Late deployment", "Human factors", 6, 4, 3, "Drills", "Pre-authorised deploy on red alert"),
("Power supply", "Loss of site AC to JAZR", "Bays freeze in position; screws stop", "Grid/house load shedding", 8, 2, 2, "None", "Fail-open by gravity on loss of power; UPS for PLC/cameras"),
("Training wall", "Scour / settlement", "Lane geometry and sweep change", "Currents", 5, 2, 5, "Survey", "Bathymetric survey each season"),
]
rows = []
for c, m, e, cause, S, O, D, ctl, act in F:
    rows.append(dict(component=c, failure_mode=m, effect=e, cause=cause, S=S, O=O, D=D, RPN=S*O*D, control=ctl, action=act))
rows.sort(key=lambda r: -r["RPN"])
with open(os.path.join(RES, "t5_fmea.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
with open(os.path.join(RES, "t5_fmea.md"), "w") as f:
    f.write("| # | Component | Failure mode | Effect | S | O | D | RPN | Recommended action |\n|---|---|---|---|---|---|---|---|---|\n")
    for i, r in enumerate(rows, 1):
        f.write(f"| {i} | {r['component']} | {r['failure_mode']} | {r['effect']} | {r['S']} | {r['O']} | {r['D']} | **{r['RPN']}** | {r['action']} |\n")

# ---------------- Fault trees (per unit, per bloom event) ----------------
def OR(*p):
    q = 1.0
    for x in p: q *= (1 - x)
    return 1 - q
def AND(*p):
    q = 1.0
    for x in p: q *= x
    return q

B = dict(  # basic events [ASSUME]
    alert_late=0.15,           # alert arrives < deploy time (Gravelines saw "tens of kg" the day before)
    deploy_fail=0.02,          # OS/drive failure prevents deployment
    density_over_design=0.20,  # bloom exceeds 0.3/m3 locally
    blinding_given_over=0.5,
    lift_fail=0.03,            # screw/pump/pipe out during bloom with no N+1
    relief_pulse_large=0.3,    # roll-ups during lift loss release > plant screen capacity
    plant_screen_fail_given_load=0.3,  # plant screens fail when they see today's load (Hanul, Ohi)
    leakage_load_over_capacity=0.1,    # residual leakage alone over plant screen capacity
    structure_debris=0.001,
)
# Top 1: intake blockage despite JAZR
not_deployed = OR(B["alert_late"], B["deploy_fail"])
overwhelmed = AND(B["density_over_design"], B["blinding_given_over"], B["relief_pulse_large"])
lift_loss = AND(B["lift_fail"], B["relief_pulse_large"])
leak = B["leakage_load_over_capacity"]
top1 = OR(AND(not_deployed, B["plant_screen_fail_given_load"]),
          AND(OR(overwhelmed, lift_loss, leak), B["plant_screen_fail_given_load"]),
          B["structure_debris"])
contrib1 = {"not deployed in time": AND(not_deployed, B["plant_screen_fail_given_load"]),
            "overwhelmed (density>design, blinding, pulse)": AND(overwhelmed, B["plant_screen_fail_given_load"]),
            "lift loss -> pulse": AND(lift_loss, B["plant_screen_fail_given_load"]),
            "residual leakage over capacity": AND(leak, B["plant_screen_fail_given_load"]),
            "structure debris": B["structure_debris"]}
baseline_today = B["plant_screen_fail_given_load"]

# Top 2: wildlife harm (per bloom event, per unit)
W = dict(turtle_at_bypass=0.5,   # at least one turtle reaches a bypass mouth during a bloom [ASSUME]
         cam_miss=0.15, door_fail=0.3, divert_fail=0.01, stop_fail=0.01,
         pinning=AND(0.3, 0.05),  # local blinding hotspot AND turtle present/exhausted
         entangle=0.01, dead_release_hypoxia=0.05, stranding_event=0.1, dolphin_in_lane=0.02)
turtle_screw = AND(W["turtle_at_bypass"], OR(AND(W["cam_miss"], W["door_fail"]), AND(1 - W["cam_miss"], W["divert_fail"], W["stop_fail"])))
top2 = OR(turtle_screw, W["pinning"], W["entangle"], W["dead_release_hypoxia"], W["stranding_event"], W["dolphin_in_lane"])
contrib2 = {"turtle into screw/pipe": turtle_screw, "turtle pinned on blinded bay": W["pinning"], "mesh entanglement": W["entangle"],
            "dead-release hypoxia": W["dead_release_hypoxia"], "mass stranding from outlet": W["stranding_event"], "dolphin/dugong in lane": W["dolphin_in_lane"]}

# ---------------- Common mode across 4 units (beta-factor, IEC 61508-6 style) ----------------
cm = {}
for name, p_unit, beta, why in (
    ("OS/PLC software fault", 0.02, 0.5, "same software in all units unless diverse"),
    ("late alert", 0.15, 1.0, "one forecast serves the site: fully common"),
    ("bloom over design density", 0.2, 0.9, "same water mass"),
    ("site power loss to JAZR", 0.01, 0.8, "shared supply"),
    ("drum drive failure", 0.05, 0.05, "independent hardware, typical beta 1-10%"),
    ("camera misses (turbidity/night)", 0.15, 0.6, "same water clarity at all units"),
):
    p4_indep = p_unit**4
    p4_cm = beta*p_unit + (1-beta)*p_unit**4 if beta < 1 else p_unit
    cm[name] = dict(p_unit=p_unit, beta=beta, P_all4_if_independent=p4_indep, P_all4_with_CCF=p4_cm, ratio=p4_cm/p4_indep, note=why)

res = dict(fmea_top10=[(r["component"], r["failure_mode"], r["RPN"]) for r in rows[:10]],
           fault_tree_intake=dict(basic=B, P_top=top1, contributions=contrib1, baseline_today_P=baseline_today),
           fault_tree_wildlife=dict(basic=W, P_top=top2, contributions=contrib2),
           common_mode=cm)
res["verdicts"] = {
  "T5a_FMEA": ("MARGINAL", "%d modes; %d with RPN>=200; top: %s" % (len(rows), sum(r['RPN'] >= 200 for r in rows), "; ".join(f"{a}/{b} ({c})" for a, b, c in res['fmea_top10'][:4]))),
  "T5b_FTA_intake": ("PASS (conditional)", "P(blockage | bloom) %.3f vs today %.2f -> %.0f%% reduction; dominated by 'not deployed in time' (%.3f): alert lead and auto-Ready matter more than screen hardware" % (top1, baseline_today, (1-top1/baseline_today)*100, contrib1['not deployed in time'])),
  "T5c_FTA_wildlife": ("FAIL", "P(any wildlife harm | bloom, unit) %.3f; biggest terms stranding %.3f, dead-release %.3f, turtle-into-screw %.4f -- all [ASSUME] but no target <0.01 is met" % (top2, contrib2['mass stranding from outlet'], contrib2['dead-release hypoxia'], turtle_screw)),
  "T5d_common_mode": ("FAIL vs claim", "v3 says 'no common-mode failure across units'; alert, bloom density, water clarity, power and software are common (beta 0.5-1.0) -> P(all 4 affected) is ~10^2-10^5 x the independent value. Re-word and add diverse local control"),
}
save("t5_fmea_fta.json", res)
if __name__ == "__main__":
    for r in rows[:12]:
        print(r["RPN"], r["component"], "|", r["failure_mode"])
    print("top1", top1, contrib1); print("top2", top2, contrib2)
    for k, d in cm.items(): print(k, "%.2e %.2e x%.0f" % (d['P_all4_if_independent'], d['P_all4_with_CCF'], d['ratio']))
    for k, (v, w) in res["verdicts"].items(): print(k, v, w)
