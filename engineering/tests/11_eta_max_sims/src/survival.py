"""
survival.py - end-to-end SURVIVAL CHAIN Monte Carlo for guided Blue Blubber jellyfish (Catostylus sp.).
*** MODEL-BASED. Stage ranges are literature ANALOGUES or ASSUMPTIONS (labelled). No scyphomedusa has ever been
tested through a screw, pump or km-scale pipe (09_biology_behaviour R20; 04 T3). ***

Stages: screen contact -> entrance -> dewatering -> excluder grid -> lift [screw | fish lock | vacuum pump]
        -> pipe 3 h [with dissolved O2 | without] -> outlet.
Screen stage is linked to the simulations: S_screen = exp(-h_c * contacts - h_t * time_on_face), with contacts
and time-on-face sampled between the prototype tracker (lower) and the tank analogue (upper) for that option.
Swarm-level outcome = eta_r x chain survival (unguided bells go to the plant screens, where they die).
Writes results/survival_stages.csv, results/survival_chain.csv
"""
import os, csv
import numpy as np

RES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")
N = 200_000
rng = np.random.default_rng(11)

# (lo, hi, basis, source)  - uniform ranges
STAGES = {
    "screen_hazard_per_contact": (0.002, 0.02, "ASSUME", "AZA Jellyfish Care Manual: mesh abrades tissue (qualitative); no rate data"),
    "screen_hazard_per_s_on_face": (1e-4, 1e-3, "ASSUME", "pinned at 0.07-0.14 m/s through-velocity; no rate data"),
    "entrance": (0.95, 0.995, "ANALOGUE", "fish bypass entrances (EPRI 2006 / USBR); smooth accelerating mouth (09 R10/R11)"),
    "dewatering": (0.85, 0.99, "ANALOGUE", "wedge-wire dewatering for fish; sliding contact only (09 R07); jelly UNKNOWN"),
    "excluder_grid": (0.97, 1.0, "ASSUME", "15 cm bars, bells 6.5-12 cm pass without squeezing (00 data)"),
    "lift_screw": (0.90, 0.995, "ANALOGUE", "Red Bluff Archimedes screw trout 98-100% (USBR vol 25); gel surrogate 100% intact (07 T09)"),
    "lift_fish_lock": (0.95, 1.0, "ASSUME", "water-to-water, no moving contact; fill/drain time only"),
    "lift_vacuum_pump": (0.50, 0.95, "ANALOGUE+ASSUME", "vacuum fish pumps 95-99% for fish; pressure swing -> degassing bubbles under bells (09 R01/R02) lowers it"),
    "pipe_3h_O2": (0.85, 0.99, "ASSUME", "aquarium shipping 1->24 h survives if no air, DO 75-99% sat (09 R03/R06); wall contact at 1 m/s"),
    "pipe_3h_noO2_0.3m3": (0.40, 0.95, "DERIVED+ASSUME", "pipe biomass ~7.6 kg/m3 at 0.3 /m3 > 6.6 kg/m3 O2 limit (09 R04/R05); scyphozoans oxyregulate <10% sat but rhizostome Pc UNKNOWN"),
    "outlet": (0.95, 1.0, "ASSUME", "submerged gentle outlet, ambient T/S (09 R17)"),
}


def U(k, n=N):
    lo, hi = STAGES[k][:2]
    return rng.uniform(lo, hi, n)


def load(path, key_col="config"):
    d = {}
    if os.path.exists(path):
        for r in csv.DictReader(open(path)):
            d[r[key_col]] = r
    return d


def main():
    vt = load(os.path.join(RES, "vt_levers.csv")); pr = load(os.path.join(RES, "proto_levers.csv"))
    def screen_inputs(vt_cfg, pr_cfg):
        a, b = vt.get(vt_cfg), pr.get(pr_cfg)
        c = [float(x["contacts_per_bell"]) for x in (a, b) if x]
        t = [float(a["t_face_s_proto"])] if a else []
        t += [float(b["t_face_s"])] if b else []
        return (min(c), max(c)), (min(t), max(t)), (float(a["eta_mean"]) if a else np.nan, float(a["eta_cp_lo"]) if a else np.nan)
    opts = {"v4.1 screen": screen_inputs("v4.1 (4 entr, 20%, mu 0.4)", "v4.1 | nominal"),
            "best-combo screen": screen_inputs("+ mu 0.1 coating", "best | nominal")}
    rows, srows = [], []
    for k, (lo, hi, basis, src) in STAGES.items():
        srows.append(dict(stage=k, low=lo, high=hi, basis=basis, source=src))
    for so, ((c0, c1), (t0, t1), (eta, eta_lo)) in opts.items():
        srows.append(dict(stage=f"{so}: contacts per bell (sim)", low=c0, high=c1, basis="SIMULATED", source="vt_levers.csv / proto_levers.csv"))
        srows.append(dict(stage=f"{so}: time on face s, prototype (sim)", low=t0, high=t1, basis="SIMULATED", source="vt_levers.csv (x sqrt 20) / proto_levers.csv"))
        nc = rng.uniform(c0, c1, N); tf = rng.uniform(t0, t1, N)
        S_screen = np.exp(-U("screen_hazard_per_contact") * nc - U("screen_hazard_per_s_on_face") * tf)
        common = S_screen * U("entrance") * U("dewatering") * U("excluder_grid") * U("outlet")
        for lift in ("screw", "fish_lock", "vacuum_pump"):
            for pipe in ("O2", "noO2_0.3m3"):
                S = common * U(f"lift_{lift}") * U(f"pipe_3h_{pipe}")
                q = np.percentile(S, [5, 50, 95])
                sw = eta * S
                rows.append(dict(screen=so, lift=lift, pipe=pipe, chain_p05=round(q[0], 3), chain_median=round(q[1], 3),
                                 chain_p95=round(q[2], 3), screen_stage_median=round(float(np.median(S_screen)), 3),
                                 eta_r=round(eta, 4), swarm_released_alive_median=round(float(np.median(sw)), 3),
                                 swarm_p05=round(float(np.percentile(sw, 5)), 3), swarm_p95=round(float(np.percentile(sw, 95)), 3),
                                 data_type="MODEL-BASED Monte Carlo (literature analogues + assumptions)"))
                print(rows[-1])
    with open(os.path.join(RES, "survival_stages.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(srows[0].keys())); w.writeheader(); w.writerows(srows)
    with open(os.path.join(RES, "survival_chain.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)


if __name__ == "__main__":
    main()
