"""Time-domain bloom simulation with fault injection (1 unit, 15 screen bays + relief bay, 1 s scan).

Uses controller.step unchanged. Scenario (baseline 8 h):
  t=60 s alert; 120 s approve (READY); 180 s approve (DEPLOYING) -> lowering, L concurrent drums
  bloom density ramps to 0.3 ind/m3 by 10 min; 2.5-3.0 h surge to 1.0 ind/m3
  F1 1.0 h  bay 3 dP-A transmitter stuck at 2000 Pa
  F2 1.5 h  bay 5 dP-B transmitter dropout (NaN)
  F3 2.0 h  bay 7 drum seizes (cannot move)
  F4 3.0-3.5 h comms loss (local mode: TDMA + hard-wired busy line)
  F5 4.0-5.0 h storm sea Hs 1.5 m, Tp 5 s (else Hs 0.6 m, Tp 4 s) -> wave dP spikes
  F6 5.5 h  3 turtle detections; 5.6-5.7 h camera fault
  F7 6.0-6.5 h forecast stale; 6.2 h outlet A becomes unsafe
  F8 6.6-6.7 h wind gust > 20 m/s
  F9 7.0 h  seismic trip (clears 7.05 h); operator approves return to IDLE at 7.9 h
Cleaning scheduler (central, OPERATE only): when no bay is raising, request a cycle for the
oldest-cleaned DOWN bay if filtered line dP > 150 Pa or its age > 20 min.
"""
import json, sys, pathlib, time
import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent))
import controller as C
from plant import Plant, WaveDP, Sensing
from common import params as P

H = 3600


