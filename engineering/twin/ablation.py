"""Layer-by-layer ablation + sensitivity for the JAZR stack (reduced-order twin; relative comparison only).
Each configuration: N = 3000 particles, averaged over 4 tide phases at alert time x 2 random seeds."""
import numpy as np, json, os, itertools
from multiprocessing import Pool
import jazr_twin as J
PH = (0, np.pi/2, np.pi, 3*np.pi/2); SEEDS = (1, 2)
STACK = [
 ("S0 Today (no system)",                         dict(system=False)),
 ("S1 Residual Guard only (L6)",                  dict(system=True, ring=False, policy="immediate")),
 ("S2 Arms + Lane, no guard (L2+L3)",             dict(system=True, eta_r=0.0, policy="immediate")),
 ("S3 + Residual Guard (L6)",                     dict(system=True, policy="immediate")),
 ("S4 + Ebb Window timing (L1+L4)",               dict(system=True, policy="ebb", window=0.25)),
 ("S5 + Lane extended to 1.2 km (L3)",            dict(system=True, policy="ebb", window=0.25, gate_x=1200)),
 ("S6 + Ratchet vane field (L2b, alpha 0.07)",    dict(system=True, policy="ebb", window=0.25, gate_x=1200, ratchet=0.07)),
 ("S7 + Express export 3 km on red days (L5)",    dict(system=True, policy="ebb", window=0.25, gate_x=1200, gate_y=3000, ratchet=0.07)),
]
def one(args):
    kw, ph, sd = args
    r = J.simulate(N=3000, phase0=ph, seed=sd, **kw)[0]
    return r
def avg(kw):
    with Pool() as p:
        rs = p.map(one, [(kw, ph, sd) for ph in PH for sd in SEEDS])
    c = [r["captured_frac"] for r in rs]
    return dict(captured=float(np.mean(c)), lo=float(min(c)), hi=float(max(c)),
                handlings=float(np.mean([r["mean_handlings"] for r in rs])),
                peak_held_t=float(np.mean([r["peak_held_tonnes"] for r in rs])),
                far=float(np.mean([r["far_frac"] for r in rs])),
                swarm_t=rs[0]["swarm_tonnes"])
if __name__ == "__main__":
    OUT = J.OUT; R = {"stack": {}, "sens": {}}
    for swim in (0.036, 0.10):
        for name, kw in STACK:
            a = avg(dict(kw, swim=swim)); R["stack"][f"{name}|swim={swim}"] = a
            print(f"{name:45s} swim {swim:.3f}: intake {a['captured']*100:5.1f}% [{a['lo']*100:.0f}-{a['hi']*100:.0f}]  handled {a['handlings']:.2f}x  >2km {a['far']*100:4.1f}%  peak held {a['peak_held_t']:6.0f} t", flush=True)
    full = dict(STACK[-1][1])
    for lab, kw in [("eta_g=0.5", dict(eta_g=0.5)), ("eta_g=0.9", dict(eta_g=0.9)),
                    ("eta_r=0.5", dict(eta_r=0.5)), ("residual 1 cm/s onshore", dict(vr=-0.01)),
                    ("residual 2 cm/s alongshore", dict(ur=0.02)), ("ratchet alpha 0", dict(ratchet=0.0)),
                    ("ratchet alpha 0.15", dict(ratchet=0.15)), ("window 0.5", dict(window=0.5)),
                    ("S5 eta_g=0.5", dict(STACK[5][1], eta_g=0.5)), ("S5 eta_g=0.9", dict(STACK[5][1], eta_g=0.9))]:
        base = dict(full) if not lab.startswith("S5") else {}
        base.update(kw); a = avg(base); R["sens"][lab] = a
        print(f"SENS {lab:28s}: intake {a['captured']*100:5.1f}%  handled {a['handlings']:.2f}x  peak held {a['peak_held_t']:6.0f} t", flush=True)
    json.dump(R, open(os.path.join(OUT, "ablation.json"), "w"), indent=1)
