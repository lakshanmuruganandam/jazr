"""T9 - Bloom Incident OS smoke tests (run: python3 -m pytest -q test_bloom_os.py)."""
import json
import pytest
from bloom_os import BloomOS, TransitionError, IDLE, READY, DEPLOYING, OPERATING, STANDDOWN


def run_to_operating(os_):
    os_.tick(700)
    assert os_.state == OPERATING


def test_distant_alert_end_to_end():
    s = BloomOS()
    s.receive_alert(lead_h=5.0)
    assert s.state == READY                      # waits for a human
    s.tick(3600)
    assert s.state == READY and s.bays[0] == "UP"
    s.approve("deploy", by="shift supervisor")
    assert s.state == DEPLOYING
    run_to_operating(s)
    assert s.dashboard()["bays_down"] == 17 and s.dashboard()["relief_open"]
    s.set_forecast({"outlet_W": True, "outlet_E": False})
    assert s.outlet == "outlet_W" and s.mode == "RELEASE"
    s.approve("standdown", by="shift supervisor")
    assert s.state == STANDDOWN
    s.tick(18 * 95)
    assert s.state == IDLE
    assert s.invariants()
    whos = [e.get("by") for e in s.log if "to" in e]
    assert "shift supervisor" in whos


def test_close_alert_autodeploys_within_15_min():
    s = BloomOS()
    s.receive_alert(lead_h=0.3, level="RED")
    assert s.state == DEPLOYING                  # pre-authorised, no approval wait
    s.tick(15 * 60)
    assert s.state == OPERATING
    assert s.log[-1]["t"] <= 15 * 60
    assert s.invariants()


def test_close_alert_without_preauth_waits():
    s = BloomOS(preauthorised=False)
    s.receive_alert(lead_h=0.3)
    assert s.state == READY


def test_deploy_requires_ready_and_invalid_transitions_rejected():
    s = BloomOS()
    with pytest.raises(TransitionError):
        s.approve("deploy", by="x")
    with pytest.raises(TransitionError):
        s.approve("standdown", by="x")
    s.receive_alert(lead_h=6)
    with pytest.raises(TransitionError):
        s.approve("teleport", by="x")


def test_relief_bay_never_deploys():
    s = BloomOS()
    s.receive_alert(lead_h=0.2)
    s.tick(700)
    assert s.bays[17] == "UP"
    assert s.invariants()


def test_dp_transient_filtered_and_staged_rollup():
    s = BloomOS()
    s.receive_alert(lead_h=0.2); s.tick(700)
    s.bay_dp(3, 900); s.tick(10); s.bay_dp(3, 50); s.tick(60)       # 10 s wave spike
    assert s.bays[3] == "DOWN"
    for b in (1, 2, 4, 5):                                              # 4 bays blind together
        s.bay_dp(b, 900)
    s.tick(40)
    assert sum(1 for v in s.bays.values() if v == "ROLLING_UP") == 1   # one at a time (<1 t pulse)
    s.tick(4 * 95)
    assert s.max_simultaneous_rolling == 1
    assert s.invariants()


def test_turtle_stops_screw_and_restarts_after_clear():
    s = BloomOS()
    s.receive_alert(lead_h=0.2); s.tick(700)
    assert s.screw_running
    s.turtle_detected(entrance=4)
    assert not s.screw_running and s.diverter == "ESCAPE"
    assert s.invariants()
    s.tick(61)
    assert s.screw_running and s.diverter == "BYPASS"


def test_no_safe_outlet_switches_to_recover():
    s = BloomOS()
    s.receive_alert(lead_h=0.2); s.tick(700)
    s.set_forecast({"outlet_W": False, "outlet_E": False})
    assert s.mode == "RECOVER" and s.outlet is None
    s.set_forecast({"outlet_W": False, "outlet_E": True})
    assert s.mode == "RELEASE" and s.outlet == "outlet_E"


def test_dashboard_is_json_and_complete():
    s = BloomOS()
    s.receive_alert(lead_h=5); s.approve("deploy", by="op"); s.tick(700)
    d = s.dashboard()
    for k in ("state", "mode", "bays_down", "relief_open", "screw_running", "diverter", "alert"):
        assert k in d
    assert json.loads(json.dumps(d))["state"] == OPERATING