def run(hours=8.0, n=15, density=P.DESIGN_DENSITY, tau=60.0, s0=0.02, speed=P.DRUM_LINE_SPEED, K=1, L=6,
        sens_tau=30.0, sens_pers=20, raw_mode=False, hard_vote="2oo2", faults=True, surge=True, busy_line=True,
        tdma=True, clean_dp=150.0, clean_age=1200, seed=0, record=True, relief_mode="open", clean_in_place=False):
    T = int(hours * H)
    cfg = C.Config(n=n, K=K, L=L, pers=1, to=15, dwell=30, busy_line=busy_line, tdma=tdma, bottom=30)
    pl = Plant(n=n, density=0.0, tau=tau, s0=s0, speed=speed, seed=seed, relief_mode=relief_mode)
    waves_calm = WaveDP(n, 0.6, 4.0, seed=seed + 1)
    waves_storm = WaveDP(n, 1.5, 5.0, seed=seed + 2)
    sn = Sensing(n, tau=sens_tau, pers=sens_pers, raw_mode=raw_mode, hard_vote=hard_vote, seed=seed + 3)
    s = C.initial(cfg)
    last_clean = np.zeros(n)
    belt = np.zeros(n)
    log = {k: [] for k in ("t", "dp", "down", "raising", "rel", "os", "alarms", "outlet", "screw", "turtle", "camera", "lvl_bays", "approve")}
    events = []          # (t, bay, kg) per raise event
    cur_event = np.zeros(n)
    raise_cnt = 0
    dp_raises = 0
    false_dp_raises = 0
    t_all_up_after_seismic = None
    t_operate = None
    max_raising_local = 0
    screw_violation = 0
    arrivals = 0.0
    rel_hist = np.zeros(T)
    for t in range(T):
        th = t / H
        # ---------------- environment ----------------
        dens = density * min(1.0, t / 600)
        if surge and 2.5 <= th < 3.0:
            dens = 1.0
        pl.density = dens
        if faults:
            if t == int(1.0 * H): sn.fault[(3, 0)] = ("stuck", 2000.0)
            if t == int(1.5 * H): sn.fault[(5, 1)] = ("nan", None)
            if t == int(2.0 * H): pl.stuck_drum[7] = True
        comms = not (faults and 3.0 <= th < 3.5)
        wv = waves_storm if (faults and 4.0 <= th < 5.0) else waves_calm
        turtle = faults and int(5.5 * H) <= t < int(5.5 * H) + 30 and (t // 10) % 2 == 0
        camera_ok = not (faults and 5.6 <= th < 5.7)
        fresh = not (faults and 6.0 <= th < 6.5)
        safeA = not (faults and th >= 6.2)
        wind = faults and 6.6 <= th < 6.7
        seismic = faults and 7.0 <= th < 7.05
        alert = t == 60
        approve = t in (120, 180) or (faults and t == int(7.9 * H))
        # ---------------- sensing ----------------
        dp_bays = pl.dp + wv.dp(t)
        lvl, raw = sn.read(dp_bays)
        pos = pl.pos_code(cfg.bottom)
        # cleaning scheduler (central; needs comms)
        cyc = [False] * n
        if clean_in_place and s.os == "OPERATE":
            # belt cleaning releases nothing to the plant -> no pulse rule; up to 5 belts at once (power),
            # local timers keep cleaning during comms loss
            for k in sorted(range(n), key=lambda k: last_clean[k]):
                if (belt > 0).sum() >= 5:
                    break
                if belt[k] <= 0 and s.bays[k].mode == C.DOWN and \
                        (np.nanmedian(sn.lp[k]) > clean_dp or t - last_clean[k] > clean_age):
                    belt[k] = 60.0
                    last_clean[k] = t
        elif s.os == "OPERATE" and comms and not any(b.mode == C.RAISING for b in s.bays):
            cand = [k for k, b in enumerate(s.bays) if b.mode == C.DOWN]
            if cand:
                k = min(cand, key=lambda k: last_clean[k])
                if np.nanmedian(sn.lp[k]) > clean_dp or t - last_clean[k] > clean_age:
                    if clean_in_place:      # endless-belt face: biomass lifted to collector, bay stays closed
                        belt[k] = 60.0
                        last_clean[k] = t
                    else:
                        cyc[k] = True
        for k in np.where(belt > 0)[0]:
            if pl.stuck_drum[k]:          # seized drive: belt does not move (latent, not seen by PLC)
                belt[k] -= 1.0
                continue
            frac = 1.0 / belt[k]
            moved = (pl.slide[k] + pl.stuck[k]) * frac
            pl.slide[k] *= (1 - frac); pl.stuck[k] *= (1 - frac)
            pl.to_bypass_kg += moved
            belt[k] -= 1.0
        inp = C.Inputs(bays=tuple(C.BayIn(dp=int(lvl[k]), pos=int(pos[k]), cycle=cyc[k]) for k in range(n)),
                       alert=alert, approve=approve, seismic=seismic, wind_high=wind, comms_ok=comms, clock=t // 2,
                       turtle=turtle, camera_ok=camera_ok, fc_fresh=fresh, fc_safe=(safeA, True), fc_score=(0.6, 0.5))
        prev_modes = [b.mode for b in s.bays]
        s, out = C.step(s, inp, cfg)
        for k, b in enumerate(s.bays):
            if b.mode == C.RAISING and prev_modes[k] != C.RAISING:
                raise_cnt += 1
                cur_event[k] = 0.0
                if lvl[k] >= 1 and s.os == "OPERATE":
                    dp_raises += 1
                    if pl.dp < P.DP_TRIP:
                        false_dp_raises += 1
            if b.mode == C.UP and prev_modes[k] == C.RAISING:
                events.append((t, k, float(cur_event[k])))
                last_clean[k] = t
        nr = sum(1 for b in s.bays if b.mode == C.RAISING)
        if not comms:
            max_raising_local = max(max_raising_local, nr)
        if out.screw_run and (turtle or not camera_ok):
            screw_violation += 1
        if t_operate is None and s.os == "OPERATE":
            t_operate = t
        if faults and t >= int(7.0 * H) and t_all_up_after_seismic is None and all(b.mode in (C.UP, C.FAULT) for b in s.bays):
            t_all_up_after_seismic = t - int(7.0 * H)
        # ---------------- plant ----------------
        before = pl.to_bypass_kg + pl.to_plant_kg + (pl.slide.sum() + pl.stuck.sum())
        rel = pl.step(out.cmd)
        cur_event += rel
        rel_hist[t] = rel.sum()
        arrivals += pl.density * P.BELL_MASS * pl.Q
        if record:
            log["t"].append(t); log["dp"].append(pl.dp); log["down"].append(int((pl.x >= 1 - 1e-9).sum()))
            log["raising"].append(nr); log["rel"].append(float(rel.sum())); log["os"].append(s.os)
            log["alarms"].append(sorted(set(out.alarms) | {f"SENSOR_DISAGREE_B{k}" for k in np.where(sn.disagree)[0]})); log["outlet"].append(out.outlet); log["screw"].append(out.screw_run)
            log["turtle"].append(turtle); log["camera"].append(camera_ok)
            log["lvl_bays"].append([int(k) for k in np.where(lvl >= 1)[0]]); log["approve"].append(bool(approve))
    win = int(pl.travel)
    roll = np.convolve(rel_hist, np.ones(win), "valid")
    ev_kg = [e[2] for e in events]
    m = dict(deploy_time_s=(t_operate - 180) if t_operate else None, raises=raise_cnt,
             max_event_kg=max(ev_kg) if ev_kg else 0.0, events_over_1t=int(sum(1 for x in ev_kg if x > P.PULSE_LIMIT_KG)),
             mean_event_kg=float(np.mean(ev_kg)) if ev_kg else 0.0,
             max_release_in_any_raise_window_kg=float(roll.max()),
             max_line_dp=float(max(log["dp"])) if record else float("nan"),
             max_raising_during_comms_loss=max_raising_local, screw_with_turtle_or_camfault_s=screw_violation,
             leakage_to_plant_fraction=float(pl.to_plant_kg / max(arrivals, 1)),
             relief_and_open_bay_fraction=float(pl.relief_kg / max(arrivals, 1)),
             dp_triggered_raises=dp_raises, false_dp_raises=false_dp_raises,
             seismic_all_up_s=t_all_up_after_seismic,
             stuck_bay7_fault=bool(s.bays[7].mode == C.FAULT) if n > 7 else None)
    return m, log, events


def first_alarm_time(log, name, after):
    for t, a in zip(log["t"], log["alarms"]):
        if t >= after and name in a:
            return t - after
    return None


if __name__ == "__main__":
    t0 = time.time()
    m, log, ev = run(relief_mode=sys.argv[1] if len(sys.argv) > 1 else "open")
    print(json.dumps(m, indent=1), time.time() - t0)
