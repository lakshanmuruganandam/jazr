"""One JAZR gantry bay: 2 piles + box girder + drum frame (2 posts + drum core).

Coordinates: x along the screen/gantry line, y normal to the screen (through-screen flow
direction), z up, z=0 at MSL. The screen sits at 11 deg to the lane flow [V3], so the lane
current is mostly along x (cos 11) with a small normal component (sin 11).
"""
import numpy as np
from . import params as P
from .fe3d import Frame, Section


def wave_number(T, d):
    w = 2 * np.pi / T
    k = w**2 / P.G
    for _ in range(100):
        k = w**2 / (P.G * np.tanh(k * d))
    return k


def build(fixity_D=P.PILE_FIXITY_DEPTH_D, seg=0.5, deployed=True):
    f = Frame()
    pile = Section.chs(P.PILE_D, P.PILE_T, P.STEEL, "pile CHS1016x22(eff)")
    gird = Section.box(P.GIRDER_H, P.GIRDER_B, P.GIRDER_T, P.STEEL, "girder box 800x600x20")
    post = Section.box(P.POST_B, P.POST_B, P.POST_T, P.DUPLEX, "post SHS300x12 2205")
    drum = Section.chs(P.DRUM_D, P.DRUM_T, P.DUPLEX, "drum CHS610x10 2205")
    z_fix = P.SEABED_Z - fixity_D * P.PILE_D
    D_eff = P.PILE_D + 2 * P.MARINE_GROWTH
    Di = P.PILE_D - 2 * P.PILE_T

    def madd(z):
        if z > 0 or z < P.SEABED_Z:
            return 0.0  # above MSL or in soil (soil mass ignored)
        return P.RHO_W * np.pi / 4 * (D_eff**2 + Di**2)  # Ca=1 added + entrained water

    n_p = int(round((P.DECK_Z - z_fix) / seg))
    p1 = f.line((0, 0, z_fix), (0, 0, P.DECK_Z), n_p, pile, ref=np.array([1.0, 0, 0]), madd_fn=madd)
    p2 = f.line((P.BAY_W, 0, z_fix), (P.BAY_W, 0, P.DECK_Z), n_p, pile, ref=np.array([1.0, 0, 0]), madd_fn=madd)
    f.fix(p1[0]); f.fix(p2[0])
    ng = int(round(P.BAY_W / seg))
    g = f.line((0, 0, P.DECK_Z), (P.BAY_W, 0, P.DECK_Z), ng, gird, ref=np.array([0, 0, 1.0]), n1=p1[-1], n2=p2[-1])
    xpost = [0.5, P.BAY_W - 0.5]
    gx = {round(f.nodes[i][0], 6): i for i in g}
    posts = []
    for xp in xpost:
        base = gx[round(xp, 6)]
        posts.append(f.line((xp, 0, P.DECK_Z), (xp, 0, P.DRUM_Z), 3, post, ref=np.array([1.0, 0, 0]), n1=base))
    nd = int(round((xpost[1] - xpost[0]) / seg))
    d = f.line((xpost[0], 0, P.DRUM_Z), (xpost[1], 0, P.DRUM_Z), nd, drum, ref=np.array([0, 0, 1.0]),
               n1=posts[0][-1], n2=posts[1][-1])
    # lumped masses
    f.add_mass(posts[0][-1], P.DRIVE_MASS)
    mesh_mass = P.MESH_AREAL_MASS * P.BAY_W * P.MESH_DROP + P.BOTTOM_BAR_MASS_PER_M * P.BAY_W
    for i in d:
        f.add_mass(i, mesh_mass / len(d))
    furn = (P.DECK_FURNITURE / P.G) * P.BAY_W
    for i in g:
        f.add_mass(i, furn / len(g))
    groups = dict(pile1=p1, pile2=p2, girder=g, post1=posts[0], post2=posts[1], drum=d)
    secs = dict(pile=pile, girder=gird, post=post, drum=drum)
    return f, groups, secs, dict(z_fix=z_fix, D_eff=D_eff, mesh_mass=mesh_mass)


def elem_group(f, groups):
    """Map element index -> group name."""
    node_group = {}
    for name, ids in groups.items():
        for i in ids:
            node_group.setdefault(i, set()).add(name)
    out = []
    for e in f.elems:
        a = node_group.get(e["n1"], set()); b = node_group.get(e["n2"], set())
        common = (a & b) or a or b
        nm = sorted(common)[0]
        out.append(nm.rstrip("12") if nm.startswith(("pile", "post")) else nm)
    return out


# ---------------- load builders ----------------
def _add_line_load(f, F, nodes_seq, wfun):
    """wfun(z or x, node) -> global force per unit length (3,). Lumped half to each end."""
    for a, b in zip(nodes_seq[:-1], nodes_seq[1:]):
        pa, pb = f.nodes[a], f.nodes[b]
        L = np.linalg.norm(pb - pa)
        w = np.asarray(wfun(0.5 * (pa + pb)), float)
        F[6 * a:6 * a + 3] += w * L / 2
        F[6 * b:6 * b + 3] += w * L / 2


def load_dead(f, groups):
    F = np.zeros(f.ndof)
    for e in f.elems:
        L, _ = f._geom(e)
        W = e["sec"].mat["rho"] * e["sec"].A * L * P.G
        F[6 * e["n1"] + 2] -= W / 2
        F[6 * e["n2"] + 2] -= W / 2
    for n, m in f.lumped.items():
        F[6 * n + 2] -= m * P.G
    return F


