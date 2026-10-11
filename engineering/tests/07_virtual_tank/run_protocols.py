"""
Run every pre-registered physical protocol T01-T16 in the VIRTUAL TANK.
*** SIMULATED virtual tank -- not physical evidence. ***

Usage:  python3 run_protocols.py [T01 T03 ...]      (default: all)
Writes  results/SIM_T##_*.csv  (copies of the blank datasheets, filled with
simulated logs) and results/sim_results.json (summaries + verdicts).
"""
import sys, os, json, time, csv
import numpy as np
from dataclasses import replace
import multiprocessing as _mp
Pool = _mp.get_context("fork").Pool
from vtank import (Params, Sim, Flow, Geometry, K_mesh, settling_velocity, surrogate_drho, SURR,
                   RHO, GRAV, LABEL, ACTIVE, INTAKE, BYPASS, EXIT_DOWN, EXIT_UP, KIND_FRAG,
                   KIND_TURTLE, KIND_FISH)

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
os.makedirs(RES, exist_ok=True)
JSON = os.path.join(RES, "sim_results.json")
NOM = Params()
SCALE = 20
N_BELLS = 30
EXT_SEEDS = 12          # extra seeds for statistics beyond the 3 protocol runs


def wcsv(name, header, rows):
    path = os.path.join(RES, name)
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header + ["data_type"])
        for r in rows:
            w.writerow(list(r) + [LABEL])
    return path


def stats(x):
    x = np.asarray(x, float)
    return dict(mean=float(x.mean()), min=float(x.min()), max=float(x.max()), n=int(len(x)))


def pool_map(fn, jobs):
    with Pool(min(10, len(jobs))) as p:
        return p.map(fn, jobs)


# =====================================================================================
# generic guidance run (T02, T03, T04, T13, sensitivity)
def job_guidance(a):
    kw, seed, T, wave = a.get("kw", {}), a["seed"], a.get("T", 180), a.get("wave")
    P = replace(NOM, **kw)
    s = Sim(P, seed)
    if wave is not None:
        Hw, Tp = wave
        om = 2 * np.pi / Tp
        k = om ** 2 / GRAV
        for _ in range(60):
            k = om ** 2 / (GRAV * np.tanh(k * P.H))
        s.wave = (Hw, om, k, P.H)
    s.release_bells(a.get("n", N_BELLS))
    t0 = time.time()
    s.run(T, early_stop=wave is None)
    out = s.summary()
    out.update(seed=seed, t_end=round(s.t, 1), cpu=round(time.time() - t0, 1),
               events=[(round(t, 2), i, c) for t, i, c in s.events if c in (INTAKE, BYPASS)])
    return out


# =====================================================================================
def T01():
    """Surrogate characterisation: density scatter -> settling velocity -> buoyancy class."""
    HOVER = 0.005   # |w_s| <= 5 mm/s  (<= 30 cm/min drift) = "hover" (our operationalisation)
    rows, frac = [], []
    for run in range(3):
        rng = np.random.default_rng(100 + run)
        n = N_BELLS
        d = rng.uniform(0.04, 0.06, n)
        drho = surrogate_drho(rng, n)
        vol = np.pi * d ** 3 / 12
        ws = settling_velocity(drho, d, vol, np.pi * d ** 2 / 4)
        cls = np.where(ws > HOVER, "sink", np.where(ws < -HOVER, "float", "hover"))
        frac.append(np.mean(cls == "hover"))
        S_t = 0  # tank salt reported relative to tuning (see notes)
        for i in range(n):
            rows.append([f"R{run+1}-B{i+1:02d}", round(d[i] * 100, 2), round(d[i] * 50, 2),
                         round((RHO + drho[i]) * vol[i] * 1000, 2), f"{SURR['gel']} {SURR['gel_pct']}%",
                         "tank tuned to median bell (0.1 g/L steps)", cls[i], "SIM",
                         f"drho={drho[i]:+.3f} kg/m3; w_s={ws[i]*1000:+.1f} mm/s"])
    wcsv("SIM_T01_surrogates.csv", ["bell_id", "diameter_cm", "height_cm", "mass_g", "recipe(agar/gelatin %)",
                                    "salt_g_per_L", "buoyancy(sink/hover/float)", "colour", "notes"], rows)
    # sensitivity: hover fraction vs density-scatter scale and vs hover threshold
    scan = {}
    for sc in (0.05, 0.1, 0.2, 0.5, 1.0, 2.0):
        rng = np.random.default_rng(7)
        d = rng.uniform(0.04, 0.06, 3000)
        dr = surrogate_drho(rng, 3000, sc)
        ws = settling_velocity(dr, d, np.pi * d ** 3 / 12, np.pi * d ** 2 / 4)
        scan[sc] = dict(sd_drho=float(dr.std()), hover_5mm=float(np.mean(np.abs(ws) <= 0.005)),
                        hover_10mm=float(np.mean(np.abs(ws) <= 0.010)), hover_3mm=float(np.mean(np.abs(ws) <= 0.003)))
    m = float(np.mean(frac))
    crosses = any(v["hover_5mm"] >= 0.8 for v in scan.values()) and m < 0.8
    verdict = "PASS" if m >= 0.8 else ("FAIL (nominal) / SENSITIVE" if crosses else "FAIL")
    return dict(test="T01", hover_frac=stats(frac), scan=scan, criterion=">=80% hover", verdict=verdict,
                note="hover = |w_s|<=5 mm/s; nominal scatter: gel % sd 0.05, air 0.02%+-0.02%, 0.1 g/L salt steps")


# =====================================================================================
def guidance_set(conds, nrep=3, ext=EXT_SEEDS, T=180):
    jobs, keys = [], []
    for ci, c in enumerate(conds):
        for r in range(nrep + ext):
            jobs.append(dict(kw=c["kw"], seed=10000 + 97 * r + c.get("seed_off", 0), T=T, wave=c.get("wave")))
            keys.append((ci, r))
    res = pool_map(job_guidance, jobs)
    out = [[None] * (nrep + ext) for _ in conds]
    for (ci, r), v in zip(keys, res):
        out[ci][r] = v
    return out


