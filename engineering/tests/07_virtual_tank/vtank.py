"""
JAZR Gate v3 -- VIRTUAL TANK (tank-scale twin of the physical protocols T01-T16)
=================================================================================
*** SIMULATED virtual tank -- not physical evidence. ***

Model (all SI units, MODEL scale ~1:20 Froude):
  * Plan-view tank 1.5 m x 0.4 m, water depth H = 0.25 m (2.5-D: depth-uniform flow,
    particles carry a vertical coordinate z for buoyancy / gaps / waves).
  * Flow: steady potential (Darcy-form) flow  div(G grad phi) = sources  on a
    finite-volume grid.  Thin walls = zero-conductance cell links, the roll-down
    mesh = resistive links (resistance length ell_s, raised by blinding), outer
    guide curtain = partially open links, bypass entrances = volumetric sinks,
    intake = fixed-potential outflow, pump = uniform inflow.  Re-solved when
    blinding changes (two-way coupling) or bays are lifted.
  * Particles (bells, fragments, turtle, fish beads): finite-size spheres with
    Maxey-Riley-type dynamics (fluid acceleration + added mass + Re-dependent
    drag), OU turbulence, buoyant settling, soft DEM contacts between particles,
    Coulomb friction/adhesion + mesh pressure load on the screen, extrusion through
    the mesh by a Cauchy-number criterion, passage under/over gaps.
"""
import numpy as np
import scipy.sparse as sp
from scipy.sparse.linalg import spsolve
from scipy.spatial import cKDTree
from dataclasses import dataclass, replace, asdict

RHO = 1000.0
GRAV = 9.81
MU = 1.0e-3
NU = MU / RHO
LABEL = "SIMULATED virtual tank - not physical evidence"

# status codes
ACTIVE, INTAKE, BYPASS, EXIT_DOWN, EXIT_UP = 0, 1, 2, 3, 4
KIND_BELL, KIND_FRAG, KIND_TURTLE, KIND_FISH = 0, 1, 2, 3


def K_mesh(beta):
    """Wire-mesh head-loss coefficient vs open-area ratio (Idelchik-type, high Re)."""
    beta = np.clip(beta, 0.02, 1.0)
    return 1.3 * (1 - beta) + (1.0 / beta - 1.0) ** 2


def cd_sphere(Re):
    Re = np.maximum(Re, 1e-6)
    return 24.0 / Re * (1 + 0.15 * Re ** 0.687) + 0.42 / (1 + 42500.0 / Re ** 1.16)


def settling_velocity(drho, d, vol, area, cd_mult=1.0):
    """Terminal vertical velocity (positive = sinking) by fixed-point on Cd(Re)."""
    drho = np.asarray(drho, float)
    w = np.full_like(drho, 1e-3)
    for _ in range(40):
        Re = np.abs(w) * d / NU
        cd = cd_sphere(Re) * cd_mult
        w = np.sqrt(2 * np.abs(drho) * GRAV * vol / (RHO * cd * area))
    return np.sign(drho) * w


@dataclass
class Params:
    # ---- tank / geometry ----
    Lx: float = 1.5
    Ly: float = 0.4
    H: float = 0.25
    dx: float = 0.005
    layout: str = "lane"          # 'lane' (training-walled lane + inner screen) or 'open'
    U: float = 0.11               # approach speed, m/s  (0.5 m/s prototype / sqrt(20))
    y_lo: float = 0.14            # training walls -> 16 cm lane
    y_up: float = 0.30
    x_s: float = 0.25             # screen toe
    screen: bool = True           # bays down?
    theta_deg: float = 11.0
    n_bays: int = 4
    gap_w: float = 0.06           # downstream bypass entrance (gap between screen end and wall)
    pocket_len: float = 0.06
    n_mid_slots: int = 1          # extra entrances in the face (1 -> "2 bypass slots")
    slot_w: float = 0.05
    bypass_frac: float = 0.10     # total bypass flow / lane flow
    ell_s: float = 0.05           # screen resistance length (calibration parameter)
    beta: float = 0.5             # mesh open-area ratio
    mesh_mm: float = 5.0
    freeboard: float = 0.02
    bottom_gap: float = 0.001     # seated bottom bar gap (m)
    # ---- outer guide curtain (open layout) ----
    curtain: bool = False
    curtain_angle: float = 20.0
    curtain_len: float = 0.45
    curtain_cx: float = 0.75
    curtain_cy: float = 0.20
    curtain_zlo: float = 0.03
    curtain_zhi: float = 0.19
    curtain_draw: float = 0.5     # vertical draw toward gaps while pressed on curtain
    # ---- particle physics ----
    mu_f: float = 0.4             # bell-mesh Coulomb friction
    adhesion: float = 0.0         # Pa, mucus/gel adhesion to mesh
    E: float = 5000.0             # bell Young's modulus, Pa (gel surrogate)
    cd_mult: float = 1.0
    Cm: float = 0.5               # added-mass coefficient
    turb_I: float = 0.10          # turbulence intensity (fraction of local speed)
    turb_s0: float = 0.003        # background velocity noise, m/s
    TL: float = 0.5               # Lagrangian integral time, s
    c_ext: float = 1.0            # extrusion pressure factor
    squeeze_max: float = 0.3      # max fractional squeeze through gaps
    mu_floor: float = 0.3
    dt: float = 0.01
    rho_sd_scale: float = 1.0     # scale on surrogate density scatter (T01 model)


