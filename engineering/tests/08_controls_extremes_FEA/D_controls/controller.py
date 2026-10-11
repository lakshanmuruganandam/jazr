"""JAZR control logic as a pure, PLC-style step function (one scan per tick).

Layers (one unit / one lane):
  * Bloom Incident OS (central PLC, operator approval for every forward step):
      IDLE -alert-> ALERT -approve-> READY -approve-> DEPLOYING -(all bays down)-> OPERATE
      OPERATE -standdown+approve-> STANDDOWN -(all bays up)-> IDLE
      ALERT/READY -standdown-> IDLE
      any -estop|seismic-> SAFE (raise all, staged) -approve & no seismic & all up-> IDLE
  * Per-bay local controller (LBC): UP / LOWERING / DOWN / RAISING / FAULT.
      - raise request: filtered dP high (persistence) or cleaning cycle or OS raise-all;
        hard dP is a local hard-wired request (no persistence) that works without comms.
      - the PULSE RULE: at most K bays RAISING at once (each pulse <1 t).
        comms OK  -> central arbiter grants permits (priority: hard dP first, then round-robin).
        comms LOST-> local rule: TDMA slot (clock) AND, if cfg.busy_line, a hard-wired
                     'someone is raising' loop (independent of the network).
      - stuck drum: commanded motion with no limit-switch change for TO ticks -> FAULT (latched,
        motor off, alarm); other bays continue.
      - lowering only in DEPLOYING/OPERATE, comms OK, wind not high, no seismic; max L concurrent.
  * Lift/screw: RUN only if OS in OPERATE, camera healthy and no turtle detected (same scan).
  * Outlet selection: forecast fresh -> best safe outlet with hysteresis; else RECOVER.
The forecast/twin input (IT side) can only change the outlet recommendation; it never reaches
bay commands (checked exhaustively in model_check.py).
"""
from dataclasses import dataclass
from typing import NamedTuple, Tuple

UP, LOWERING, DOWN, RAISING, FAULT = "UP", "LOWERING", "DOWN", "RAISING", "FAULT"
OS_STATES = ("IDLE", "ALERT", "READY", "DEPLOYING", "OPERATE", "STANDDOWN", "SAFE")


@dataclass(frozen=True)
class Config:
    n: int = 3                 # screen bays (relief bay is passive, always open)
    K: int = 1                 # max bays raising simultaneously (pulse rule)
    L: int = 2                 # max bays lowering simultaneously (power)
    pers: int = 2              # persistence ticks for filtered dP-high
    to: int = 3                # stuck-drum timeout ticks without limit-switch progress
    dwell: int = 1             # ticks to stay UP after a cleaning raise before re-lowering
    cycle_every: int = 0       # 0 = cleaning requests come from input; >0 periodic per bay
    busy_line: bool = True     # hard-wired 'raising' interlock loop (fix found by model checking)
    tdma: bool = True          # local time-slot staggering under comms loss
    hysteresis: float = 0.1    # outlet switch only if score improves by > this
    bottom: int = 2            # encoder code at fully deployed (0 = stowed); progress = code change


class Bay(NamedTuple):
    mode: str = UP
    pers: int = 0              # dP-high persistence counter
    stall: int = 0             # ticks commanded without progress
    dwell: int = 0
    pos_prev: int = 0          # last seen position code (0 top .. 2 bottom) for progress detection
    want_up: bool = False      # latched raise request (cleared when UP)


class State(NamedTuple):
    os: str = "IDLE"
    bays: Tuple[Bay, ...] = ()
    outlet: str = "RECOVER"
    alarms: frozenset = frozenset()


class BayIn(NamedTuple):
    dp: int = 0                # 0 normal, 1 filtered-high, 2 hard (local hard-wired)
    pos: int = 0               # drum encoder code: 0 top .. cfg.bottom fully down
    cycle: bool = False        # cleaning-cycle request from scheduler


class Inputs(NamedTuple):
    bays: Tuple[BayIn, ...]
    alert: bool = False
    approve: bool = False
    standdown: bool = False
    estop: bool = False
    seismic: bool = False
    wind_high: bool = False
    comms_ok: bool = True
    clock: int = 0
    turtle: bool = False
    camera_ok: bool = True
    fc_fresh: bool = True
    fc_safe: Tuple[bool, bool] = (True, True)     # outlets A, B safe per 72 h forecast
    fc_score: Tuple[float, float] = (0.5, 0.4)    # higher = better (low drift-back)


class Outputs(NamedTuple):
    cmd: Tuple[str, ...]       # per bay: 'UP' (motor raise), 'DOWN' (motor lower), 'HOLD'
    screw_run: bool
    diverter_to_chute: bool
    outlet: str
    alarms: frozenset


def initial(cfg: Config) -> State:
    return State(bays=tuple(Bay() for _ in range(cfg.n)))


def _all(bays, modes, skip_fault=True):
    return all(b.mode in modes or (skip_fault and b.mode == FAULT) for b in bays)


