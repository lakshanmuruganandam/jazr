"""Sanity tests on the analysis outputs (physics/arithmetic checks, not biology)."""
import json, os, math
from params import RES, do_sat_mg_L

def load(n):
    return json.load(open(os.path.join(RES, n)))

def test_do_saturation_plausible():
    assert 5.0 < do_sat_mg_L(35.8, 40) < 6.2
    assert 6.5 < do_sat_mg_L(20.0, 35) < 7.8

def test_pipe_residence_and_velocity():
    p = load("t1_jelly_transport.json")["pipe"]["L5000_clean"]
    assert abs(p["v"] - 2.0 / (math.pi * 0.36)) < 1e-6
    assert 45 < p["residence_min"] < 50

def test_oxygen_monotonic_in_biomass():
    c = load("t1_jelly_transport.json")["oxygen"]["cases"]
    assert c["1/m3 extreme, 1 line"]["DO_drop_active_mgL"] > c["0.3/m3 design, 1 line"]["DO_drop_active_mgL"] > c["pilot_peak_35t/h"]["DO_drop_active_mgL"]

def test_stop_distance_grows_with_velocity():
    t = load("t2_wildlife.json")["stop_distance"]["table"]
    assert t["0.70"]["d_screw_stop_m"][1] > t["0.40"]["d_screw_stop_m"][1]

def test_fmea_rpn_consistent():
    import csv
    rows = list(csv.DictReader(open(os.path.join(RES, "t5_fmea.csv"))))
    assert len(rows) >= 30
    for r in rows:
        assert int(r["RPN"]) == int(r["S"]) * int(r["O"]) * int(r["D"])

def test_closed_floor_beats_open_skirt():
    r = load("t8_retention.json")
    for k, v in r.items():
        if isinstance(v, dict) and "open skirt 2 m" in v:
            assert v["JAZR closed floor (seal gap 0-10 cm)"] > v["open skirt 2 m"]

def test_des_crew_hours_lower_than_today():
    r = load("t6_ops_des.json")["crew_hours_per_bloom"]
    for v in r.values():
        assert v["jazr_mean"] < v["today_low_mean"]
