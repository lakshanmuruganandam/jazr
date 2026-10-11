import sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "E_human_factors")); sys.path.insert(0, str(ROOT / "D_controls"))
from procedures import PROCEDURES, ALARM_RESPONSES
import controller as C

VERBS = {"Acknowledge", "Run", "Press", "Confirm", "Log", "Verify", "Approve"}


def test_every_procedure_step_is_complete_and_single_action():
    for k, p in PROCEDURES.items():
        assert set(p) == {"cue", "action", "check", "time_s", "abort"}, k
        assert p["action"].split()[0] in VERBS, (k, p["action"])
        assert " and " not in p["action"], k
        assert p["time_s"] > 0 and p["abort"]


def test_os_transitions_have_procedures():
    import model_check as M
    nodes, seen, edges, viol, _ = M.explore(C.Config(n=1, K=1, L=2, pers=2, to=2, dwell=1))
    pairs = set()
    for sid, succ in edges:
        for t in succ:
            a, b = nodes[sid][0].os, nodes[t][0].os
            if a != b:
                pairs.add((a, b))
    missing = [p for p in pairs if p not in PROCEDURES and not (p[1] == "SAFE")]
    assert missing == [], missing