def step(s: State, i: Inputs, cfg: Config):
    alarms = set()
    os_ = s.os
    # ---------------- Incident OS ----------------
    if i.estop or i.seismic:
        if os_ != "SAFE":
            os_ = "SAFE"
        alarms.add("SEISMIC_TRIP" if i.seismic else "ESTOP")
    elif os_ == "IDLE" and i.alert:
        os_ = "ALERT"
    elif os_ in ("ALERT", "READY") and i.standdown:
        os_ = "IDLE"
    elif os_ == "ALERT" and i.approve:
        os_ = "READY"
    elif os_ == "READY" and i.approve and not i.wind_high and i.comms_ok:
        os_ = "DEPLOYING"
    elif os_ == "DEPLOYING" and _all(s.bays, (DOWN,)):
        os_ = "OPERATE"
    elif os_ in ("DEPLOYING", "OPERATE") and i.standdown and i.approve:
        os_ = "STANDDOWN"
    elif os_ == "STANDDOWN" and _all(s.bays, (UP,)):
        os_ = "IDLE"
    elif os_ == "SAFE" and i.approve and _all(s.bays, (UP,)):
        os_ = "IDLE"
    raise_all = os_ in ("SAFE", "STANDDOWN", "IDLE", "ALERT", "READY")
    lower_ok = (os_ in ("DEPLOYING", "OPERATE") and i.comms_ok and not i.wind_high and not i.seismic and not i.estop)
    if i.wind_high:
        alarms.add("WIND_HIGH_MOTION_BLOCKED")
    if not i.comms_ok:
        alarms.add("COMMS_LOSS_LOCAL_MODE")

    # ---------------- per-bay request evaluation ----------------
    bays = list(s.bays)
    reqs = []
    for k, (b, bi) in enumerate(zip(bays, i.bays)):
        pers = min(b.pers + 1, cfg.pers) if bi.dp >= 1 else 0
        want = b.want_up or bi.dp == 2 or pers >= cfg.pers or (bi.cycle and os_ == "OPERATE") or raise_all
        if b.mode == UP:
            want = False
        bays[k] = b._replace(pers=pers, want_up=want)
        if b.mode == FAULT:
            alarms.add(f"DRUM_STUCK_B{k}")
        if bi.dp == 2:
            alarms.add(f"DP_HARD_B{k}")

    # ---------------- arbitration of raise permits (pulse rule) ----------------
    raising_now = [k for k, b in enumerate(bays) if b.mode == RAISING]
    candidates = [k for k, b in enumerate(bays) if b.mode in (DOWN, LOWERING) and b.want_up]
    permits = set()
    if i.comms_ok:
        free = cfg.K - len(raising_now)
        # priority: hard dP first, then round-robin from the clock (oldest-cleaned-first proxy, no starvation)
        pri = sorted(candidates, key=lambda k: (-i.bays[k].dp, (k - i.clock) % cfg.n))
        permits = set(pri[:max(0, free)])
    else:
        # each LBC decides in the same scan from what it can physically see: the hard-wired busy
        # loop as it was at the start of the scan (no in-scan arbitration -> races are modelled)
        busy = len(raising_now) > 0 if cfg.busy_line else False
        for k in candidates:
            slot_ok = (i.clock % cfg.n == k) if cfg.tdma else True
            if slot_ok and not busy:
                permits.add(k)
    if any(i.bays[k].dp == 2 for k in candidates if k not in permits):
        alarms.add("RAISE_DEFERRED_PULSE_RULE")

    # ---------------- per-bay mode machine ----------------
    lowering_now = sum(1 for b in bays if b.mode == LOWERING)
    cmds = []
    for k, (b, bi) in enumerate(zip(bays, i.bays)):
        mode, stall, dwell = b.mode, b.stall, b.dwell
        progressed = bi.pos != b.pos_prev
        if mode == FAULT:
            cmds.append("HOLD")
            bays[k] = b._replace(pos_prev=bi.pos)
            continue
        if mode in (RAISING, LOWERING):
            stall = 0 if progressed else stall + 1
            if stall >= cfg.to:
                mode = FAULT
                alarms.add(f"DRUM_STUCK_B{k}")
                cmds.append("HOLD")
                bays[k] = b._replace(mode=mode, stall=0, pos_prev=bi.pos, want_up=False)
                continue
        if mode == RAISING and bi.pos == 0:
            mode, dwell, stall = UP, cfg.dwell, 0
            bays[k] = bays[k]._replace(want_up=False)
        elif mode == LOWERING and bi.pos == cfg.bottom:
            mode, stall = DOWN, 0
        if mode in (DOWN, LOWERING) and k in permits:
            mode, stall = RAISING, 0
        elif mode == UP:
            dwell = max(0, dwell - 1)
            if lower_ok and dwell == 0 and bi.dp == 0 and lowering_now < cfg.L and not bays[k].want_up:
                mode, stall = LOWERING, 0
                lowering_now += 1
        cmd = {RAISING: "UP", LOWERING: "DOWN"}.get(mode, "HOLD")
        cmds.append(cmd)
        bays[k] = bays[k]._replace(mode=mode, stall=stall, dwell=dwell, pos_prev=bi.pos)

    # ---------------- lift / wildlife ----------------
    screw = os_ == "OPERATE" and i.camera_ok and not i.turtle
    diverter = i.turtle or not i.camera_ok
    if not i.camera_ok:
        alarms.add("CAMERA_FAULT_SCREW_STOPPED")

    # ---------------- outlet selection ----------------
    outlet = s.outlet
    if not i.fc_fresh or not any(i.fc_safe):
        outlet = "RECOVER"
        alarms.add("OUTLET_RECOVER_MODE")
    else:
        opts = {"A": i.fc_score[0], "B": i.fc_score[1]}
        safe = [o for o, ok in zip("AB", i.fc_safe) if ok]
        best = max(safe, key=lambda o: opts[o])
        if outlet not in safe or outlet == "RECOVER":
            outlet = best
        elif opts[best] > opts[outlet] + cfg.hysteresis:
            outlet = best
    return State(os=os_, bays=tuple(bays), outlet=outlet, alarms=frozenset(alarms)), \
        Outputs(cmd=tuple(cmds), screw_run=screw, diverter_to_chute=diverter, outlet=outlet, alarms=frozenset(alarms))
