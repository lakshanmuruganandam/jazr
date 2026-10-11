"""Explicit-state model checking of controller.step (the same code used in the simulator).

Closed system = controller x abstract drum plant (position 0 top / 1 between / 2 bottom; on each
commanded scan the environment may move it one step OR stall it -> stuck/slow drums) x
environment levels (seismic, wind, comms) toggled by single events per scan (interleaving).

MC1 full OS + bays, n=2 bays: invariants, transition invariants, deadlock & liveness (EF safe-idle).
MC2 pulse rule under comms loss, n=3, for three local-rule designs: TDMA only, busy-line only,
    TDMA + busy-line (expected: only the last satisfies 'at most 1 bay raising').
MC3 wildlife + outlet logic: exhaustive truth table.
MC4 IT/OT separation: forecast inputs never change bay commands (all MC1 reachable states).
"""
import itertools, json, sys, pathlib, time
from collections import deque

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import controller as C

EVENTS = ("none", "alert", "approve", "standdown", "standdown+approve", "estop", "seismic", "wind", "comms")
BAYIN_CHOICES = ((0, False), (1, False), (2, False), (0, True))


def key(s):
    return s._replace(alarms=frozenset())


def explore(cfg, events=EVENTS, bayin=BAYIN_CHOICES, init_os="IDLE", init_env=(False, False, True),
            init_mode=C.UP, init_pos=0, max_states=400000, store_edges=True):
    """BFS. Node = (ctrl_state, plant_pos tuple, env (seismic, wind, comms), clock)."""
    s0 = C.initial(cfg)._replace(os=init_os, bays=tuple(C.Bay(mode=init_mode, pos_prev=init_pos) for _ in range(cfg.n)))
    n0 = (key(s0), (init_pos,) * cfg.n, init_env, 0)
    seen = {n0: 0}
    nodes = [n0]
    edges = []
    viol = {}
    q = deque([n0])
    t0 = time.time()
    while q:
        node = q.popleft()
        s, pos, env, clk = node
        sid = seen[node]
        succ = set()
        for ev in events:
            seis, wind, comms = env
            if ev == "seismic": seis = not seis
            if ev == "wind": wind = not wind
            if ev == "comms": comms = not comms
            for bins in itertools.product(bayin, repeat=cfg.n):
                inp = C.Inputs(bays=tuple(C.BayIn(dp=d, pos=p, cycle=c) for (d, c), p in zip(bins, pos)),
                               alert=ev == "alert", approve=ev in ("approve", "standdown+approve"),
                               standdown=ev in ("standdown", "standdown+approve"), estop=ev == "estop",
                               seismic=seis, wind_high=wind, comms_ok=comms, clock=clk)
                s2, out = C.step(s, inp, cfg)
                check_transition(s, inp, s2, out, cfg, viol, node)
                # plant: each commanded drum may move or stall
                opts = []
                for k, c in enumerate(out.cmd):
                    if c == "UP" and pos[k] > 0:
                        opts.append((pos[k] - 1, pos[k]))
                    elif c == "DOWN" and pos[k] < 2:
                        opts.append((pos[k] + 1, pos[k]))
                    else:
                        opts.append((pos[k],))
                for newpos in itertools.product(*opts):
                    nn = (key(s2), tuple(newpos), (seis, wind, comms), (clk + 1) % cfg.n)
                    check_state(nn, cfg, viol)
                    if nn not in seen:
                        seen[nn] = len(nodes); nodes.append(nn); q.append(nn)
                        if len(nodes) > max_states:
                            raise RuntimeError("state cap")
                    succ.add(seen[nn])
        if store_edges:
            edges.append((sid, succ))
    return nodes, seen, edges, viol, time.time() - t0


def _v(viol, name, node):
    if name not in viol:
        viol[name] = dict(count=0, example=str(node)[:600])
    viol[name]["count"] += 1


def check_state(node, cfg, viol):
    s, pos, env, clk = node
    nr = sum(1 for b in s.bays if b.mode == C.RAISING)
    if nr > cfg.K:
        _v(viol, f"I1 pulse rule: >{cfg.K} bays RAISING", node)
    if s.os in ("IDLE",) and any(b.mode in (C.LOWERING,) for b in s.bays):
        _v(viol, "I5 lowering while IDLE", node)


