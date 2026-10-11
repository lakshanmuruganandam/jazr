"""Verification of the frame solver against closed-form solutions."""
import numpy as np
from common.fe3d import Frame, Section

MAT = dict(E=210e9, G=81e9, rho=7850.0, fy=355e6)


def cantilever(dirn, n=10, L=5.0, axis="z"):
    f = Frame()
    sec = Section.chs(0.5, 0.02, MAT)
    end = (0, 0, L) if axis == "z" else (L, 0, 0)
    ids = f.line((0, 0, 0), end, n, sec)
    f.fix(ids[0])
    return f, ids, sec, L


def test_cantilever_tip_deflection_both_planes():
    for axis in ("z", "x"):
        for d in (0, 1, 2):
            f, ids, sec, L = cantilever(d, axis=axis)
            if (axis == "z" and d == 2) or (axis == "x" and d == 0):
                continue  # axial
            F = np.zeros(f.ndof); F[6 * ids[-1] + d] = 1e4
            u = f.solve(F)
            exact = 1e4 * L**3 / (3 * MAT["E"] * sec.Iy)
            assert abs(u[6 * ids[-1] + d] / exact - 1) < 1e-6


def test_axial_and_torsion():
    f, ids, sec, L = cantilever(0)
    F = np.zeros(f.ndof); F[6 * ids[-1] + 2] = 1e5; F[6 * ids[-1] + 5] = 1e3
    u = f.solve(F)
    assert abs(u[6 * ids[-1] + 2] / (1e5 * L / (MAT["E"] * sec.A)) - 1) < 1e-9
    assert abs(u[6 * ids[-1] + 5] / (1e3 * L / (MAT["G"] * sec.J)) - 1) < 1e-9


def test_cantilever_root_moment_stress():
    f, ids, sec, L = cantilever(0)
    F = np.zeros(f.ndof); F[6 * ids[-1] + 0] = 1e4
    u = f.solve(F)
    s, _ = f.stresses(u)
    assert abs(s[0] / (1e4 * L / sec.Wy) - 1) < 1e-6


def test_cantilever_first_frequency():
    f, ids, sec, L = cantilever(0, n=40)
    fr, *_ = f.modal(2)
    m = MAT["rho"] * sec.A
    exact = 1.8751**2 / (2 * np.pi) * np.sqrt(MAT["E"] * sec.Iy / (m * L**4))
    assert abs(fr[0] / exact - 1) < 0.01


def test_tip_mass_frequency():
    f, ids, sec, L = cantilever(0, n=20)
    f.add_mass(ids[-1], 5e4)
    fr, *_ = f.modal(1)
    k = 3 * MAT["E"] * sec.Iy / L**3
    exact = np.sqrt(k / (5e4 + 0.2357 * MAT["rho"] * sec.A * L)) / (2 * np.pi)
    assert abs(fr[0] / exact - 1) < 0.01


def test_euler_buckling_cantilever():
    f, ids, sec, L = cantilever(0, n=20)
    F = np.zeros(f.ndof); F[6 * ids[-1] + 2] = -1.0e6
    u = f.solve(F)
    lam = f.buckling(u, 1)[0]
    Pcr = np.pi**2 * MAT["E"] * sec.Iy / (4 * L**2)
    assert abs(lam * 1e6 / Pcr - 1) < 0.01


def test_portal_frame_sway_matches_stiffness_method():
    # fixed-base portal, rigid-ish beam -> sway stiffness 2*12EI/h^3
    f = Frame()
    col = Section.chs(0.5, 0.02, MAT)
    beam = Section(1e3, 1e4, 1e4, 1e4, MAT, Wy=1, Wz=1)  # near-rigid beam
    a = f.line((0, 0, 0), (0, 0, 4), 8, col)
    b = f.line((6, 0, 0), (6, 0, 4), 8, col)
    f.line((0, 0, 4), (6, 0, 4), 6, beam, n1=a[-1], n2=b[-1])
    f.fix(a[0]); f.fix(b[0])
    F = np.zeros(f.ndof); F[6 * a[-1]] = 1e5
    u = f.solve(F)
    exact = 1e5 / (2 * 12 * MAT["E"] * col.Iy / 4**3)
    assert abs(u[6 * a[-1]] / exact - 1) < 0.01