def T02_T03():
    angles = [8, 11, 15, 20]
    conds = [dict(name="T02 no screen, bypass off", kw=dict(screen=False, bypass_frac=0.0)),
             dict(name="T02 no screen, bypass on (control)", kw=dict(screen=False))]
    conds += [dict(name=f"T03 screen {a} deg", kw=dict(theta_deg=a)) for a in angles]
    res = guidance_set(conds)
    rows, summ = [], {}
    for c, rr in zip(conds, res):
        ang = c["kw"].get("theta_deg", "none") if c["kw"].get("screen", True) else "none"
        test = c["name"].split()[0]
        for k, v in enumerate(rr[:3]):
            rows.append([test, k + 1, ang, 11.0, v["n"], v["bypass"], v["intake"], v["stuck"], v["lost"],
                         v["t_end"], f"SIM_log seed={v['seed']}", "SIM"])
        eta = [v["bypass"] / v["n"] for v in rr]
        summ[c["name"]] = dict(eta_r_protocol=stats(eta[:3]), eta_r_all=stats(eta),
                               intake_frac=stats([v["intake"] / v["n"] for v in rr]),
                               stuck_frac=stats([v["stuck"] / v["n"] for v in rr]),
                               lost_frac=stats([v["lost"] / v["n"] for v in rr]))
    wcsv("SIM_T02_T03_guidance.csv", ["test", "run", "screen_angle_deg", "approach_speed_cm_s", "n_released",
                                      "n_bypass", "n_intake", "n_stuck_on_screen", "n_lost", "time_s",
                                      "video_file", "counter_initials"], rows)
    e11 = summ["T03 screen 11 deg"]["eta_r_protocol"]["mean"]
    all_lt04 = all(summ[f"T03 screen {a} deg"]["eta_r_protocol"]["mean"] < 0.4 for a in angles)
    v3 = "PASS" if e11 >= 0.7 else "FAIL"
    if all_lt04:
        v3 = "KILL (eta_r<0.4 at every angle)"
    # keep events of 11-deg runs for T16
    ev = {"T03_11": [v["events"] for v in res[3][:6]], "T02_on": [v["events"] for v in res[1][:6]]}
    with open(os.path.join(RES, "_events_for_T16.json"), "w") as f:
        json.dump(ev, f)
    return dict(test="T02/T03", conditions=summ, verdict_T02="REFERENCE (no criterion)",
                verdict_T03=v3, criterion="eta_r >= 0.7 at 11 deg; kill if <0.4 at every angle",
                note="eta_r = n_bypass / n_released (conservative; stuck bells count against)")


def T04():
    conds = [dict(name="2 entrances", kw=dict(n_mid_slots=1)), dict(name="4 entrances", kw=dict(n_mid_slots=3))]
    res = guidance_set(conds)
    Ls = Geometry(NOM).Ls
    rows, summ = [], {}
    for c, rr in zip(conds, res):
        sp_cm = Ls / (c["kw"]["n_mid_slots"] + 1) * 100
        for k, v in enumerate(rr[:3]):
            rows.append([k + 1, round(sp_cm, 1), v["n"], v["bypass"], v["intake"], v["stuck"], f"SIM_log seed={v['seed']}"])
        summ[c["name"]] = dict(spacing_cm=sp_cm, eta_r=stats([v["bypass"] / v["n"] for v in rr]),
                               stuck=stats([v["stuck"] for v in rr]), stuck_protocol=stats([v["stuck"] for v in rr[:3]]))
    wcsv("SIM_T04_entrance_spacing.csv", ["run", "spacing_cm", "n_released", "n_bypass", "n_intake", "n_stuck", "video_file"], rows)
    fewer = summ["4 entrances"]["stuck"]["mean"] < summ["2 entrances"]["stuck"]["mean"]
    return dict(test="T04", conditions=summ, criterion="more entrances -> fewer stuck",
                verdict="PASS" if fewer else "FAIL")


# =====================================================================================
def design_rate_per_min():
    """Bell feed rate giving the same dimensionless face-loading as the prototype design case."""
    n_p, U_p, W_p, D_p = 0.3, 0.5, 28.0, 7.0                 # 0.3 /m3, lane 28 m x 7 m at 0.5 m/s
    flux_p = n_p * U_p * W_p * D_p                          # bells / s
    a_p = np.pi * 0.3 ** 2 / 4                               # 30 cm Catostylus bell
    A_face_p = 1000.0
    Pi_p = flux_p * a_p / A_face_p                           # fraction of face arriving per second
    Pi_m = Pi_p * np.sqrt(SCALE)                             # Froude time scale
    g = Geometry(NOM)
    A_face_m = g.Ls * NOM.H
    a_m = np.pi * 0.05 ** 2 / 4
    return float(Pi_m * A_face_m / a_m * 60)


def job_clog(a):
    P = replace(NOM, **a.get("kw", {}))
    s = Sim(P, a["seed"])
    rate = a["rate"] / 60.0
    acc = [0.0]
    cyc = a["cycling"]
    state = dict(next=20.0, up=None, until=0.0, k=0)
    ts = []

    def cb(sim):
        acc[0] += rate * P.dt
        if acc[0] >= 1:
            nn = int(acc[0]); acc[0] -= nn
            sim.release_bells(nn, x_range=(0.03, 0.10))
        if cyc:
            if state["up"] is None and sim.t >= state["next"]:
                state["up"] = state["k"] % P.n_bays; state["k"] += 1
                sim.set_bay(state["up"], True); state["until"] = sim.t + 2.0
            elif state["up"] is not None and sim.t >= state["until"]:
                sim.set_bay(state["up"], False); state["up"] = None; state["next"] = sim.t + 18.0
        if sim.step_i % 100 == 0:
            ts.append((round(sim.t, 1), sim.flow.screen_head_mm(), sim.face_cover_pct(),
                       int((sim.status == INTAKE).sum()), int((sim.status == BYPASS).sum())))

    s.run(a.get("T", 300), early_stop=False, callback=cb)
    ts = np.array(ts)
    def at(t):
        return ts[np.argmin(np.abs(ts[:, 0] - t))]
    first50 = ts[ts[:, 2] > 50, 0]
    return dict(rate=a["rate"], cycling=cyc, seed=a["seed"], n_fed=s.N,
                dh0=float(at(5)[1]), dh1=float(at(60)[1]), dh5=float(at(300)[1]),
                cover1=float(at(60)[2]), cover5=float(at(300)[2]), cover_max=float(ts[:, 2].max()),
                t_cover50=float(first50[0]) if len(first50) else None,
                intake=int((s.status == INTAKE).sum()), bypass=int((s.status == BYPASS).sum()),
                ts=ts.tolist())