def check_transition(s, i, s2, out, cfg, viol, node):
    fwd = {("ALERT", "READY"), ("READY", "DEPLOYING"), ("OPERATE", "STANDDOWN"), ("DEPLOYING", "STANDDOWN"), ("SAFE", "IDLE")}
    if (s.os, s2.os) in fwd and not i.approve:
        _v(viol, "I2 forward OS step without operator approval", node)
    if (i.seismic or i.estop) and s2.os != "SAFE":
        _v(viol, "I6 seismic/estop not -> SAFE", node)
    for k, (b, b2) in enumerate(zip(s.bays, s2.bays)):
        if b2.mode == C.LOWERING and b.mode != C.LOWERING and (i.wind_high or i.seismic or i.estop or not i.comms_ok):
            _v(viol, "I5 lowering started under wind/seismic/estop/comms-loss", node)
        if b2.mode == C.LOWERING and b.mode != C.LOWERING and s2.os not in ("DEPLOYING", "OPERATE"):
            _v(viol, "I5 lowering started outside DEPLOYING/OPERATE", node)
        # bounded response to a hard dP when the pulse budget is free
        others_raising = any(x.mode == C.RAISING for j, x in enumerate(s.bays) if j != k)
        if b.mode == C.DOWN and i.bays[k].dp == 2 and not others_raising:
            hard = [j for j, x in enumerate(s.bays) if x.mode in (C.DOWN, C.LOWERING) and i.bays[j].dp == 2]
            lead = min(hard, key=lambda j: (j - i.clock) % cfg.n) if hard else k
            if i.comms_ok and lead == k and b2.mode != C.RAISING:
                _v(viol, "I8 hard dP with free budget not raised in same scan (comms OK)", node)
            if (not i.comms_ok) and i.clock % cfg.n == k and b2.mode != C.RAISING:
                _v(viol, "I8b hard dP not raised in own TDMA slot (comms lost)", node)
        if b.mode == C.FAULT and b2.mode != C.FAULT:
            _v(viol, "I9 FAULT not latched", node)
        if b2.mode == C.FAULT and f"DRUM_STUCK_B{k}" not in out.alarms:
            _v(viol, "I9 FAULT without alarm", node)
    if out.screw_run and (i.turtle or not i.camera_ok):
        _v(viol, "I3 screw runs with turtle/camera fault", node)


def liveness(nodes, edges, cfg):
    """EF goal: OS IDLE, all non-fault bays UP. Backward reachability."""
    pred = [[] for _ in nodes]
    nsucc = [0] * len(nodes)
    for sid, succ in edges:
        nsucc[sid] = len(succ)
        for t in succ:
            pred[t].append(sid)
    goal = [i for i, (s, pos, env, clk) in enumerate(nodes)
            if s.os == "IDLE" and all(b.mode in (C.UP, C.FAULT) for b in s.bays)]
    can = set(goal)
    q = deque(goal)
    while q:
        t = q.popleft()
        for p in pred[t]:
            if p not in can:
                can.add(p); q.append(p)
    dead = [i for i in range(len(nodes)) if nsucc[i] == 0]
    stuck = [i for i in range(len(nodes)) if i not in can]
    return len(goal), len(stuck), len(dead), [str(nodes[i])[:400] for i in stuck[:3]]


def mc3():
    """Wildlife + outlet exhaustive table."""
    cfg = C.Config(n=1)
    bad = []
    n = 0
    scores = (0.0, 0.3, 0.45, 0.5, 0.9)
    for os_ in C.OS_STATES:
        for prev in ("A", "B", "RECOVER"):
            for fresh, sa, sb, turtle, cam in itertools.product((True, False), repeat=5):
                for sc in itertools.product(scores, repeat=2):
                    s = C.State(os=os_, bays=(C.Bay(),), outlet=prev)
                    i = C.Inputs(bays=(C.BayIn(),), turtle=turtle, camera_ok=cam, fc_fresh=fresh, fc_safe=(sa, sb), fc_score=sc)
                    s2, o = C.step(s, i, cfg)
                    n += 1
                    if o.screw_run and (turtle or not cam):
                        bad.append(("screw", i))
                    if (turtle or not cam) and not o.diverter_to_chute:
                        bad.append(("diverter", i))
                    safe = [x for x, ok in zip("AB", (sa, sb)) if ok]
                    if o.outlet not in safe + ["RECOVER"]:
                        bad.append(("unsafe outlet", i))
                    if o.outlet in ("A", "B") and o.outlet not in safe:
                        bad.append(("unsafe outlet", i))
                    if (not fresh or not safe) and o.outlet != "RECOVER":
                        bad.append(("stale/no-safe not RECOVER", i))
                    if fresh and safe and o.outlet == "RECOVER":
                        bad.append(("RECOVER with safe outlet", i))
                    if fresh and safe and prev in safe and o.outlet != prev:
                        best = max(safe, key=lambda x: sc["AB".index(x)])
                        if sc["AB".index(best)] <= sc["AB".index(prev)] + cfg.hysteresis:
                            bad.append(("flapping", i))
    return n, bad


