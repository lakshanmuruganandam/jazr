"""Shared helpers for the twin V&V suite. Imports the twin read-only (no edits to twin/)."""
import os, sys, json, contextlib
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
TWIN = os.path.abspath(os.path.join(HERE, "..", "..", "twin"))
sys.path.insert(0, TWIN)
import jazr_twin as J  # noqa: E402
OUT = os.path.join(HERE, "out"); FIGS = os.path.join(HERE, "figs")
os.makedirs(OUT, exist_ok=True); os.makedirs(FIGS, exist_ok=True)
PH = (0.0, np.pi/2, np.pi, 3*np.pi/2)

# The v3 configurations exactly as in twin/v3study.py
V3_BASE = dict(system=True, policy="immediate", ring=False, eta_r=0.9, gate_x=1200, gate_y=3000)
V3 = dict(V3_BASE, ring=True, eta_g=0.4, gate_y=5000)          # "Gate + outer guide (0.4) + outlet 5 km"
TODAY = dict(system=False)
CONDS = {"median": {}, "onshore 3 cm/s": dict(vr=-0.03), "10-day bloom": dict(hours=240), "guard 0.5": dict(eta_r=0.5)}
HEADLINE = {"median": 0.05483333333333333, "onshore 3 cm/s": 0.12233333333333334,
            "10-day bloom": 0.13279166666666667, "guard 0.5": 0.280625}   # from twin/out/v3study.json

@contextlib.contextmanager
def patched(**kw):
    """Temporarily override module-level constants of jazr_twin (U0, Q, BAND_X, ...)."""
    old = {k: getattr(J, k) for k in kw}
    for k, v in kw.items(): setattr(J, k, v)
    try: yield
    finally:
        for k, v in old.items(): setattr(J, k, v)

def run(args):
    """args = (kw, patch_dict). Returns result dict of simulate()."""
    kw, patch = args
    with patched(**(patch or {})):
        return J.simulate(**kw)[0]

def pmap(jobs, procs=None):
    from multiprocessing import Pool
    with Pool(procs) as p:
        return p.map(run, jobs, chunksize=max(1, len(jobs)//(4*(os.cpu_count() or 4))))

def save(name, obj):
    with open(os.path.join(OUT, name), "w") as f: json.dump(obj, f, indent=1, default=float)