# ----------------------------------------------------------------------------------
class Seg:
    def __init__(self, p0, p1, kind, bay=-1, s0=0.0):
        self.p0 = np.asarray(p0, float)
        self.p1 = np.asarray(p1, float)
        d = self.p1 - self.p0
        self.L = float(np.hypot(*d))
        self.t = d / self.L
        self.n = np.array([-self.t[1], self.t[0]])
        self.kind, self.bay, self.s0 = kind, bay, s0


class Geometry:
    def __init__(self, P: Params):
        self.P = P
        self.walls, self.screens, self.curtains = [], [], []
        self.mid_slots = []          # arclength positions along the screen
        if P.layout == "lane":
            th = np.radians(P.theta_deg)
            self.t = np.array([np.cos(th), np.sin(th)])
            self.n = np.array([-np.sin(th), np.cos(th)])   # +n = front (upstream) side
            self.S = np.array([P.x_s, P.y_lo])
            self.Ls = (P.y_up - P.gap_w - P.y_lo) / np.sin(th)
            self.E = self.S + self.Ls * self.t
            self.walls.append(Seg((0, P.y_up), (P.Lx, P.y_up), "wall"))
            self.walls.append(Seg((0, P.y_lo), (P.Lx, P.y_lo), "wall"))
            ex = self.E[0] + P.pocket_len
            self.walls.append(Seg(self.E, (ex, self.E[1]), "wall"))
            self.walls.append(Seg((ex, self.E[1]), (ex, P.y_up), "wall"))
            for k in range(P.n_bays):
                a, b = k * self.Ls / P.n_bays, (k + 1) * self.Ls / P.n_bays
                self.screens.append(Seg(self.S + a * self.t, self.S + b * self.t, "screen", k, a))
            m = P.n_mid_slots
            self.mid_slots = [self.Ls * (i + 1) / (m + 1) for i in range(m)]
            self.pocket = (self.E[0] - 0.005, ex, self.E[1], P.y_up)
        else:
            if P.curtain:
                a = np.radians(P.curtain_angle)
                c = np.array([P.curtain_cx, P.curtain_cy])
                h = 0.5 * P.curtain_len * np.array([np.cos(a), np.sin(a)])
                self.curtains.append(Seg(c - h, c + h, "curtain"))

    def all_segments(self):
        return self.walls + self.screens + self.curtains


def links_crossed(seg, dx, nx, ny):
    """Cell links (axis, i, j, s) crossed by a segment; axis 0 = x-link (i,j)-(i+1,j)."""
    out = []
    (x0, y0), (x1, y1) = seg.p0, seg.p1
    if abs(y1 - y0) > 1e-12:
        for j in range(ny):
            yc = (j + 0.5) * dx
            if min(y0, y1) <= yc < max(y0, y1):
                f = (yc - y0) / (y1 - y0)
                xs = x0 + f * (x1 - x0)
                i = int(np.floor(xs / dx - 0.5))
                if 0 <= i < nx - 1:
                    out.append((0, i, j, f * seg.L))
    if abs(x1 - x0) > 1e-12:
        for i in range(nx):
            xc = (i + 0.5) * dx
            if min(x0, x1) <= xc < max(x0, x1):
                f = (xc - x0) / (x1 - x0)
                ys = y0 + f * (y1 - y0)
                j = int(np.floor(ys / dx - 0.5))
                if 0 <= j < ny - 1:
                    out.append((1, i, j, f * seg.L))
    return out


