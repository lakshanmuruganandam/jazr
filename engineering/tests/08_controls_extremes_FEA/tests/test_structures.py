import sys, pathlib
import numpy as np
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "A_structural_FEA"))
from common import gantry as GT, params as P


def test_morison_inertia_matches_hand_calc():
    # small wave, deep-ish: inertia force/length at surface ~ rho Cm pi D^2/4 * w^2 H/2 * coth(kd)
    H, T, d, D = 0.2, 6.0, 7.5, 1.0
    z, f = GT.morison_profile(H, T, d, 0.0, np.pi / 2, D, Cd=0.0, Cm=2.0, nz=200)
    k = GT.wave_number(T, d); w = 2 * np.pi / T
    hand = P.RHO_W * 2.0 * np.pi * D**2 / 4 * w**2 * H / 2 / np.tanh(k * d)
    assert abs(f[-1] / hand - 1) < 0.02


def test_dispersion():
    k = GT.wave_number(8.0, 1000.0)
    assert abs(k / ((2 * np.pi / 8) ** 2 / 9.81) - 1) < 1e-6


def test_gantry_operating_case_passes():
    import run_fea
    f, g, res, extra, _ = run_fea.run_static()
    op = [v for k, v in res.items() if k.startswith("OP1")][0]
    assert op["util_max"] < 1.0


def test_membrane_pull_formula():
    f, g, secs, info = GT.build()
    F = GT.load_screen_dp(f, g, 1000.0, sag=0.05)
    # x-resultant on pile 1 = dp*L/(8*sag) * wetted height
    wet = P.HAT_Z - P.SEABED_Z
    fx1 = sum(F[6 * i] for i in g["pile1"])
    assert abs(fx1 / (1000 * P.BAY_W / 0.4 * wet) - 1) < 0.05