def T05():
    dr = design_rate_per_min()
    rates = [10, 20, round(dr), round(2 * dr)]
    jobs = [dict(rate=r, cycling=c, seed=500 + k) for r in rates for c in (False, True) for k in range(3)]
    res = pool_map(job_clog, jobs)
    rows = []
    for i, v in enumerate(res):
        rows.append([i + 1, v["rate"], "Y" if v["cycling"] else "N", round(v["dh0"], 4), round(v["dh1"], 4),
                     round(v["dh5"], 4), round(v["cover5"], 1), v["intake"], f"SIM_log seed={v['seed']}"])
    wcsv("SIM_T05_clogging.csv", ["run", "bells_per_min", "bay_cycling(Y/N)", "dP_mm_water_t0", "dP_mm_t1min",
                                  "dP_mm_t5min", "face_cover_pct_photo", "n_intake", "video_file"], rows)
    summ = {}
    for r in rates:
        for c in (False, True):
            vv = [v for v in res if v["rate"] == r and v["cycling"] == c]
            summ[f"{r}/min cycling={'Y' if c else 'N'}"] = dict(
                dh0=stats([v["dh0"] for v in vv]), dh5=stats([v["dh5"] for v in vv]),
                cover1=stats([v["cover1"] for v in vv]), cover5=stats([v["cover5"] for v in vv]),
                cover_max=stats([v["cover_max"] for v in vv]), intake=stats([v["intake"] for v in vv]),
                fed=stats([v["n_fed"] for v in vv]),
                t_cover50=[v["t_cover50"] for v in vv])
    with open(os.path.join(RES, "_T05_timeseries.json"), "w") as f:
        json.dump([dict(rate=v["rate"], cycling=v["cycling"], seed=v["seed"], ts=v["ts"]) for v in res], f)
    d = [v for v in res if v["rate"] == round(dr)]
    kill = any(v["t_cover50"] is not None and v["t_cover50"] < 60 for v in d)
    cyc = [v for v in d if v["cycling"]]
    stable = all(v["dh5"] <= 1.5 * max(v["dh0"], 1e-6) for v in cyc)
    verdict = "KILL (face >50% covered <1 min at design rate)" if kill else ("PASS" if stable else "FAIL")
    return dict(test="T05", design_rate_per_min=dr, rates=rates, conditions=summ, verdict=verdict,
                criterion="cycling keeps dP stable at design rate (operationalised: dP(5min) <= 1.5 x dP(t0)); "
                          "kill: >50% face covered in <1 min at design rate",
                note="dP values are far below what two clear tubes can resolve (~0.5 mm): see README")


# =====================================================================================
def job_deploy(a):
    P = replace(NOM, screen=False)
    s = Sim(P, a["seed"])
    rng = s.rng
    s.release_bells(N_BELLS)
    t_start = rng.uniform(1.0, 4.0)
    v_d = rng.uniform(0.03, 0.06)          # hand lowering speed on a string
    handling = rng.uniform(2.0, 5.0)       # find slots, align, release string
    W_bar = 0.3                            # N, weighted bottom dowel
    st = dict(phase="wait", z=P.H + 0.05, seat_t=None, gap=None, pinned=0)
    s.bay_zlo[:] = P.H + 0.05

    def cb(sim):
        if st["phase"] == "wait" and sim.t >= t_start:
            st["phase"] = "lower"; sim.block_override = True
        if st["phase"] == "lower":
            st["z"] -= v_d * P.dt
            sim.bay_zlo[:] = max(st["z"], P.bottom_gap)
            if st["z"] < P.H / 2 and sim.flow.raised.all():
                sim.flow.raised[:] = False; sim.flow.solve()
            if st["z"] <= 0:
                st["phase"] = "seated"; st["seat_t"] = sim.t
                # pinned bells under the bottom bar?
                A = np.nonzero(sim.status == ACTIVE)[0]
                rel = sim.pos[A, :2] - sim.g.S
                sa, na = rel @ sim.g.t, rel @ sim.g.n
                r = sim.d[A] / 2
                pin = (np.abs(na) < 0.9 * r) & (sa > 0) & (sa < sim.g.Ls) & (sim.pos[A, 2] - r < 0.01)
                st["pinned"] = int(pin.sum())
                gaps = np.full(P.n_bays, P.bottom_gap + rng.uniform(0, 0.0015))
                if pin.any():
                    for i in A[pin]:
                        rel_i = (sim.pos[i, :2] - sim.g.S) @ sim.g.t
                        b = int(np.clip(rel_i / (sim.g.Ls / P.n_bays), 0, P.n_bays - 1))
                        strain = min(0.7, (W_bar / P.n_bays) / (sim.E[i] * sim.d[i] * 0.01))
                        gaps[b] = max(gaps[b], sim.d[i] * (1 - strain))
                    # rigid strip tilts: neighbours get half the gap
                    g2 = gaps.copy()
                    for b in range(P.n_bays):
                        for nb in (b - 1, b + 1):
                            if 0 <= nb < P.n_bays:
                                g2[nb] = max(g2[nb], 0.5 * gaps[b])
                    gaps = g2
                sim.bay_zlo[:] = gaps
                st["gap"] = float(gaps.max())

    s.run(120, early_stop=False, callback=cb)
    under_after = sum(1 for t, i, c in s.events if c == 10 and st["seat_t"] is not None and t > st["seat_t"])
    under_during = sum(1 for t, i, c in s.events if c == 10 and (st["seat_t"] is None or t <= st["seat_t"]))
    passed_before = int(s.flags["raised_cross"].sum())
    return dict(seed=a["seed"], deploy_time=t_start * 0 + P.H / v_d + handling, seated=st["pinned"] == 0,
                gap_mm=st["gap"] * 1000, n=N_BELLS, under_after=under_after, under_during=under_during,
                pinned=st["pinned"])


