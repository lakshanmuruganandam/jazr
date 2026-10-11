"""Controller verification: model checking (reduced sizes for speed), truth tables, unit tests, smoke sim."""
import sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "D_controls"))
import controller as C
import model_check as M


def test_mc_full_os_single_bay_no_violation_and_live():
    cfg = C.Config(n=1, K=1, L=2, pers=2, to=2, dwell=1)
    nodes, seen, edges, viol, _ = M.explore(cfg)
    assert viol == {}, viol
    goal, stuck, dead, _ = M.liveness(nodes, edges, cfg)
    assert stuck == 0 and dead == 0 and goal > 0


def _pulse(cfg):
    nd, _, _, v, _ = M.explore(cfg, events=("none",), bayin=((0, False), (2, False)), init_os="OPERATE",
                               init_env=(False, False, False), init_mode=C.DOWN, init_pos=2, store_edges=False)
    return v.get(f"I1 pulse rule: >{cfg.K} bays RAISING")


def test_comms_loss_pulse_rule_needs_tdma_and_busy_line():
    assert _pulse(C.Config(n=2, busy_line=True, tdma=True, to=2)) is None
    assert _pulse(C.Config(n=2, busy_line=False, tdma=True, to=2)) is not None   # TDMA alone fails (slow drums overlap)
    assert _pulse(C.Config(n=2, busy_line=True, tdma=False, to=2)) is not None   # busy line alone races


def test_wildlife_and_outlet_truth_table():
    n, bad = M.mc3()
    assert n > 10000 and bad == []


def test_forecast_cannot_command_bays():
    cfg = C.Config(n=1, K=1, L=2, pers=2, to=2, dwell=1)
    nodes, *_ = M.explore(cfg, store_edges=False)
    chk, diffs = M.mc4(nodes, cfg)
    assert chk > 0 and diffs == 0


def test_seismic_forces_safe_and_raise():
    cfg = C.Config(n=3)
    s = C.initial(cfg)._replace(os="OPERATE", bays=tuple(C.Bay(mode=C.DOWN, pos_prev=2) for _ in range(3)))
    s2, o = C.step(s, C.Inputs(bays=tuple(C.BayIn(pos=2) for _ in range(3)), seismic=True), cfg)
    assert s2.os == "SAFE" and o.cmd.count("UP") == 1 and "SEISMIC_TRIP" in o.alarms


def test_outlet_hysteresis_and_recover():
    cfg = C.Config(n=1)
    s = C.initial(cfg)._replace(outlet="A")
    b = (C.BayIn(),)
    s2, o = C.step(s, C.Inputs(bays=b, fc_score=(0.5, 0.55)), cfg)
    assert o.outlet == "A"                       # 0.05 < hysteresis
    s2, o = C.step(s, C.Inputs(bays=b, fc_score=(0.5, 0.7)), cfg)
    assert o.outlet == "B"
    s2, o = C.step(s, C.Inputs(bays=b, fc_fresh=False), cfg)
    assert o.outlet == "RECOVER"
    s2, o = C.step(s, C.Inputs(bays=b, fc_safe=(False, False)), cfg)
    assert o.outlet == "RECOVER"


def test_smoke_sim_deploy_time_and_turtle():
    import faultsim as FS
    m, log, ev = FS.run(hours=0.5, faults=False, surge=False)
    assert m["deploy_time_s"] is not None and m["deploy_time_s"] + 120 <= 600   # alert -> OPERATE <= 10 min
    assert m["screw_with_turtle_or_camfault_s"] == 0