def mc4(nodes, cfg):
    """Forecast/twin inputs never change bay commands or OS state."""
    diffs = 0
    checked = 0
    fc_variants = [(True, (True, True), (0.9, 0.1)), (False, (False, False), (0.0, 0.0)), (True, (False, True), (0.1, 0.9))]
    for (s, pos, env, clk) in nodes:
        for ev in ("none", "approve"):
            base = None
            for fresh, safe, sc in fc_variants:
                inp = C.Inputs(bays=tuple(C.BayIn(dp=2 if k == 0 else 0, pos=p) for k, p in enumerate(pos)),
                               approve=ev == "approve", seismic=env[0], wind_high=env[1], comms_ok=env[2], clock=clk,
                               fc_fresh=fresh, fc_safe=safe, fc_score=sc)
                s2, o = C.step(s, inp, cfg)
                sig = (o.cmd, s2.os, tuple(b.mode for b in s2.bays))
                if base is None:
                    base = sig
                elif sig != base:
                    diffs += 1
                checked += 1
    return checked, diffs


def main():
    report = {}
    # MC1a: full OS, all events, all bay inputs, n=1
    for tag, cfg, ev, bi in (("MC1a n=1 all events/inputs", C.Config(n=1, K=1, L=2, pers=2, to=2, dwell=1), EVENTS, BAYIN_CHOICES),
                             ("MC1b n=2 (events: none/alert/approve/standdown+approve/seismic/comms; dp 0/2/cycle)",
                              C.Config(n=2, K=1, L=2, pers=1, to=2, dwell=1),
                              ("none", "alert", "approve", "standdown+approve", "seismic", "comms"), ((0, False), (2, False), (0, True)))):
        nodes, seen, edges, viol, dt = explore(cfg, events=ev, bayin=bi)
        goal, stuck, dead, ex = liveness(nodes, edges, cfg)
        ntr = sum(len(e[1]) for e in edges)
        report[tag] = dict(cfg=str(cfg), states=len(nodes), distinct_transitions=ntr, seconds=round(dt, 1),
                           violations=viol, goal_states=goal, states_that_cannot_reach_safe_idle=stuck,
                           deadlocks=dead, examples=ex)
        print(tag, len(nodes), "states", ntr, "edges", f"{dt:.1f}s", "viol", list(viol), "stuck", stuck, "dead", dead)
        if tag.startswith("MC1b"):
            chk, diffs = mc4(nodes, cfg)
            report["MC4 IT/OT separation"] = dict(checked=chk, differing=diffs)
            print("MC4", chk, diffs)
    # MC2: pulse rule under comms loss, n=3, OS OPERATE, all bays DOWN start
    mc2 = {}
    for name, cf in (("TDMA only", C.Config(n=3, busy_line=False, tdma=True, to=2)),
                     ("busy-line only", C.Config(n=3, busy_line=True, tdma=False, to=2)),
                     ("TDMA + busy-line", C.Config(n=3, busy_line=True, tdma=True, to=2)),
                     ("none (each LBC free)", C.Config(n=3, busy_line=False, tdma=False, to=2))):
            nd, _, _, v, dt = explore(cf, events=("none",), bayin=((0, False), (2, False)), init_os="OPERATE",
                                      init_env=(False, False, False), init_mode=C.DOWN, init_pos=2, store_edges=False)
            pulse = v.get(f"I1 pulse rule: >{cf.K} bays RAISING")
            mc2[name] = dict(states=len(nd), pulse_violations=pulse["count"] if pulse else 0,
                             counterexample=pulse["example"] if pulse else None,
                             other_violations=[k for k in v if not k.startswith("I1")])
            print("MC2", name, len(nd), "pulse viol", mc2[name]["pulse_violations"], mc2[name]["other_violations"])
    report["MC2"] = mc2
    n3, bad = mc3()
    report["MC3"] = dict(cases=n3, violations=len(bad), examples=[str(b)[:300] for b in bad[:3]])
    print("MC3", n3, len(bad))
    (HERE / "out").mkdir(exist_ok=True)
    json.dump(report, open(HERE / "out" / "model_check.json", "w"), indent=2, default=str)
    return report


if __name__ == "__main__":
    main()