def T06():
    res = pool_map(job_deploy, [dict(seed=600 + k) for k in range(10)])
    rows = [[k + 1, round(v["deploy_time"], 1), "Y" if v["seated"] else "N", round(v["gap_mm"], 1), v["n"],
             v["under_after"], f"SIM_log seed={v['seed']}; under during lowering={v['under_during']}; pinned={v['pinned']}"]
            for k, v in enumerate(res)]
    wcsv("SIM_T06_rolldown.csv", ["run", "deploy_time_s", "seated_fully(Y/N)", "bottom_gap_mm", "n_released",
                                  "n_under_bottom", "video_file"], rows)
    frac_runs = np.mean([v["under_after"] > 0 for v in res])
    zero = all(v["under_after"] == 0 for v in res)
    verdict = "KILL" if frac_runs > 0.10 else ("PASS" if zero else "FAIL")
    return dict(test="T06", runs=len(res), deploy_time=stats([v["deploy_time"] for v in res]),
                gap_mm=stats([v["gap_mm"] for v in res]), frac_runs_with_under=float(frac_runs),
                pinned_runs=int(sum(v["pinned"] > 0 for v in res)),
                under_during_lowering=stats([v["under_during"] for v in res]),
                criterion="gap ~0 and 0 bells under (seated); kill if bells pass under in >10% of runs",
                verdict=verdict)


# =====================================================================================
def job_relief(a):
    P = replace(NOM, bypass_frac=0.0)       # bypass blocked -> face loads up (the case relief exists for)
    s = Sim(P, a["seed"])
    s.release_bells(40)
    s.run(60, early_stop=False)
    on_face = s.summary()["stuck"]
    t_lift = s.t
    bays = list(range(P.n_bays)) if a["bay"] == "all" else [a["bay"]]
    for b in bays:
        s.flow.raised[b] = True
    s.flow.solve()
    s.run(5, early_stop=False)
    for b in bays:
        s.flow.raised[b] = False
    s.flow.solve()
    s.run(40, early_stop=False)
    crossed = {i for t, i, c in s.events if c == 12 and t >= t_lift}
    intake = sum(1 for i in crossed if s.status[i] == INTAKE)
    return dict(seed=a["seed"], bay=a["bay"], on_face=on_face, released=len(crossed), intake=intake)


def T07():
    jobs = [dict(seed=700 + k, bay=k % 4) for k in range(8)] + [dict(seed=780 + k, bay="all") for k in range(3)]
    res = pool_map(job_relief, jobs)
    rows = [[k + 1, v["on_face"], v["released"], v["intake"],
             f"lifted bay {v['bay'] if v['bay']=='all' else v['bay']+1} (bay 1 = upstream) for 5 s; bypass closed to load face; seed={v['seed']}"]
            for k, v in enumerate(res)]
    wcsv("SIM_T07_relief_pulse.csv", ["run", "bells_on_face_before", "bells_released_on_rollup", "n_into_intake", "notes"], rows)
    one = [v for v in res if v["bay"] != "all"]
    frac = [v["released"] / max(v["on_face"], 1) for v in one]
    by_bay = {b + 1: stats([v["released"] / max(v["on_face"], 1) for v in one if v["bay"] == b]) for b in range(4)}
    allb = [v["released"] / max(v["on_face"], 1) for v in res if v["bay"] == "all"]
    worst = max(frac)
    verdict = "PASS" if np.mean(frac) <= 0.35 else "FAIL"
    if np.mean(frac) <= 0.35 < worst:
        verdict = "PASS on average / FAIL for the downstream bay"
    return dict(test="T07", single_bay_pulse_frac=stats(frac), by_bay=by_bay, all_bays_pulse_frac=stats(allb),
                criterion="pulse is a small fraction of bells on the face (operationalised: <=35%, ~one bay of four + margin)",
                verdict=verdict)


# =====================================================================================
def job_outer(a):
    P = replace(NOM, layout="open", screen=False, curtain=True, curtain_angle=a["angle"], U=0.05)
    s = Sim(P, a["seed"])
    sgn = 1 if a["dir"] == "flood" else -1
    s.scale = lambda t: (sgn, 0.0)
    g = s.g.curtains[0]
    ylo, yhi = min(g.p0[1], g.p1[1]), max(g.p0[1], g.p1[1])
    xr = (0.05, 0.15) if sgn > 0 else (P.Lx - 0.15, P.Lx - 0.05)
    s.release_bells(N_BELLS, x_range=xr, y_range=(ylo, yhi))
    s.run(150, early_stop=True)
    defl = int(s.flags["curtain_defl"].sum()); thr = int(s.flags["curtain_through"].sum())
    return dict(seed=a["seed"], angle=a["angle"], dir=a["dir"], n=N_BELLS, defl=defl, through=thr)