# ----------------------------------------------------------------------------------
class Flow:
    """Potential flow with resistive screen links on a uniform FV grid."""

    BIN = 0.01   # screen coverage bin (m along the face)

    def __init__(self, P: Params, geom: Geometry):
        self.P, self.g = P, geom
        dx = P.dx
        nx, ny = int(round(P.Lx / dx)), int(round(P.Ly / dx))
        self.nx, self.ny, self.dx = nx, ny, dx
        self.xc = (np.arange(nx) + 0.5) * dx
        self.yc = (np.arange(ny) + 0.5) * dx
        self.Gx0 = np.ones((nx - 1, ny))
        self.Gy0 = np.ones((nx, ny - 1))
        for s in geom.walls:
            for ax, i, j, _ in links_crossed(s, dx, nx, ny):
                (self.Gx0 if ax == 0 else self.Gy0)[i, j] = 0.0
        for s in geom.curtains:
            fo = 1.0 - (P.curtain_zhi - P.curtain_zlo) / P.H
            for ax, i, j, _ in links_crossed(s, dx, nx, ny):
                (self.Gx0 if ax == 0 else self.Gy0)[i, j] = fo
        # screen links
        sl = []
        for s in geom.screens:
            for ax, i, j, ss in links_crossed(s, dx, nx, ny):
                e = np.array([1.0, 0.0]) if ax == 0 else np.array([0.0, 1.0])
                orient = -np.sign(e @ geom.n)      # +1: link direction goes front->behind
                sl.append((ax, i, j, ss + s.s0, s.bay, orient))
        self.scr = np.array(sl, float).reshape(-1, 6)
        if len(sl):
            self.nbins = int(np.ceil(geom.Ls / self.BIN))
            self.scr_bin = np.clip((self.scr[:, 3] / self.BIN).astype(int), 0, self.nbins - 1)
            gap = np.zeros(len(sl), bool)
            for sm in geom.mid_slots:
                gap |= np.abs(self.scr[:, 3] - sm) < P.slot_w / 2
            self.scr_gap = gap
        else:
            self.nbins = 0
        # sources / BCs
        X, Y = np.meshgrid(self.xc, self.yc, indexing="ij")
        if P.layout == "lane":
            self.inflow = (self.yc > P.y_lo) & (self.yc < P.y_up)
            self.outflow = (self.yc > P.y_lo) & (self.yc < P.y_up)
            qlane = P.U * (P.y_up - P.y_lo)
            nslot = 1 + len(geom.mid_slots)
            self.q_slot = P.bypass_frac * qlane / nslot
            self.sinks = []
            x0, x1, y0, y1 = geom.pocket
            m = (X > geom.E[0]) & (X < x1) & (Y > y0) & (Y < y1)
            self.sinks.append(m)
            for sm in geom.mid_slots:
                rel = np.stack([X - geom.S[0], Y - geom.S[1]], -1)
                sa = rel @ geom.t
                na = rel @ geom.n
                m = (np.abs(sa - sm) < P.slot_w / 2) & (na > 0) & (na < 0.6 * P.slot_w)
                self.sinks.append(m)
        else:
            self.inflow = np.ones(ny, bool)
            self.outflow = np.ones(ny, bool)
            self.sinks, self.q_slot = [], 0.0
        self.cov = np.zeros(max(self.nbins, 1))
        self.raised = np.zeros(P.n_bays, bool) if P.screen else np.ones(P.n_bays, bool)
        self.solve()

    # ------------------------------------------------------------------
    def screen_G(self):
        P = self.P
        b = self.cov[self.scr_bin]
        G = 1.0 / (1.0 + P.ell_s / (self.dx * np.maximum(1 - b, 0.02)))
        bay = self.scr[:, 4].astype(int)
        G = np.where(self.raised[bay], 1.0, G)
        G = np.where(self.scr_gap, 0.0, G)
        return G

    def solve(self):
        P, nx, ny, dx = self.P, self.nx, self.ny, self.dx
        Gx, Gy = self.Gx0.copy(), self.Gy0.copy()
        if self.nbins:
            G = self.screen_G()
            ax = self.scr[:, 0].astype(int)
            ii, jj = self.scr[:, 1].astype(int), self.scr[:, 2].astype(int)
            Gx[ii[ax == 0], jj[ax == 0]] = G[ax == 0]
            Gy[ii[ax == 1], jj[ax == 1]] = G[ax == 1]
            self._Gs = G
        idx = np.arange(nx * ny).reshape(nx, ny)
        r, c, d = [], [], []
        for Pi, Ni, g in ((idx[:-1, :], idx[1:, :], Gx), (idx[:, :-1], idx[:, 1:], Gy)):
            Pi, Ni, g = Pi.ravel(), Ni.ravel(), g.ravel()
            r += [Pi, Ni, Pi, Ni]; c += [Pi, Ni, Ni, Pi]; d += [g, g, -g, -g]
        diag = np.full(nx * ny, 1e-10)
        diag[idx[-1, self.outflow]] += 2.0
        r.append(np.arange(nx * ny)); c.append(np.arange(nx * ny)); d.append(diag)
        A = sp.csr_matrix((np.concatenate(d), (np.concatenate(r), np.concatenate(c))),
                          shape=(nx * ny, nx * ny))
        b = np.zeros((nx, ny))
        b[0, self.inflow] += P.U * dx
        bs = np.zeros((nx, ny))
        for m in self.sinks:
            bs[m] -= self.q_slot / m.sum()
        b = b + bs
        phi = spsolve(A.tocsc(), b.ravel(), permc_spec="MMD_AT_PLUS_A").reshape(nx, ny)
        self.phi = phi
        ux = np.zeros((nx + 1, ny)); uy = np.zeros((nx, ny + 1))
        ux[1:-1] = Gx * (phi[:-1] - phi[1:]) / dx
        ux[0, self.inflow] = P.U
        ux[-1, self.outflow] = 2 * phi[-1, self.outflow] / dx
        uy[:, 1:-1] = Gy * (phi[:, :-1] - phi[:, 1:]) / dx
        self.ux_f, self.uy_f = ux, uy
        u = 0.5 * (ux[:-1] + ux[1:]); v = 0.5 * (uy[:, :-1] + uy[:, 1:])
        dudx, dudy = np.gradient(u, dx); dvdx, dvdy = np.gradient(v, dx)
        a_x = np.clip(u * dudx + v * dudy, -0.5, 0.5)
        a_y = np.clip(u * dvdx + v * dvdy, -0.5, 0.5)
        self.F = np.stack([u, v, a_x, a_y])
        # mass balance
        self.Q_in = P.U * dx * self.inflow.sum()
        self.Q_out = (2 * phi[-1, self.outflow]).sum()
        self.Q_sink = self.q_slot * len(self.sinks)
        div = (ux[1:] - ux[:-1] + uy[:, 1:] - uy[:, :-1]) * dx - bs
        self.max_cell_residual = float(np.abs(div).max())
        # per-bin through-flow (normal velocity, m/s depth-averaged)
        if self.nbins:
            ax = self.scr[:, 0].astype(int); ii = self.scr[:, 1].astype(int); jj = self.scr[:, 2].astype(int)
            flux = np.where(ax == 0, ux[ii + 1, jj], uy[ii, jj + 1]) * dx * self.scr[:, 5]
            q = np.bincount(self.scr_bin, flux, self.nbins)
            self.un_bin = q / self.BIN
        return self

    def sample(self, x, y):
        dx = self.dx
        fi = np.clip(x / dx - 0.5, 0, self.nx - 1.0001)
        fj = np.clip(y / dx - 0.5, 0, self.ny - 1.0001)
        i0 = np.minimum(fi.astype(int), self.nx - 2); j0 = np.minimum(fj.astype(int), self.ny - 2)
        tx, ty = fi - i0, fj - j0
        F = self.F
        return (F[:, i0, j0] * (1 - tx) * (1 - ty) + F[:, i0 + 1, j0] * tx * (1 - ty)
                + F[:, i0, j0 + 1] * (1 - tx) * ty + F[:, i0 + 1, j0 + 1] * tx * ty)

    # screen hydraulics (quadratic mesh law, used for dP, loads, bell pressure)
    def dp_bins(self):
        P = self.P
        b = self.cov[: self.nbins]
        dp = 0.5 * RHO * K_mesh(P.beta * np.maximum(1 - b, 0.02)) * self.un_bin ** 2
        return dp

    def screen_head_mm(self):
        """Flux-weighted head difference across the screen (mm water)."""
        dp = self.dp_bins(); q = np.abs(self.un_bin)
        active = ~self.raised[np.minimum((np.arange(self.nbins) * self.BIN / (self.g.Ls / self.P.n_bays)).astype(int), self.P.n_bays - 1)]
        if q[active].sum() == 0:
            return 0.0
        return float((dp * q)[active].sum() / q[active].sum() / (RHO * GRAV) * 1000)

    def screen_force_N(self):
        dp = self.dp_bins()
        return float((dp * self.BIN * self.P.H).sum())


