"""dP filter / voting tests (wave spikes, stuck and failed transmitters)."""
import sys, pathlib
import numpy as np
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "D_controls"))
from plant import Sensing, WaveDP


def _trips(sn, true, wave, T):
    prev = np.zeros(sn.n, bool); n = 0
    for t in range(T):
        lvl, _ = sn.read(true + wave.dp(t))
        on = lvl >= 1; n += int((on & ~prev).sum()); prev = on
    return n


def test_filter_rejects_storm_waves():
    wv = WaveDP(15, 2.0, 5.5, seed=3)
    assert _trips(Sensing(15, tau=30, pers=20), 300.0, wv, 3600) == 0
    assert _trips(Sensing(15, raw_mode=True), 300.0, wv, 3600) > 0      # naive design trips


def test_filter_detects_blinding_within_60s():
    wv = WaveDP(15, 1.0, 4.5, seed=4)
    sn = Sensing(15, tau=30, pers=20)
    det = None
    for t in range(600):
        true = 300.0 + (np.clip((t - 100) / 120, 0, 1) * 1200 if t >= 100 else 0)
        lvl, _ = sn.read(true + wv.dp(t))
        if t > 100 and (lvl >= 1).sum() >= 8 and det is None:
            det = t
    t_cross = 100 + 200 / 1200 * 120
    assert det is not None and det - t_cross <= 60


def test_stuck_high_transmitter_masked_by_voting():
    sn = Sensing(3, tau=30, pers=20, hard_vote="2oo2")
    sn.fault[(0, 0)] = ("stuck", 2000.0)
    for t in range(300):
        lvl, _ = sn.read(np.full(3, 50.0))
    assert lvl[0] == 0 and sn.disagree[0]
    sn1 = Sensing(3, tau=30, pers=20, hard_vote="1oo1")
    sn1.fault[(0, 0)] = ("stuck", 2000.0)
    for t in range(300):
        lvl1, _ = sn1.read(np.full(3, 50.0))
    assert lvl1[0] == 2        # single-channel hard trip is fooled