def T08():
    jobs = [dict(angle=an, dir=d, seed=800 + 10 * k + an) for an in (15, 20, 25) for d in ("flood", "ebb") for k in range(3)]
    res = pool_map(job_outer, jobs)
    rows = [[k + 1, v["angle"], v["dir"], v["n"], v["defl"], v["through"], f"SIM_log seed={v['seed']}"] for k, v in enumerate(res)]
    wcsv("SIM_T08_outer_line.csv", ["run", "line_angle_deg", "flow_direction(flood/ebb)", "n_released", "n_deflected",
                                    "n_through", "video_file"], rows)
    summ = {}
    for an in (15, 20, 25):
        for d in ("flood", "ebb"):
            vv = [v for v in res if v["angle"] == an and v["dir"] == d]
            summ[f"{an} deg {d}"] = dict(eta_g=stats([v["defl"] / v["n"] for v in vv]),
                                         through=stats([v["through"] / v["n"] for v in vv]))
    ok = {an: all(summ[f"{an} deg {d}"]["eta_g"]["mean"] >= 0.4 for d in ("flood", "ebb")) for an in (15, 20, 25)}
    verdict = "PASS at " + ",".join(f"{a} deg" for a in ok if ok[a]) if any(ok.values()) else "FAIL"
    return dict(test="T08", conditions=summ, criterion="eta_g >= 0.4 in both directions", verdict=verdict,
                note="curtain covers z=3-19 cm of 25 cm (open top 6 cm); far-field 5 cm/s")


# =====================================================================================
def T09():
    """Passage damage: strain/impact/abrasion model per path (parametric, not flow-resolved)."""
    gel = dict(gelatin=dict(eps_f=0.6, sd=0.15), agar=dict(eps_f=0.25, sd=0.08))
    paths = [("screw", None), ("siphon", 0.5), ("pump", None), ("tube", 1.0), ("tube", 3.0), ("tube", 5.0)]
    rows, summ = [], {}
    for gname in ("gelatin", "agar"):
        G = gel[gname]
        for run in range(3):
            rng = np.random.default_rng(900 + run + (50 if gname == "agar" else 0))
            for path, Lt in paths:
                key = f"{gname}:{path}{'' if Lt is None else f'_{Lt:g}m'}"
                sc = []
                for b in range(N_BELLS):
                    d = rng.uniform(0.04, 0.06)
                    E = NOM.E * (1 if gname == "gelatin" else 4)
                    eps_f = max(0.05, rng.normal(G["eps_f"], G["sd"]))
                    c = np.sqrt(E / RHO)
                    if path == "screw":       # rotating-tube screw, 30 rpm, R=4 cm, 2 flights, 6 cm bore
                        ID, Lp, v = 0.06, 0.3, 0.04
                        strike = rng.random() < min(1, 2 * 0.5 * d / 0.10)
                        v_imp = 2 * np.pi * 0.5 * 0.04 if strike else 0.0
                    elif path == "pump":      # aquarium centrifugal pump, 3000 rpm, R=1.5 cm
                        ID, Lp, v = 0.012, 0.5, 0.6
                        v_imp = 2 * np.pi * 50 * 0.015 * rng.uniform(0.5, 1.0)
                    else:                     # siphon / tube, 4 cm ID, 0.25 m/s
                        ID, Lp, v = 0.04, Lt, 0.25
                        v_imp = 0.0
                    eps_sq = max(0.0, 1 - ID / d)
                    eps_imp = v_imp / c
                    eps = max(eps_sq, eps_imp)
                    if eps > 2 * eps_f:
                        score = 3
                    elif eps > eps_f:
                        score = 2
                    elif rng.random() < 1 - np.exp(-0.5 * Lp * eps_sq * 10):
                        score = 1
                    else:
                        score = 0
                    sc.append(score)
                    rows.append([f"{gname[:3]}-R{run+1}-B{b+1:02d}", path, "" if Lt is None else Lt,
                                 round(Lp / v, 1), "Y" if score <= 1 else "N", score, "SIM"])
                summ.setdefault(key, []).extend(sc)
    wcsv("SIM_T09_passage_damage.csv", ["bell_id", "path(screw/siphon/pump/tube)", "tube_length_m", "transit_s",
                                        "intact(Y/N)", "damage_score_0_3", "photo_file"], rows)
    out = {k: dict(intact_frac=float(np.mean(np.array(v) <= 1)), mean_score=float(np.mean(v))) for k, v in summ.items()}
    ok = all(out[f"gelatin:{p}"]["intact_frac"] >= 0.9 for p in ("screw", "siphon_0.5m"))
    ok_agar = all(out[f"agar:{p}"]["intact_frac"] >= 0.9 for p in ("screw", "siphon_0.5m"))
    kill = any(out[f"gelatin:{p}"]["intact_frac"] < 0.5 for p in ("screw", "siphon_0.5m"))
    verdict = ("PASS" if ok else ("KILL" if kill else "FAIL")) + ("" if ok == ok_agar else " (SENSITIVE to gel recipe)")
    return dict(test="T09", paths=out, criterion=">=90% intact via screw/siphon; kill <50%", verdict=verdict,
                note="intact = damage score <=1 (no tear). Model is parametric (strain/impact), not flow-resolved")


# =====================================================================================
def job_turtle(a):
    P = replace(NOM)
    s = Sim(P, a["seed"])
    var = a["variant"]
    rng = s.rng
    n = 10
    d = np.full(n, 0.05)
    xy = np.column_stack([rng.uniform(0.03, 0.2, n), rng.uniform(P.y_lo + 0.03, P.y_up - 0.03, n)])
    if var == "clay_weighted":
        drho, swim, z = np.full(n, 600.0), 0.0, np.full(n, 0.025)
    elif var == "neutral_passive":
        drho, swim, z = rng.normal(0, 0.3, n), 0.0, rng.uniform(0.03, 0.22, n)
    else:
        drho, swim, z = rng.normal(0, 0.3, n), 0.08, rng.uniform(0.03, 0.22, n)
    ids = s.add(xy, z, d, drho, KIND_TURTLE, E=1e7, swim=swim, dome=True)
    x0 = s.pos[ids, 0].copy()
    s.run(180, early_stop=True)
    moved = np.abs(s.pos[ids, 0] - x0)
    out = []
    for i in ids:
        st = s.status[i]
        fate = {BYPASS: "bypass", INTAKE: "intake", EXIT_UP: "exit_upstream"}.get(st, "in_tank")
        out.append(dict(fate=fate, moved=float(moved[i - ids[0]]) if st == ACTIVE else None))
    return dict(seed=a["seed"], variant=var, turtles=out)