# ----------------------------------------------------------------------------------
class Sim:
    def __init__(self, P: Params, seed=0, flow=None, record_every=0):
        self.P = P
        self.rng = np.random.default_rng(seed)
        self.g = Geometry(P)
        self.flow = flow if flow is not None else Flow(P, self.g)
        if flow is not None:
            self.flow.cov[:] = 0
            self.flow.raised[:] = not P.screen
            self.flow.solve()
        self.t = 0.0
        self.N = 0
        z2 = np.zeros((0, 2))
        self.pos = np.zeros((0, 3)); self.vel = z2.copy(); self.ut = np.zeros((0, 3))
        self.d = np.zeros(0); self.rho = np.zeros(0); self.E = np.zeros(0)
        self.kind = np.zeros(0, int); self.status = np.zeros(0, int)
        self.t_out = np.full(0, np.nan); self.vol = np.zeros(0); self.ws = np.zeros(0)
        self.swim = np.zeros(0); self.head = np.zeros(0)
        self.flags = {k: np.zeros(0, bool) for k in ("extruded", "under", "over", "raised_cross",
                                                       "curtain_through", "curtain_defl")}
        self.contact = np.zeros(0, bool); self.cs = np.zeros(0); self.still = np.zeros(0)
        self.bay_of = np.zeros(0, int)
        self.events = []
        self.scale = lambda t: (1.0, 0.0)
        self.wave = None
        self.couple = P.layout == "lane" and P.screen
        self.next_couple = 1.0
        self.nlay = 5
        self.slot_timer = np.zeros((1 + len(self.g.mid_slots), self.nlay))
        self.bay_zlo = np.full(P.n_bays, P.bottom_gap)
        self.record_every = record_every
        self.frames = []
        self.step_i = 0
        self.block_override = False   # T06: bar position governs blocking while lowering

    # ---------------------------------------------------------------
    def add(self, xy, z, d, drho, kind=KIND_BELL, E=None, swim=0.0, dome=True):
        n = len(d)
        d = np.asarray(d, float)
        vol = np.pi * d ** 3 / (12 if dome else 6)
        area = np.pi * d ** 2 / 4
        rho_p = RHO + np.asarray(drho, float)
        ws = settling_velocity(np.asarray(drho, float) * np.ones(n), d, vol, area, self.P.cd_mult)
        ext = lambda a, b: np.concatenate([a, b])
        self.pos = np.vstack([self.pos, np.column_stack([xy, z])])
        self.vel = np.vstack([self.vel, np.zeros((n, 2))])
        self.ut = np.vstack([self.ut, np.zeros((n, 3))])
        self.d = ext(self.d, d); self.rho = ext(self.rho, rho_p)
        self.E = ext(self.E, np.full(n, self.P.E) if E is None else np.broadcast_to(E, n).astype(float))
        self.kind = ext(self.kind, np.full(n, kind)); self.status = ext(self.status, np.zeros(n, int))
        self.t_out = ext(self.t_out, np.full(n, np.nan)); self.vol = ext(self.vol, vol); self.ws = ext(self.ws, ws)
        self.swim = ext(self.swim, np.broadcast_to(swim, n).astype(float))
        self.head = ext(self.head, self.rng.uniform(0, 2 * np.pi, n))
        for k in self.flags:
            self.flags[k] = ext(self.flags[k], np.zeros(n, bool))
        self.contact = ext(self.contact, np.zeros(n, bool)); self.cs = ext(self.cs, np.zeros(n))
        self.still = ext(self.still, np.zeros(n)); self.bay_of = ext(self.bay_of, -np.ones(n, int))
        ids = np.arange(self.N, self.N + n)
        self.N += n
        return ids

    def release_bells(self, n, x_range=(0.03, 0.18), d_range=(0.04, 0.06), drho=None, kind=KIND_BELL,
                      E=None, dome=True, swim=0.0, y_range=None, z_range=None):
        P, r = self.P, self.rng
        d = r.uniform(*d_range, n)
        if y_range is None:
            y_range = (P.y_lo, P.y_up) if P.layout == "lane" else (0.0, P.Ly)
        y = r.uniform(y_range[0] + d / 2 + 0.003, y_range[1] - d / 2 - 0.003)
        x = r.uniform(*x_range, n)
        zr = z_range or (0, P.H)
        z = r.uniform(np.maximum(zr[0], d / 2), np.minimum(zr[1], P.H - d / 2))
        if drho is None:
            drho = surrogate_drho(r, n, self.P.rho_sd_scale)
        return self.add(np.column_stack([x, y]), z, d, drho, kind, E, swim, dome)

    # ---------------------------------------------------------------
    def set_bay(self, k, raised):
        self.flow.raised[k] = raised
        self.flow.solve()

    def _capture(self, ids, code):
        self.status[ids] = code
        self.t_out[ids] = self.t
        for i in ids:
            self.events.append((self.t, int(i), int(code)))

    def update_coverage(self):
        """Face blinding per bin from bells in contact with the (down) screen."""
        fl = self.flow
        cov = np.zeros(fl.nbins)
        A = np.nonzero((self.status == ACTIVE) & self.contact)[0]
        for i in A:
            r = self.d[i] / 2
            a = int(max(0, (self.cs[i] - r) / fl.BIN)); b = int(min(fl.nbins - 1, (self.cs[i] + r) / fl.BIN))
            cov[a:b + 1] += np.pi * r / (2 * self.P.H)
        cov = np.minimum(cov, 0.95)
        dc = np.abs(cov - fl.cov[: fl.nbins])
        if dc.mean() > 0.01 or dc.max() > 0.25:
            fl.cov[: fl.nbins] = cov
            fl.solve()

    def face_cover_pct(self):
        A = np.nonzero((self.status == ACTIVE) & self.contact)[0]
        down = ~self.flow.raised
        area = self.g.Ls * self.P.H * down.mean() if down.any() else 1
        return float(min(100.0, 100 * np.sum(np.pi * self.d[A] ** 2 / 4) / area))

    # ---------------------------------------------------------------
    def step(self):
        P, dt = self.P, self.P.dt
        A = np.nonzero(self.status == ACTIVE)[0]
        self.t += dt
        self.step_i += 1
        self.slot_timer = np.maximum(self.slot_timer - dt, 0)
        if len(A) == 0:
            self._record()
            return
        pos, vel = self.pos[A], self.vel[A]
        d, r = self.d[A], self.d[A] / 2
        sc, dsc = self.scale(self.t)
        f = self.flow.sample(pos[:, 0], pos[:, 1])
        u = sc * f[0:2].T
        a_f = sc * sc * f[2:4].T + dsc * f[0:2].T
        wz = np.zeros(len(A))
        eta = 0.0
        if self.wave is not None:
            Hw, om, k, h = self.wave
            ph = k * pos[:, 0] - om * self.t
            zz = np.clip(pos[:, 2], 0, h)
            Uw = 0.5 * Hw * om * np.cosh(k * zz) / np.sinh(k * h)
            Ww = 0.5 * Hw * om * np.sinh(k * zz) / np.sinh(k * h)
            u[:, 0] += Uw * np.cos(ph)
            a_f[:, 0] += Uw * om * np.sin(ph)
            wz += Ww * np.sin(ph)
            eta = 0.5 * Hw * np.cos(ph)
        # swimming (turtle)
        sw = self.swim[A]
        if np.any(sw > 0):
            self.head[A] += np.sqrt(2 * 0.5 * dt) * self.rng.standard_normal(len(A))
            u = u + sw[:, None] * np.column_stack([np.cos(self.head[A]), np.sin(self.head[A])])
        # turbulence (OU)
        spd = np.hypot(u[:, 0], u[:, 1])
        sig = P.turb_I * spd + P.turb_s0
        al = np.exp(-dt / P.TL)
        ut = self.ut[A]
        ut = ut * al + np.sqrt(1 - al ** 2) * self.rng.standard_normal((len(A), 3)) * \
            np.column_stack([sig, sig, 0.5 * sig])
        self.ut[A] = ut
        uf = u + ut[:, :2]
        # drag / added mass
        vol = self.vol[A]
        area = np.pi * d ** 2 / 4
        rho_p = self.rho[A]
        m_eff = (rho_p + P.Cm * RHO) * vol
        vrel = uf - vel
        vr = np.hypot(vrel[:, 0], vrel[:, 1])
        cdrag = 0.5 * RHO * area * cd_sphere(vr * d / NU + 1e-9) * P.cd_mult * vr
        cdrag = np.maximum(cdrag, 3 * np.pi * MU * d)
        beta = (1 + P.Cm) * RHO * vol / m_eff
        Fc = np.zeros((len(A), 2))
        dz = np.zeros(len(A))
        # particle-particle soft contacts
        if len(A) > 1:
            tree = cKDTree(pos)
            pairs = tree.query_pairs(self.d.max(), output_type="ndarray")
            if len(pairs):
                i, j = pairs[:, 0], pairs[:, 1]
                dv = pos[j] - pos[i]
                dist = np.linalg.norm(dv, axis=1) + 1e-12
                ov = r[i] + r[j] - dist
                m = ov > 0
                if m.any():
                    i, j, dv, dist, ov = i[m], j[m], dv[m], dist[m], ov[m]
                    nrm = dv / dist[:, None]
                    mij = 1 / (1 / m_eff[i] + 1 / m_eff[j])
                    Eij = 2 / (1 / self.E[A][i] + 1 / self.E[A][j])
                    k = np.minimum(Eij * 0.5 * (d[i] + d[j]), 0.2 * mij / dt ** 2)
                    vn = np.sum((vel[j] - vel[i]) * nrm[:, :2], 1)
                    fn = k * ov - 2 * 0.5 * np.sqrt(k * mij) * vn
                    fn = np.maximum(fn, 0)
                    fv = fn[:, None] * nrm[:, :2]
                    np.add.at(Fc, i, -fv); np.add.at(Fc, j, fv)
                    np.add.at(dz, i, -0.5 * ov * nrm[:, 2]); np.add.at(dz, j, 0.5 * ov * nrm[:, 2])
        # semi-implicit velocity update
        cm = cdrag / m_eff
        vnew = (vel + dt * (beta[:, None] * a_f + cm[:, None] * uf + Fc / m_eff[:, None])) / (1 + dt * cm)[:, None]
        # floor friction for sinkers resting on the floor
        on_floor = pos[:, 2] <= r + 1e-4
        Wsub = np.maximum(rho_p - RHO, 0) * vol * GRAV
        fr = np.where(on_floor, P.mu_floor * Wsub / m_eff * dt, 0)
        vs = np.hypot(vnew[:, 0], vnew[:, 1]) + 1e-12
        vnew *= np.maximum(0, 1 - fr / vs)[:, None]
        newp = pos[:, :2] + vnew * dt
        # vertical
        znew = pos[:, 2] + dt * (-self.ws[A] + ut[:, 2] + wz) + dz
        # ---- segment contacts ----
        contact = np.zeros(len(A), bool); cs = np.zeros(len(A)); bayof = -np.ones(len(A), int)
        for sg in self.g.all_segments():
            newp, vnew, znew = self._seg_contact(sg, A, pos, newp, vnew, znew, r, d, m_eff, u, contact, cs, bayof, eta)
        # tank box
        newp[:, 0] = np.clip(newp[:, 0], r, P.Lx - r * 0.5)
        newp[:, 1] = np.clip(newp[:, 1], r, P.Ly - r)
        ztop = P.H + (eta if np.ndim(eta) else 0) - r * 0.5
        znew = np.clip(znew, r, np.maximum(ztop, r + 1e-3))
        moved = np.hypot(*(newp - pos[:, :2]).T) / dt
        self.still[A] = np.where(moved < 0.002, self.still[A] + dt, 0)
        self.pos[A, :2] = newp; self.pos[A, 2] = znew; self.vel[A] = vnew
        self.contact[A] = contact; self.cs[A] = cs; self.bay_of[A] = bayof
        self._captures(A)
        if self.couple and self.t >= self.next_couple:
            self.next_couple = self.t + 2.0
            self.update_coverage()
        self._record()

    def _record(self):
        if self.record_every and self.step_i % self.record_every == 0:
            self.frames.append((self.t, self.pos[:, :3].copy(), self.status.copy(), self.d.copy(),
                                self.kind.copy(), self.contact.copy(), self.flow.raised.copy()))

    def _blocks(self, sg, z, r, d, eta):
        """Which particles are blocked by segment sg (depends on bay state & z-gaps)."""
        P = self.P
        if sg.kind == "wall":
            return np.ones(len(z), bool), None
        sq = P.squeeze_max
        if sg.kind == "screen":
            if self.flow.raised[sg.bay] and not self.block_override:
                return np.zeros(len(z), bool), "raised"
            zlo = self.bay_zlo[sg.bay]
            zhi = P.H + P.freeboard
            under = (z + r * (1 - sq)) < zlo
            over = (z - r * (1 - sq)) > zhi
            return ~(under | over), np.where(under, "under", np.where(over, "over", ""))
        if sg.kind == "curtain":
            under = (z + r * (1 - sq)) < P.curtain_zlo
            over = (z - r * (1 - sq)) > P.curtain_zhi
            return ~(under | over), np.where(under, "under", np.where(over, "over", ""))

    def _seg_contact(self, sg, A, pos, newp, vnew, znew, r, d, m_eff, u, contact, cs, bayof, eta):
        P, dt = self.P, self.P.dt
        rel_old = pos[:, :2] - sg.p0
        rel = newp - sg.p0
        sd_old = rel_old @ sg.n
        sd = rel @ sg.n
        s = rel @ sg.t
        near = (s > -r) & (s < sg.L + r) & ((np.abs(sd) < r) | (np.sign(sd) != np.sign(sd_old)))
        if not near.any():
            return newp, vnew, znew
        blk, mode = self._blocks(sg, znew, r, d, eta)
        side = np.where(sd_old >= 0, 1.0, -1.0)
        crossed = (np.sign(sd) != np.sign(sd_old)) & (s >= 0) & (s <= sg.L)
        # non-blocked crossings -> flags
        pas = near & crossed & ~blk
        if pas.any():
            ids = A[pas]
            if sg.kind == "screen":
                for k, i in zip(np.nonzero(pas)[0], ids):
                    md = mode if isinstance(mode, str) else mode[k]
                    code = {"raised": 12, "under": 10, "over": 11}.get(md)
                    if code is not None:
                        key = {12: "raised_cross", 10: "under", 11: "over"}[code]
                        if not self.flags[key][i]:
                            self.events.append((self.t, int(i), code))
                        self.flags[key][i] = True
            elif sg.kind == "curtain":
                self.flags["curtain_through"][ids] = True
        idx = np.nonzero(near & blk)[0]
        if len(idx) == 0:
            return newp, vnew, znew
        sc = np.clip(s[idx], 0, sg.L)
        C = sg.p0 + sc[:, None] * sg.t
        inner = (s[idx] > 0) & (s[idx] < sg.L)
        nrm = np.where(inner[:, None], side[idx, None] * sg.n, 0)
        dvec = newp[idx] - C
        dl = np.linalg.norm(dvec, axis=1) + 1e-12
        nrm = np.where(inner[:, None], nrm, dvec / dl[:, None])
        dist = np.where(inner, side[idx] * sd[idx], dl)
        rr = r[idx]
        hit = dist < rr
        if not hit.any():
            return newp, vnew, znew
        idx, nrm, dist, rr, C, sc = idx[hit], nrm[hit], dist[hit], rr[hit], C[hit], sc[hit]
        newp[idx] += (rr - dist)[:, None] * nrm
        v = vnew[idx]
        vn = np.sum(v * nrm, 1)
        inward = np.maximum(-vn, 0)
        v = v - np.minimum(vn, 0)[:, None] * nrm
        tng = np.column_stack([-nrm[:, 1], nrm[:, 0]])
        vt = np.sum(v * tng, 1)
        cap = P.mu_f * inward
        area = np.pi * rr ** 2
        if sg.kind == "screen":
            front = side[idx] > 0
            if True:
                fl = self.flow
                sabs = sc + sg.s0
                bins = np.clip((sabs / fl.BIN).astype(int), 0, fl.nbins - 1)
                bl = fl.cov[bins]
                un = np.abs(fl.un_bin[bins]) * abs(self.scale(self.t)[0])
                dp = 0.5 * RHO * K_mesh(P.beta * np.maximum(1 - bl, 0.02)) * un ** 2
                # extrusion through mesh (fragments mainly): Cauchy-number criterion
                a_mesh = P.mesh_mm / 1000
                dcrit = P.c_ext * self.E[A[idx]] * np.maximum(2 * rr / a_mesh - 1, 0)
                ext = front & (dp > dcrit)
                if ext.any():
                    ii = idx[ext]
                    newp[ii] -= 2.2 * rr[ext, None] * nrm[ext]
                    self.flags["extruded"][A[ii]] = True
                    keep = ~ext
                    idx, nrm, v, vt, tng, cap, inward, dp, front, rr, area, sc = (
                        idx[keep], nrm[keep], v[keep], vt[keep], tng[keep], cap[keep], inward[keep], dp[keep],
                        front[keep], rr[keep], area[keep], sc[keep])
                push = np.where(front, (dp + P.adhesion) * area / m_eff[idx] * dt, 0)
                cap = cap + P.mu_f * push
                contact[idx] = front
                cs[idx] = sc + sg.s0
                bayof[idx] = sg.bay
        if sg.kind == "curtain":
            # through-flow over/under the curtain draws pressed particles toward the gaps
            unl = np.abs(np.sum(u[idx] * nrm, 1))
            zc = znew[idx]
            mid = 0.5 * (P.curtain_zlo + P.curtain_zhi)
            znew[idx] += np.where(zc > mid, 1, -1) * P.curtain_draw * unl * dt
        vt_new = np.sign(vt) * np.maximum(np.abs(vt) - cap, 0)
        vnew[idx] = v + (vt_new - vt)[:, None] * tng
        return newp, vnew, znew

    def _captures(self, A):
        P = self.P
        x, y, z = self.pos[A, 0], self.pos[A, 1], self.pos[A, 2]
        r = self.d[A] / 2
        sc = self.scale(self.t)[0]
        if P.layout == "lane":
            m = (x > P.Lx - r - 0.006) & (y < P.y_up) & (y > P.y_lo)
            if m.any():
                self._capture(A[m], INTAKE)
            m = (x < r + 0.004) & (self.swim[A] > 0) & (self.status[A] == ACTIVE)
            if m.any():
                self._capture(A[m], EXIT_UP)
            fl = self.flow
            if fl.q_slot > 0:
                v_in_end = fl.q_slot / P.gap_w
                v_in_mid = fl.q_slot / P.slot_w
                lay = np.clip((z / (P.H / self.nlay)).astype(int), 0, self.nlay - 1)
                x0, x1, y0, y1 = self.g.pocket
                inp = (x > x0) & (x < x1) & (y > y0) & (self.status[A] == ACTIVE)
                for k in np.nonzero(inp)[0]:
                    if self.slot_timer[0, lay[k]] <= 0:
                        self.slot_timer[0, lay[k]] = self.d[A[k]] / max(v_in_end, 0.005)
                        self._capture(A[[k]], BYPASS)
                rel = np.column_stack([x - self.g.S[0], y - self.g.S[1]])
                sa, na = rel @ self.g.t, rel @ self.g.n
                for q, sm in enumerate(self.g.mid_slots):
                    m = (np.abs(sa - sm) < P.slot_w / 2) & (na > 0) & (na < r + 0.012) & (self.status[A] == ACTIVE)
                    for k in np.nonzero(m)[0]:
                        if self.slot_timer[q + 1, lay[k]] <= 0:
                            self.slot_timer[q + 1, lay[k]] = self.d[A[k]] / max(v_in_mid, 0.005)
                            self._capture(A[[k]], BYPASS)
        else:
            if sc > 0:
                m = x > P.Lx - r - 0.006
                if m.any():
                    self._capture(A[m], EXIT_DOWN)
            elif sc < 0:
                m = x < r + 0.006
                if m.any():
                    self._capture(A[m], EXIT_UP)
            if self.g.curtains:
                sg = self.g.curtains[0]
                # deflection = passing the curtain's (infinite) line outside the segment
                rel = self.pos[A, :2] - sg.p0
                s = rel @ sg.t
                sd = rel @ sg.n
                prev = getattr(self, "_sd_prev", None)
                if prev is None or len(prev) != self.N:
                    self._sd_prev = np.full(self.N, np.nan)
                    prev = self._sd_prev
                pv = prev[A]
                cr = ~np.isnan(pv) & (np.sign(pv) != np.sign(sd))
                outside = (s < 0) | (s > sg.L)
                newd = cr & outside & ~self.flags["curtain_through"][A]
                self.flags["curtain_defl"][A[newd]] = True
                self._sd_prev[A] = sd

    # ---------------------------------------------------------------
    def run(self, T, early_stop=True, callback=None):
        nsteps = int(round(T / self.P.dt))
        for k in range(nsteps):
            if callback is not None:
                callback(self)
            self.step()
            if early_stop and k % 100 == 0 and self.N:
                act = self.status == ACTIVE
                if not act.any():
                    break
                if self.t > 20 and np.all(self.still[act] > 10):
                    break
        return self

    def summary(self, ids=None):
        ids = np.arange(self.N) if ids is None else np.asarray(ids)
        st = self.status[ids]
        act = st == ACTIVE
        front = self.contact[ids].copy()
        if self.P.layout == "lane" and self.P.screen:
            rel = self.pos[ids, :2] - self.g.S
            sa, na = rel @ self.g.t, rel @ self.g.n
            front |= (na > 0) & (sa > 0) & (sa < self.g.Ls + 0.02)
        stuck = act & front & (self.still[ids] > 3.0)
        return dict(n=len(ids), intake=int((st == INTAKE).sum()), bypass=int((st == BYPASS).sum()),
                    stuck=int(stuck.sum()), lost=int((act & ~stuck).sum()),
                    exit_down=int((st == EXIT_DOWN).sum()), exit_up=int((st == EXIT_UP).sum()),
                    under=int(self.flags["under"][ids].sum()), over=int(self.flags["over"][ids].sum()),
                    extruded=int(self.flags["extruded"][ids].sum()))


