"""Verification of the virtual tank solver (SIMULATED virtual tank - not physical evidence).
1 mass balance, 2 uniform-lane check, 3 sweep/through vs cot(theta), 4 grid check, 5 time-step check."""
import json, os
import numpy as np
from dataclasses import replace
import multiprocessing as _mp
Pool = _mp.get_context("fork").Pool
from vtank import Params, Flow, Geometry, Sim, LABEL

HERE = os.path.dirname(os.path.abspath(__file__))
NOM = Params()


def flow_of(**kw):
    P = replace(NOM, **kw)
    return P, Flow(P, Geometry(P))


def eta_job(a):
    P = replace(NOM, **a["kw"])
    s = Sim(P, a["seed"]); s.release_bells(30); s.run(180)
    return a["tag"], s.summary()["bypass"] / 30


def main():
    out = dict(label=LABEL)
    # 1 mass balance
    mb = {}
    for name, kw in [("lane no screen", dict(screen=False)), *[(f"lane screen {a} deg", dict(theta_deg=a)) for a in (8, 11, 15, 20)],
                     ("lane 4 entrances", dict(n_mid_slots=3)), ("open tank", dict(layout="open", screen=False)),
                     ("open + curtain 20 deg", dict(layout="open", screen=False, curtain=True))]:
        P, f = flow_of(**kw)
        mb[name] = dict(Q_in=f.Q_in, Q_out=f.Q_out, Q_bypass=f.Q_sink,
                        rel_imbalance=(f.Q_out + f.Q_sink - f.Q_in) / f.Q_in, max_cell_residual=f.max_cell_residual)
    out["mass_balance"] = mb
    # 2 uniform lane: no screen, no bypass -> u = U in the lane interior
    P, f = flow_of(screen=False, bypass_frac=0.0)
    j = (f.yc > P.y_lo + 0.02) & (f.yc < P.y_up - 0.02)
    i = (f.xc > 0.05) & (f.xc < 0.22)   # upstream of the screen toe / collector boxes
    u = f.F[0][np.ix_(i, j)]; v = f.F[1][np.ix_(i, j)]
    out["uniform_lane"] = dict(U=P.U, u_mean=float(u.mean()), u_maxerr=float(np.abs(u - P.U).max()), v_maxabs=float(np.abs(v).max()))
    # 3 sweep/through vs cot(theta) along the middle of the face (nearly transparent screen)
    st = {}
    for a in (8, 11, 15, 20):
        for ell in (0.002, 0.05):
            P, f = flow_of(theta_deg=a, ell_s=ell, bypass_frac=0.0, n_mid_slots=0)
            g = f.g
            ss = np.linspace(0.3, 0.7, 9) * g.Ls
            pts = g.S + ss[:, None] * g.t + 0.012 * g.n
            smp = f.sample(pts[:, 0], pts[:, 1])
            ut = smp[0] * g.t[0] + smp[1] * g.t[1]
            un = -(smp[0] * g.n[0] + smp[1] * g.n[1])
            st[f"{a} deg ell_s={ell}"] = dict(sweep_over_through=float(np.mean(ut / un)), cot_theta=float(1 / np.tan(np.radians(a))),
                                              un_over_Usin=float(np.mean(un) / (P.U * np.sin(np.radians(a)))))
    out["sweep_through"] = st
    # 4 grid check (flow): face-averaged through velocity and head; dx 10/5/2.5 mm
    gc = {}
    for dx in (0.01, 0.005, 0.0025):
        P, f = flow_of(dx=dx)
        g = f.g
        ss = np.linspace(0.1, 0.9, 17) * g.Ls
        pts = g.S + ss[:, None] * g.t + 0.015 * g.n
        smp = f.sample(pts[:, 0], pts[:, 1])
        un = -(smp[0] * g.n[0] + smp[1] * g.n[1])
        ut = smp[0] * g.t[0] + smp[1] * g.t[1]
        gc[f"dx={dx*1000:g} mm"] = dict(un_profile=un.tolist(), ut_profile=ut.tolist(), head_mm=f.screen_head_mm(),
                                        un_mean=float(un.mean()), ut_mean=float(ut.mean()), cells=f.nx * f.ny)
    out["grid_flow"] = gc
    # 4b/5 grid + dt check on eta_r (11 deg), 10 seeds each
    jobs = []
    for tag, kw in (("dx=5mm dt=0.01", {}), ("dx=10mm dt=0.01", dict(dx=0.01)), ("dx=2.5mm dt=0.01", dict(dx=0.0025)),
                    ("dx=5mm dt=0.005", dict(dt=0.005))):
        for sd in range(10):
            jobs.append(dict(tag=tag, kw=kw, seed=20000 + sd))
    with Pool(10) as p:
        res = p.map(eta_job, jobs)
    er = {}
    for tag, e in res:
        er.setdefault(tag, []).append(e)
    out["grid_dt_eta_r"] = {k: dict(mean=float(np.mean(v)), sd=float(np.std(v, ddof=1)), sem=float(np.std(v, ddof=1) / np.sqrt(len(v))))
                            for k, v in er.items()}
    with open(os.path.join(HERE, "results", "SIM_verification.json"), "w") as f:
        json.dump(out, f, indent=1)
    print(json.dumps({k: v for k, v in out.items() if k != "grid_flow"}, indent=1))
    print({k: (v["un_mean"], v["ut_mean"], v["head_mm"]) for k, v in gc.items()})


if __name__ == "__main__":
    main()