def load_live(f, groups):
    F = np.zeros(f.ndof)
    _add_line_load(f, F, groups["girder"], lambda p: (0, 0, -P.LIVE_WALKWAY))
    return F


def rollup_tension(dp):
    A = P.BAY_W * (P.HAT_Z - P.SEABED_Z)
    Wsub = (P.MESH_AREAL_MASS * P.BAY_W * P.MESH_DROP + P.BOTTOM_BAR_MASS_PER_M * P.BAY_W) * P.G * (1 - P.RHO_W / 7800)
    return 1.3 * (Wsub + P.RAIL_FRICTION * dp * A)  # 1.3 dynamic/start-up factor [ENG]


def load_rollup(f, groups, dp):
    F = np.zeros(f.ndof)
    T = rollup_tension(dp)
    d = groups["drum"]
    for i in d:
        F[6 * i + 2] -= T / len(d)
    return F


def load_screen_dp(f, groups, dp, wl=P.HAT_Z, sag=P.MEMBRANE_SAG_RATIO, unbalanced=True):
    """Mesh as a membrane spanning between the two pile rails.
    Normal load (y): dp*BAY_W/2 per m on each pile. Membrane end pull (x, inward): dp*L/(8 sag/L) per m.
    unbalanced=True: neighbour bays rolled up (one-bay cycling / end bay) -> pull not cancelled."""
    F = np.zeros(f.ndof)
    qn = dp * P.BAY_W / 2
    qx = dp * P.BAY_W / (8 * sag) if unbalanced else 0.0

    def mk(sign):
        return lambda p: (sign * qx, qn, 0) if P.SEABED_Z <= p[2] <= wl else (0, 0, 0)
    _add_line_load(f, F, groups["pile1"], mk(+1))
    _add_line_load(f, F, groups["pile2"], mk(-1))
    return F


def morison_profile(H, T, d, U, phase, Deff, Cd=P.CD_PILE, Cm=P.CM_PILE, nz=60):
    """Linear wave + Wheeler stretching + current. Returns (z array rel. MSL-at-WL, force/len array)."""
    k = wave_number(T, d)
    w = 2 * np.pi / T
    eta = H / 2 * np.cos(phase)
    zs = np.linspace(-d, eta, nz)
    zp = (zs - eta) * d / (d + eta)  # Wheeler
    u = w * H / 2 * np.cosh(k * (zp + d)) / np.sinh(k * d) * np.cos(phase) + U
    a = w**2 * H / 2 * np.cosh(k * (zp + d)) / np.sinh(k * d) * np.sin(phase)
    fz = 0.5 * P.RHO_W * Cd * Deff * u * np.abs(u) + P.RHO_W * Cm * np.pi * Deff**2 / 4 * a
    return zs, fz


def load_wave_current(f, groups, H, T, wl, U, direction_deg, Deff, nphase=36):
    """Returns the load vector at the phase of max total base shear (both piles in phase:
    10 m spacing << wavelength assumption gives conservative upper bound)."""
    d = wl - P.SEABED_Z
    best, Fbest = -1, None
    th = np.radians(direction_deg)
    for ph in np.linspace(0, 2 * np.pi, nphase, endpoint=False):
        zs, fz = morison_profile(H, T, d, U, ph, Deff)
        zabs = zs + wl  # z relative to MSL
        F = np.zeros(f.ndof)
        for gname in ("pile1", "pile2"):
            def w(p, zabs=zabs, fz=fz):
                z = p[2]
                if z < P.SEABED_Z or z > zabs[-1]:
                    return (0, 0, 0)
                q = np.interp(z, zabs, fz)
                return (q * np.cos(th), q * np.sin(th), 0)
            _add_line_load(f, F, groups[gname], w)
        Vb = abs(F[0::6].sum() * np.cos(th) + F[1::6].sum() * np.sin(th))
        if Vb > best:
            best, Fbest = Vb, F
    return Fbest, best


def load_wind(f, groups, V, direction_deg, mesh_exposed_h=0.0, wl=P.HAT_Z):
    """Pressure q = 0.5 rho V^2 (3-s gust used directly, G=0.85 per ASCE 7). Cf: CHS 0.7(sub/super-crit
    mix), box 2.0, drum+rolled mesh+housing as 1.5 m cylinder Cf 1.2, porous mesh Cf 0.6 (porosity 0.64)."""
    q = 0.5 * P.RHO_AIR * V**2 * 0.85
    th = np.radians(direction_deg)
    c, s = np.cos(th), np.sin(th)
    F = np.zeros(f.ndof)
    for gname in ("pile1", "pile2"):
        _add_line_load(f, F, groups[gname], lambda p: (q * 0.7 * P.PILE_D * c, q * 0.7 * P.PILE_D * s, 0)
                       if p[2] > wl else (0, 0, 0))
    # girder: projected width B for x-wind (end-on, small), H for y-wind
    _add_line_load(f, F, groups["girder"], lambda p: (0.0, q * 2.0 * P.GIRDER_H * s, 0))
    _add_line_load(f, F, groups["drum"], lambda p: (0.0, q * 1.2 * 1.5 * s, 0))
    for gname in ("post1", "post2"):
        _add_line_load(f, F, groups[gname], lambda p: (q * 2.0 * P.POST_B * c, q * 2.0 * P.POST_B * s, 0))
    if mesh_exposed_h > 0:  # deployed mesh between water and drum: shared to piles
        qn = q * 0.6 * P.BAY_W / 2 * s
        for gname in ("pile1", "pile2"):
            _add_line_load(f, F, groups[gname], lambda p: (0, qn, 0) if wl < p[2] <= wl + mesh_exposed_h else (0, 0, 0))
    return F
