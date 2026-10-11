"""
10_mechanisms -- quick virtual-tank screening of guidance mechanisms.
*** SIMULATED virtual tank - not physical evidence. ***

Re-uses ../07_virtual_tank/vtank.py unchanged and adds ONE new physics option:
a travelling/conveyor screen whose surface moves ALONG the face toward the apex
entrance at speed v_belt (Bates 1970 "horizontal traveling screen" concept).
Bell-mesh Coulomb friction then acts on the bell's velocity RELATIVE to the belt,
so a pinned bell is carried to the apex instead of stalling.

Also scans: low-friction coating (mu_f), agitation (turb_I as a crude proxy for
wall jets / Coanda sweep), bypass fraction, number of entrances, bell size.

Usage: python3 mech_vtank.py  -> ../results/sim_mechanisms.csv + .json
"""
import os, sys, json, time, inspect, textwrap, csv
import numpy as np
from dataclasses import replace
import multiprocessing as _mp

HERE = os.path.dirname(os.path.abspath(__file__))
VT = os.path.abspath(os.path.join(HERE, "..", "..", "07_virtual_tank"))
sys.path.insert(0, VT)
import vtank  # noqa: E402
from vtank import Params, Sim  # noqa: E402

OUT = os.path.abspath(os.path.join(HERE, "..", "results"))
os.makedirs(OUT, exist_ok=True)

# ---- build a belt-aware copy of Sim._seg_contact by patching ONE line --------------
_src = textwrap.dedent(inspect.getsource(Sim._seg_contact))
_old = "vt_new = np.sign(vt) * np.maximum(np.abs(vt) - cap, 0)"
assert _old in _src, "vtank._seg_contact changed; patch point not found"
_ind = [l for l in _src.splitlines() if _old in l][0].split("v")[0]
_new = ("vb = getattr(self, 'v_belt', 0.0) if sg.kind == 'screen' else 0.0\n"
        + _ind + "vbt = tng @ (vb * sg.t)\n"
        + _ind + "vrel = vt - vbt\n"
        + _ind + "vt_new = vbt + np.sign(vrel) * np.maximum(np.abs(vrel) - cap, 0)")
_src = _src.replace(_old, _new)
_ns = {}
exec(compile(_src, "<belt_patch>", "exec"), vtank.__dict__, _ns)


class BeltSim(Sim):
    """Sim with the screen surface travelling toward the apex at v_belt (m/s, tank scale)."""
    def __init__(self, P, seed=0, v_belt=0.0, **kw):
        super().__init__(P, seed, **kw)
        self.v_belt = float(v_belt)

BeltSim._seg_contact = _ns["_seg_contact"]

NOM = Params()
SWEEP = NOM.U * np.cos(np.radians(NOM.theta_deg))   # ~0.108 m/s tank (0.48 m/s prototype)
N_BELLS, T_RUN, SEEDS = 30, 150.0, 4


def job(a):
    P = replace(NOM, **a.get("kw", {}))
    s = BeltSim(P, a["seed"], v_belt=a.get("belt", 0.0) * SWEEP)
    s.release_bells(N_BELLS, d_range=a.get("d", (0.04, 0.06)))
    t0 = time.time()
    s.run(T_RUN)
    r = s.summary()
    return dict(tag=a["tag"], seed=a["seed"], eta_r=r["bypass"] / N_BELLS, stuck=r["stuck"] / N_BELLS,
                intake=r["intake"] / N_BELLS, under=r["under"], over=r["over"], cpu=round(time.time() - t0, 1))


CASES = [
    # tag, kwargs, belt (x sweep), bell diameter range (tank m)
    ("A0 baseline 10% bypass, 2 entr, 4-6 cm bells", {}, 0.0, (0.04, 0.06)),
    ("A1 belt 0.5x sweep", {}, 0.5, (0.04, 0.06)),
    ("A2 belt 1.0x sweep", {}, 1.0, (0.04, 0.06)),
    ("A3 belt 1.2x sweep", {}, 1.2, (0.04, 0.06)),
    ("A4 belt 0.25x sweep", {}, 0.25, (0.04, 0.06)),
    ("A5 belt 1.0x, sticky: mu 1.0 + adhesion 3 Pa", dict(mu_f=1.0, adhesion=3.0), 1.0, (0.04, 0.06)),
    ("A6 belt 1.0x, bypass only 3%", dict(bypass_frac=0.03), 1.0, (0.04, 0.06)),
    ("A7 belt 1.0x, 15 deg", dict(theta_deg=15), 1.0, (0.04, 0.06)),
    ("B0 coating mu 0.1", dict(mu_f=0.1), 0.0, (0.04, 0.06)),
    ("B1 coating mu 0.05", dict(mu_f=0.05), 0.0, (0.04, 0.06)),
    ("C1 agitation turb 25% (jet proxy)", dict(turb_I=0.25), 0.0, (0.04, 0.06)),
    ("D0 v4: 4 entr, 20% bypass", dict(n_mid_slots=3, bypass_frac=0.20), 0.0, (0.04, 0.06)),
    ("D1 v4 + belt 1.0x", dict(n_mid_slots=3, bypass_frac=0.20), 1.0, (0.04, 0.06)),
    ("D2 v4 + belt 1.0x + 10 cm apex mouth", dict(n_mid_slots=3, bypass_frac=0.20, gap_w=0.10), 1.0, (0.04, 0.06)),
    ("D3 v4 + coating mu 0.05", dict(n_mid_slots=3, bypass_frac=0.20, mu_f=0.05), 0.0, (0.04, 0.06)),
    ("E0 scaled bells 1.5-2.5 cm, v4", dict(n_mid_slots=3, bypass_frac=0.20), 0.0, (0.015, 0.025)),
    ("E1 scaled bells, v4 + belt 1.0x", dict(n_mid_slots=3, bypass_frac=0.20), 1.0, (0.015, 0.025)),
    ("E2 scaled bells, 10% + belt 1.0x", {}, 1.0, (0.015, 0.025)),
]


def main():
    jobs = [dict(tag=t, kw=kw, belt=b, d=d, seed=41000 + s) for (t, kw, b, d) in CASES for s in range(SEEDS)]
    with _mp.get_context("fork").Pool(min(8, len(jobs))) as p:
        res = p.map(job, jobs)
    rows, summ = [], {}
    for t, *_ in CASES:
        rr = [r for r in res if r["tag"] == t]
        e = np.array([r["eta_r"] for r in rr]); st = np.array([r["stuck"] for r in rr]); it = np.array([r["intake"] for r in rr])
        summ[t] = dict(eta_mean=round(float(e.mean()), 3), eta_se=round(float(e.std(ddof=1) / np.sqrt(len(e))), 3),
                       stuck_mean=round(float(st.mean()), 3), intake_mean=round(float(it.mean()), 3), n_seeds=len(e))
        rows += rr
    with open(os.path.join(OUT, "sim_mechanisms_runs.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()) + ["data_type"])
        w.writeheader()
        for r in rows:
            w.writerow({**r, "data_type": "SIMULATED"})
    json.dump(dict(label=vtank.LABEL, T_run_s=T_RUN, n_bells=N_BELLS, seeds=SEEDS,
                   sweep_tank_m_s=round(float(SWEEP), 4), summary=summ),
              open(os.path.join(OUT, "sim_mechanisms.json"), "w"), indent=1)
    for t, v in summ.items():
        print(f"{t:48s} eta={v['eta_mean']:.2f}±{v['eta_se']:.2f} stuck={v['stuck_mean']:.2f} intake={v['intake_mean']:.2f}")


if __name__ == "__main__":
    main()