def bypass_interlock(rng, mode, swim, door_th=0.006):
    """Camera/person trigger + diverter + spring door, 1-D collector model (model scale)."""
    v_c = 0.05 + swim                               # m/s along collector
    L_div = 0.15                                    # camera -> diverter
    if mode == "person_mock":
        p_det, lat = 0.97, np.exp(rng.normal(np.log(0.6), 0.4))
    else:
        p_det, lat = 0.95, np.exp(rng.normal(np.log(0.15), 0.3))
    t_act = 0.3
    det = rng.random() < p_det
    if det and lat + t_act < L_div / v_c:
        return "diverted", 0.0
    A = np.pi * 0.05 ** 2 / 4
    F = 0.5 * RHO * 0.5 * A * 0.05 ** 2 + 0.5 * RHO * 0.5 * A * swim ** 2
    if mode.endswith("+door") and F >= door_th:
        return "door_exit", F
    return "screw_path", F


def T10():
    jobs = [dict(seed=1000 + k + 10 * j, variant=v) for j, v in enumerate(("clay_weighted", "neutral_passive", "swimmer"))
            for k in range(3)]
    res = pool_map(job_turtle, jobs)
    rows, summ = [], {}
    rng = np.random.default_rng(1010)
    A = np.pi * 0.05 ** 2 / 4
    F_bell_pile = 5 * 0.5 * RHO * 0.5 * A * 0.05 ** 2
    for k, v in enumerate(res):
        var = v["variant"]
        swim = 0.08 if var == "swimmer" else 0.0
        mass_g = round((RHO + (600 if var == "clay_weighted" else 0)) * np.pi * 0.05 ** 3 / 12 * 1000, 1)
        for mode in ("person_mock", "camera", "camera+door"):
            res_m = []
            for j, t in enumerate(v["turtles"]):
                if var == "clay_weighted":
                    tank_fate = "hand-placed at bypass entrance (clay does not move at 11 cm/s)"
                    enter = True
                else:
                    tank_fate = t["fate"]
                    enter = t["fate"] == "bypass"
                if enter:
                    o, F = bypass_interlock(rng, mode, swim)
                else:
                    o, F = ("exit_upstream" if t["fate"] == "exit_upstream" else
                            ("REACHED_INTAKE" if t["fate"] == "intake" else "impinged/in tank (not in bypass)")), 0.0
                res_m.append(o)
                rows.append([f"{var}-{mode}-R{k % 3 + 1}-T{j+1:02d}", mass_g, f"{tank_fate} -> {mode}",
                             "Y" if o in ("diverted", "door_exit") else "N", round(F, 5), "", f"SIM_log seed={v['seed']}"])
            summ.setdefault(f"{var}|{mode}", []).extend(res_m)
    wcsv("SIM_T10_turtle.csv", ["run", "turtle_model_mass_g", "path", "diverted_to_chute(Y/N)", "door_force_N",
                                "time_s", "video_file"], rows)
    out = {}
    for k, v in summ.items():
        v = np.array(v)
        out[k] = dict(n=len(v), diverted_or_exit=float(np.mean(np.isin(v, ["diverted", "door_exit", "exit_upstream"]))),
                      screw_path=int((v == "screw_path").sum()), intake=int((v == "REACHED_INTAKE").sum()),
                      not_in_bypass=int(np.sum(np.char.startswith(v.astype(str), "impinged"))))
    any_screw = any(o["screw_path"] > 0 or o["intake"] > 0 for o in out.values())
    cam_door = [o for k, o in out.items() if k.endswith("camera+door")]
    return dict(test="T10", conditions=out, criterion="100% diverted or exit; kill: any turtle reaching screw path",
                F_bell_pile_N=F_bell_pile, door_threshold_N=0.006,
                verdict=("KILL (some configurations)" if any_screw else "PASS") + " / SENSITIVE to detection probability",
                note="Door forces are mN at 1:20 -> below spring-scale resolution; force scales x8000 (lambda^3) to prototype")


# =====================================================================================
def job_fish(a):
    P = NOM
    s = Sim(P, a["seed"])
    rng = s.rng
    s.release_bells(N_BELLS, d_range=(0.008, 0.012), drho=rng.normal(0, 0.3, N_BELLS), kind=KIND_FISH, E=1e7, dome=False)
    s.run(180)
    return dict(seed=a["seed"], **{k: v for k, v in s.summary().items()})


def T11():
    res = pool_map(job_fish, [dict(seed=1100 + k) for k in range(6)])
    rows = [[k + 1, "rigid bead 0.8-1.2 cm, near-neutral", v["n"], v["bypass"], v["intake"],
             f"stuck={v['stuck']} lost={v['lost']} seed={v['seed']}"] for k, v in enumerate(res)]
    wcsv("SIM_T11_fish_return.csv", ["run", "fish_model", "n_released", "n_returned_bypass", "n_intake", "notes"], rows)
    return dict(test="T11", returned=stats([v["bypass"] / v["n"] for v in res]),
                stuck=stats([v["stuck"] / v["n"] for v in res]), criterion="report (no target)", verdict="REPORTED")