# ----------------------------------------------------------------------------------
# Surrogate bell density model (T01) -- used for every bell in every test
SURR = dict(gel="gelatin", gel_pct=3.0, gel_pct_sd=0.05, drho_per_pct=2.6, salt_coef=0.70,
            air_frac_mean=2e-4, air_frac_sd=2e-4, salt_step_gL=0.1, batch_salt_sd_gL=0.05)


def surrogate_drho(rng, n, sd_scale=1.0, spec=SURR):
    """Bell density minus tank-water density after the tank salt is tuned to the median bell.
    Sources of scatter: gel concentration, trapped air, salt-tuning step resolution."""
    gel = spec["gel_pct"] + spec["gel_pct_sd"] * rng.standard_normal(n) * sd_scale
    air = np.clip(spec["air_frac_mean"] + spec["air_frac_sd"] * rng.standard_normal(n) * sd_scale, 0, None)
    rho_b = 998.2 + spec["drho_per_pct"] * gel - 1000 * air + spec["salt_coef"] * spec["batch_salt_sd_gL"] * rng.standard_normal(n) * sd_scale
    # tank salt tuned (in steps) to the median bell
    target = np.median(rho_b)
    S_t = np.round((target - 998.2) / spec["salt_coef"] / spec["salt_step_gL"]) * spec["salt_step_gL"]
    rho_t = 998.2 + spec["salt_coef"] * S_t
    return rho_b - rho_t