# =====================================================================================
def job_drift(a):
    P = replace(NOM, layout="open", screen=False, U=0.011)
    s = Sim(P, a["seed"])
    T_half, ramp, net = 60.0, 3.0, 0.10
    sgn0 = 1 if a["phase"] == "flood" else -1

    def scale(t):
        k = int(t // T_half)
        tau = t - k * T_half
        sg = sgn0 * (1 if k % 2 == 0 else -1)
        if tau < ramp:
            prev = -sg
            f = prev + (sg - prev) * tau / ramp if k > 0 else sg * tau / ramp
            df = (sg - prev) / ramp if k > 0 else sg / ramp
        else:
            f, df = sg, 0.0
        return f + net, df
    s.scale = scale
    x = P.Lx - a["dist"]
    s.release_bells(N_BELLS, x_range=(x - 0.02, x + 0.02))
    counts = []
    for k in range(3):
        s.run(2 * T_half, early_stop=False)
        counts.append(int((s.status == EXIT_DOWN).sum()))
    return dict(seed=a["seed"], dist=a["dist"], phase=a["phase"], counts=counts,
                exported=int((s.status == EXIT_UP).sum()))


def T12():
    dists = (0.3, 0.6, 1.0)
    jobs = [dict(dist=d, phase=ph, seed=1200 + 7 * k + int(d * 10)) for d in dists for ph in ("flood", "ebb") for k in range(3)]
    res = pool_map(job_drift, jobs)
    rows = []
    for k, v in enumerate(res):
        for kc in range(3):
            rows.append([k + 1, v["dist"] * 100, v["phase"], N_BELLS, v["counts"][kc], kc + 1, f"SIM_log seed={v['seed']}"])
    wcsv("SIM_T12_driftback.csv", ["run", "release_distance_cm", "release_phase", "n_released",
                                   "n_returned_to_intake_after_k_cycles", "k_cycles", "video_file"], rows)
    summ = {f"{d} m": dict(ret_after_3=stats([v["counts"][2] / N_BELLS for v in res if v["dist"] == d]),
                           ret_after_1=stats([v["counts"][0] / N_BELLS for v in res if v["dist"] == d])) for d in dists}
    m = [summ[f"{d} m"]["ret_after_3"]["mean"] for d in dists]
    verdict = "PASS" if m[0] >= m[1] >= m[2] and m[0] > m[2] else "FAIL"
    return dict(test="T12", conditions=summ, criterion="returns fall with distance", verdict=verdict,
                note="tidal 1.1 cm/s (~0.05 m/s prototype), 60 s half-cycles, 10% net intake draw; excursion ~0.66 m")


# =====================================================================================
def T13():
    waves = [None, (0.01, 1.0), (0.02, 1.0), (0.04, 1.0), (0.02, 1.5), (0.04, 1.5)]
    conds = [dict(name=str(w), kw={}, wave=w) for w in waves]
    res = guidance_set(conds, nrep=3, ext=3, T=120)
    base = np.mean([v["bypass"] / v["n"] for v in res[0]])
    rows, summ = [], {}
    for c, rr in zip(conds, res):
        w = c["wave"]
        for k, v in enumerate(rr[:3]):
            rows.append([k + 1, 0 if w is None else w[0] * 100, "" if w is None else w[1], v["n"], v["bypass"],
                         v["under"] + v["over"], f"SIM_log seed={v['seed']}"])
        e = np.mean([v["bypass"] / v["n"] for v in rr])
        summ["no waves" if w is None else f"H={w[0]*100:.0f} cm T={w[1]} s"] = dict(
            eta_r=stats([v["bypass"] / v["n"] for v in rr]), rel_change=float((e - base) / base) if base else None,
            leaks=int(sum(v["under"] + v["over"] for v in rr)))
    wcsv("SIM_T13_waves.csv", ["run", "wave_height_cm", "period_s", "n_released", "n_bypass", "n_leaked_over_or_under", "video_file"], rows)
    worst = min(v["rel_change"] for k, v in summ.items() if k != "no waves")
    return dict(test="T13", conditions=summ, worst_rel_change=worst, criterion="eta_r drops <20%",
                verdict="PASS" if worst > -0.2 else "FAIL")


# =====================================================================================
def job_frag(a):
    P = replace(NOM, mesh_mm=a["mesh"])
    s = Sim(P, a["seed"])
    sz = a["size"]
    s.release_bells(20, d_range=(sz * 0.9, sz * 1.1), kind=KIND_FRAG, dome=False)
    s.run(120)
    return dict(size=sz, mesh=a["mesh"], seed=a["seed"], n=20, ext=int(s.flags["extruded"].sum()),
                dh=s.flow.screen_head_mm())


def T14():
    jobs = [dict(size=sz, mesh=m, seed=1400 + k) for sz in (0.01, 0.015, 0.02) for m in (3, 5, 8) for k in range(3)]
    res = pool_map(job_frag, jobs)
    rows = [[k + 1, v["size"] * 100, v["mesh"], v["n"], v["ext"], round(v["dh"], 4)] for k, v in enumerate(res)]
    wcsv("SIM_T14_extrusion.csv", ["run", "fragment_size_cm", "mesh_opening_mm", "n_fragments", "n_extruded", "dP_mm"], rows)
    # Cauchy-number scaling table: tank vs prototype
    sc_rows = []
    for E, lab in ((30000, "agar ~1.5%"), (5000, "gelatin ~3% (nominal surrogate)"), (1000, "very soft gel"),
                   (300, "mesoglea upper (assumed)"), (50, "mesoglea lower (assumed)")):
        for where, un, H in (("tank 1:20, clean", 0.022, None), ("tank 1:20, 75% blinded", 0.022 / 0.25, None),
                             ("prototype 0.10 m/s, clean", 0.10, None), ("prototype, 75% blinded", 0.10 / 0.25, None)):
            dp = 0.5 * RHO * K_mesh(NOM.beta * (0.25 if "blinded" in where else 1.0)) * 0.10 ** 2 if "prototype" in where else \
                0.5 * RHO * K_mesh(NOM.beta * (0.25 if "blinded" in where else 1.0)) * 0.022 ** 2
            for d_over_a in (1.5, 2, 4):
                crit = NOM.c_ext * E * (d_over_a - 1)
                sc_rows.append([lab, E, where, round(dp, 2), d_over_a, round(crit, 1), round(dp / E, 5),
                                "EXTRUDES" if dp > crit else "holds"])
    wcsv("SIM_T14_cauchy_scaling.csv", ["material", "E_Pa", "condition", "dP_Pa", "fragment_over_opening",
                                        "dP_crit_Pa", "Cauchy_dP_over_E", "model_outcome"], sc_rows)
    tot = sum(v["ext"] for v in res)
    proto_ext = [r for r in sc_rows if "prototype" in r[2] and r[7] == "EXTRUDES"]
    return dict(test="T14", extruded_total=tot, fragments_total=20 * len(res),
                prototype_extrusion_cases=[f"{r[0]} | {r[2]} | d/a={r[4]}" for r in proto_ext],
                criterion="report; sets the mesh opening", verdict="REPORTED / SENSITIVE (tank cannot reproduce prototype Cauchy number)")


# =====================================================================================
def T15():
    rows, out = [], {}
    g = Geometry(NOM)
    for U in (0.11, 0.055):
        P = replace(NOM, U=U)
        fl = Flow(P, Geometry(P))
        A_face = g.Ls * P.H
        for b in (0.0, 0.25, 0.5, 0.75):
            for run in range(3):
                rng = np.random.default_rng(1500 + run)
                if run == 0:
                    cov = np.full(fl.nbins, b)
                else:   # patchy blinding with the same mean, heavier downstream (as seen in T05)
                    w = np.linspace(0.5, 1.5, fl.nbins) * rng.uniform(0.5, 1.5, fl.nbins)
                    cov = np.clip(b * w / w.mean(), 0, 0.95)
                fl.cov[:fl.nbins] = cov
                fl.solve()
                F = fl.screen_force_N()
                un = fl.un_bin.sum() * fl.BIN / g.Ls
                F_calc = 0.5 * RHO * K_mesh(P.beta * (1 - b)) * (P.U * (P.y_up - P.y_lo) * (1 - P.bypass_frac) / g.Ls) ** 2 * A_face
                rows.append([len(rows) + 1, b * 100, U * 100, round(F, 4),
                             f"calc(uniform)={F_calc:.4f} N; prototype-equiv x{SCALE**3} = {F*SCALE**3/1000:.2f} kN per strip; "
                             f"{'uniform' if run == 0 else 'patchy'} blinding"])
                out.setdefault(f"U={U*100:.1f}cm/s b={b}", []).append((F, F_calc))
    wcsv("SIM_T15_bay_load.csv", ["run", "blinding_pct", "approach_speed_cm_s", "force_N(spring/luggage scale)", "notes"], rows)
    summ = {k: dict(F_sim=stats([a for a, _ in v]), F_calc=v[0][1]) for k, v in out.items()}
    k11 = [summ[f"U=11.0cm/s b={b}"]["F_sim"]["mean"] for b in (0.0, 0.25, 0.5, 0.75)]
    mono = all(np.diff(k11) > 0)
    return dict(test="T15", conditions=summ, criterion="force scales with blinding; compare with calc",
                verdict="PASS (scales with blinding)" if mono else "FAIL",
                note="forces 0.01-1 N at tank scale: below luggage-scale resolution; use a 0.01 N spring scale or load cell")


# =====================================================================================
def T16():
    with open(os.path.join(RES, "_events_for_T16.json")) as f:
        ev = json.load(f)

    def counter(rng, times, p0=0.02, pc=0.03, pdbl=0.005):
        times = np.array(times)
        c = 0
        for t in times:
            coinc = np.sum(np.abs(times - t) < 1.0) - 1
            if rng.random() > p0 + pc * coinc:
                c += 1
            if rng.random() < pdbl:
                c += 1
        return c
    rows, disc = [], []
    rng = np.random.default_rng(1600)
    pick = rng.choice(len(ev["T03_11"]), 3, replace=False)
    for k, i in enumerate(pick):
        times = [t for t, _, c in ev["T03_11"][i] if c == BYPASS]
        a, b = counter(rng, times), counter(rng, times)
        vc = len(times)
        dsc = abs(a - b) / max(vc, 1)
        disc.append(dsc)
        rows.append(["T03 11deg bypass count", k + 1, a, b, vc, round(dsc, 3)])
    wcsv("SIM_T16_repeatability.csv", ["test", "run", "counter_A", "counter_B", "video_count", "discrepancy"], rows)
    # sensitivity: probability that a run meets <=5% vs counter error & event count
    sens = {}
    for p0 in (0.0, 0.02, 0.05):
        for n_ev in (15, 30, 60):
            ok = 0
            for _ in range(2000):
                t = np.sort(rng.uniform(0, 30, n_ev))
                ok += abs(counter(rng, t, p0) - counter(rng, t, p0)) / n_ev <= 0.05
            sens[f"p0={p0} n={n_ev}"] = ok / 2000
    return dict(test="T16", discrepancy=stats(disc), pass_prob=sens, criterion="<=5% discrepancy",
                verdict=("PASS" if max(disc) <= 0.05 else "FAIL") + " / SENSITIVE (one miss in ~15 counts = 6.7%)",
                note="'video_count' = logged ground truth; counters: miss 2% + 3% per coincident arrival (<1 s), double-count 0.5%")


TESTS = dict(T01=T01, T02=T02_T03, T04=T04, T05=T05, T06=T06, T07=T07, T08=T08, T09=T09, T10=T10, T11=T11,
             T12=T12, T13=T13, T14=T14, T15=T15, T16=T16)

if __name__ == "__main__":
    want = sys.argv[1:] or list(TESTS)
    allres = json.load(open(JSON)) if os.path.exists(JSON) else {}
    for k in want:
        t0 = time.time()
        r = TESTS[k]()
        r["wall_s"] = round(time.time() - t0, 1)
        r["label"] = LABEL
        allres[k] = r
        print(k, r.get("verdict", r.get("verdict_T03")), f"{r['wall_s']} s", flush=True)
        with open(JSON, "w") as f:
            json.dump(allres, f, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o))
