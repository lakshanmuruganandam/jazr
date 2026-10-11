"""
vt_ext.py - eta_max extensions of the JAZR virtual tank (copy of 07_virtual_tank/vtank.py in this folder).
*** SIMULATED virtual tank (1:20 Froude tank analogue) - not physical evidence. ***

Adds, without changing the base physics:
  * conveyor screen   : mesh belt moving along the face toward the apex/downstream entrance at belt_frac x V_sw;
                        Coulomb friction acts on the bell velocity RELATIVE to the belt (moving-wall BC).
  * graded baffles    : extra resistance behind the downstream 40% of the face, iterated so that the clean-screen
                        through-velocity there equals the face mean (uniform through-velocity).
  * wall jet          : added tangential velocity jet_frac x V_sw * exp(-dn/jet_delta) in front of the face.
  * apex on/off, apex share of the entrance flow, flared intermediate mouths (wider + deeper capture zone).
  * bell swimming     : random heading (base model), rheotactic (heads into the local flow = worst case),
                        or a HYPOTHETICAL cue bias (directed swim toward / away from the apex).
  * fouled bay        : one bay with raised mesh resistance and friction.
  * per-bell metrics  : face contacts (no-contact -> contact transitions), time on the face.
  * two screens       : run_series() re-releases the bells left stuck on screen 1 onto a second identical
                        catch screen (stage-2 load = what screen-1 relief/cycling would release).
V_sw (reference sweep speed) = U cos(theta) (approach speed resolved along the face).
"""
import numpy as np
from dataclasses import dataclass, replace
from vtank import (Params, Sim, Flow, Geometry, K_mesh, RHO, GRAV, ACTIVE, INTAKE, BYPASS, EXIT_UP,
                   KIND_BELL, LABEL)

SCALE = 20.0
VSCALE = np.sqrt(SCALE)          # Froude velocity scale (prototype / tank)


@dataclass
class ParamsX(Params):
    belt_frac: float = 0.0       # belt speed / V_sw
    baffle: bool = False
    jet_frac: float = 0.0        # wall-jet peak / V_sw
    jet_delta: float = 0.03      # m (tank) jet thickness (~0.6 m prototype, ~1 bell diameter in the tank)
    apex: bool = True            # downstream (apex) entrance open
    apex_share: float = -1.0     # share of entrance flow to the apex entrance (-1: equal split)
    flare: float = 1.0           # intermediate-mouth capture width multiplier (flared mouth)
    cap_depth: float = 0.012     # intermediate-mouth capture depth beyond the bell radius (m)
    foul_bay: int = -1           # index of a fouled bay (-1 none)
    foul_res: float = 4.0        # resistance multiplier on the fouled bay
    foul_mu: float = 0.8         # friction on the fouled bay


class FlowX(Flow):
    def __init__(self, P, geom):
        self.bfac = None
        self.Pext = P
        super().__init__(P, geom)
        if P.layout == "lane" and getattr(P, "baffle", False):
            self._grade_baffles()

    def _sink_shares(self):
        P = self.Pext
        n = len(self.sinks)
        sh = np.full(n, 1.0 / n)
        if not P.apex:
            sh[0] = 0.0
            sh[1:] = 1.0 / max(n - 1, 1)
        elif P.apex_share >= 0 and n > 1:
            sh[0] = P.apex_share
            sh[1:] = (1 - P.apex_share) / (n - 1)
        return sh

    def screen_G(self):
        P = self.Pext
        b = self.cov[self.scr_bin]
        ell = P.ell_s * np.ones(len(b))
        if self.bfac is not None:
            ell = ell * self.bfac[self.scr_bin]
        bay = self.scr[:, 4].astype(int)
        if P.foul_bay >= 0:
            ell = np.where(bay == P.foul_bay, ell * P.foul_res, ell)
        G = 1.0 / (1.0 + ell / (self.dx * np.maximum(1 - b, 0.02)))
        G = np.where(self.raised[bay], 1.0, G)
        G = np.where(self.scr_gap, 0.0, G)
        return G

    def solve(self):
        # same as Flow.solve but with unequal sink shares (apex share / apex closed)
        if not hasattr(self, "sinks") or len(self.sinks) == 0 or self.Pext.layout != "lane":
            return super().solve()
        P = self.Pext
        qtot = self.q_slot * len(self.sinks)
        sh = self._sink_shares()
        # temporarily emulate per-sink rates by scaling the masks' strength through q_slot trick:
        nx, ny, dx = self.nx, self.ny, self.dx
        import scipy.sparse as sp
        from scipy.sparse.linalg import spsolve
        Gx, Gy = self.Gx0.copy(), self.Gy0.copy()
        G = self.screen_G()
        ax = self.scr[:, 0].astype(int); ii, jj = self.scr[:, 1].astype(int), self.scr[:, 2].astype(int)
        Gx[ii[ax == 0], jj[ax == 0]] = G[ax == 0]; Gy[ii[ax == 1], jj[ax == 1]] = G[ax == 1]
        self._Gs = G
        idx = np.arange(nx * ny).reshape(nx, ny)
        r, c, d = [], [], []
        for Pi, Ni, g in ((idx[:-1, :], idx[1:, :], Gx), (idx[:, :-1], idx[:, 1:], Gy)):
            Pi, Ni, g = Pi.ravel(), Ni.ravel(), g.ravel()
            r += [Pi, Ni, Pi, Ni]; c += [Pi, Ni, Ni, Pi]; d += [g, g, -g, -g]
        diag = np.full(nx * ny, 1e-10); diag[idx[-1, self.outflow]] += 2.0
        r.append(np.arange(nx * ny)); c.append(np.arange(nx * ny)); d.append(diag)
        A = sp.csr_matrix((np.concatenate(d), (np.concatenate(r), np.concatenate(c))), shape=(nx * ny, nx * ny))
        b = np.zeros((nx, ny)); b[0, self.inflow] += P.U * dx
        bs = np.zeros((nx, ny))
        for m, s_ in zip(self.sinks, sh):
            bs[m] -= qtot * s_ / m.sum()
        b = b + bs
        phi = spsolve(A.tocsc(), b.ravel(), permc_spec="MMD_AT_PLUS_A").reshape(nx, ny)
        self.phi = phi
        ux = np.zeros((nx + 1, ny)); uy = np.zeros((nx, ny + 1))
        ux[1:-1] = Gx * (phi[:-1] - phi[1:]) / dx; ux[0, self.inflow] = P.U
        ux[-1, self.outflow] = 2 * phi[-1, self.outflow] / dx
        uy[:, 1:-1] = Gy * (phi[:, :-1] - phi[:, 1:]) / dx
        self.ux_f, self.uy_f = ux, uy
        u = 0.5 * (ux[:-1] + ux[1:]); v = 0.5 * (uy[:, :-1] + uy[:, 1:])
        dudx, dudy = np.gradient(u, dx); dvdx, dvdy = np.gradient(v, dx)
        self.F = np.stack([u, v, np.clip(u * dudx + v * dudy, -.5, .5), np.clip(u * dvdx + v * dvdy, -.5, .5)])
        self.Q_in = P.U * dx * self.inflow.sum(); self.Q_out = (2 * phi[-1, self.outflow]).sum()
        self.Q_sink = qtot; self.q_share = sh
        flux = np.where(ax == 0, ux[ii + 1, jj], uy[ii, jj + 1]) * dx * self.scr[:, 5]
        self.un_bin = np.bincount(self.scr_bin, flux, self.nbins) / self.BIN
        return self

    def _grade_baffles(self):
        """Iterate a resistance multiplier on the downstream 40% so un there -> face mean (clean screen)."""
        L = self.g.Ls
        sb = (np.arange(self.nbins) + 0.5) * self.BIN
        down = sb > 0.6 * L
        self.bfac = np.ones(self.nbins)
        for _ in range(12):
            self.solve()
            un = np.abs(self.un_bin)
            target = un[~down & (sb > 0.05 * L)].mean()
            f = np.where(down, np.clip(un / max(target, 1e-9), 0.5, 3.0) ** 1.5, 1.0)
            self.bfac = np.clip(self.bfac * f, 1.0, 400.0)
        self.solve()

    def sample(self, x, y):
        out = super().sample(x, y)
        P = self.Pext
        if P.layout == "lane" and P.jet_frac > 0:
            g = self.g
            rel = np.stack([x - g.S[0], y - g.S[1]], -1)
            sa, na = rel @ g.t, rel @ g.n
            on = (sa > 0) & (sa < g.Ls) & (na > 0)
            vj = P.jet_frac * P.U * np.cos(np.radians(P.theta_deg)) * np.exp(-np.maximum(na, 0) / P.jet_delta) * on
            out = out.copy()
            out[0] += vj * g.t[0]; out[1] += vj * g.t[1]
        return out


class SimX(Sim):
    def __init__(self, P, seed=0, record_every=0, swim_mode="random", cue_speed=0.0):
        g = Geometry(P)
        fl = FlowX(P, g)
        super().__init__(P, seed, flow=fl, record_every=record_every)
        if getattr(P, "baffle", False):
            # base __init__ re-solved with cov=0; keep baffle factors (bfac persists)
            pass
        self.flow.g = self.g
        self.Vsw = P.U * np.cos(np.radians(P.theta_deg))
        self.swim_mode = swim_mode
        self.cue_speed = cue_speed          # HYPOTHETICAL directed swim toward (+) / away (-) from the apex
        self.ncont = np.zeros(0, int); self.tface = np.zeros(0)
        self.prev_contact = np.zeros(0, bool)
        self.fed = 0

    def add(self, *a, **k):
        ids = super().add(*a, **k)
        n = len(ids)
        self.ncont = np.concatenate([self.ncont, np.zeros(n, int)])
        self.tface = np.concatenate([self.tface, np.zeros(n)])
        self.prev_contact = np.concatenate([self.prev_contact, np.zeros(n, bool)])
        return ids

    # -- behaviour: set heading before each step
    def _behaviour(self):
        A = np.nonzero((self.status == ACTIVE) & (self.swim > 0))[0]
        if len(A) == 0:
            return
        if self.swim_mode == "rheo":
            f = self.flow.sample(self.pos[A, 0], self.pos[A, 1])
            self.head[A] = np.arctan2(-f[1], -f[0]) + 0.3 * self.rng.standard_normal(len(A))

    def step(self):
        self._behaviour()
        P = self.P
        # hypothetical cue: directed velocity toward the apex/downstream entrance (applied as a displacement)
        if self.cue_speed != 0.0:
            A = np.nonzero(self.status == ACTIVE)[0]
            if len(A):
                E = np.array([self.g.E[0] + 0.5 * P.pocket_len, P.y_up - 0.5 * P.gap_w])
                dv = E - self.pos[A, :2]
                dd = np.linalg.norm(dv, axis=1) + 1e-9
                self.pos[A, :2] += P.dt * self.cue_speed * dv / dd[:, None]
        super().step()
        A = np.nonzero(self.status == ACTIVE)[0]
        c = self.contact[A]
        newc = c & ~self.prev_contact[A]
        self.ncont[A] += newc
        self.tface[A] += c * P.dt
        self.prev_contact[A] = c

    # -- screen contact with moving belt / fouled bay friction
    def _seg_contact(self, sg, A, pos, newp, vnew, znew, r, d, m_eff, u, contact, cs, bayof, eta):
        P = self.P
        if sg.kind != "screen" or (P.belt_frac == 0 and P.foul_bay < 0):
            return super()._seg_contact(sg, A, pos, newp, vnew, znew, r, d, m_eff, u, contact, cs, bayof, eta)
        if self.flow.raised[sg.bay]:
            return super()._seg_contact(sg, A, pos, newp, vnew, znew, r, d, m_eff, u, contact, cs, bayof, eta)
        vb = P.belt_frac * self.Vsw * sg.t
        mu0 = P.mu_f
        if P.foul_bay == sg.bay:
            object.__setattr__(P, "mu_f", P.foul_mu)
        # work in the belt frame: subtract belt velocity, apply standard contact, add it back to contacted bells
        before = vnew.copy()
        vrel = vnew - vb
        newp2, vrel2, znew2 = super()._seg_contact(sg, A, pos, newp, vrel, znew, r, d, m_eff, u - vb, contact, cs, bayof, eta)
        object.__setattr__(P, "mu_f", mu0)
        touched = np.any(vrel2 != (before - vb), axis=1)
        vout = np.where(touched[:, None], vrel2 + vb, before)
        return newp2, vout, znew2

    # -- captures with apex on/off and flared mid mouths
    def _captures(self, A):
        P = self.P
        x, y, z = self.pos[A, 0], self.pos[A, 1], self.pos[A, 2]
        r = self.d[A] / 2
        m = (x > P.Lx - r - 0.006) & (y < P.y_up) & (y > P.y_lo)
        if m.any():
            self._capture(A[m], INTAKE)
        m = (x < r + 0.004) & (self.swim[A] > 0) & (self.status[A] == ACTIVE)
        if m.any():
            self._capture(A[m], EXIT_UP)
        fl = self.flow
        if fl.q_slot <= 0:
            return
        sh = getattr(fl, "q_share", np.full(len(fl.sinks), 1 / len(fl.sinks)))
        qtot = fl.q_slot * len(fl.sinks)
        lay = np.clip((z / (P.H / self.nlay)).astype(int), 0, self.nlay - 1)
        if P.apex:
            v_in_end = qtot * sh[0] / P.gap_w
            x0, x1, y0, y1 = self.g.pocket
            inp = (x > x0) & (x < x1) & (y > y0) & (self.status[A] == ACTIVE)
            for k in np.nonzero(inp)[0]:
                if self.slot_timer[0, lay[k]] <= 0:
                    self.slot_timer[0, lay[k]] = self.d[A[k]] / max(v_in_end, 0.005)
                    self._capture(A[[k]], BYPASS)
        rel = np.column_stack([x - self.g.S[0], y - self.g.S[1]])
        sa, na = rel @ self.g.t, rel @ self.g.n
        wcap = P.slot_w * P.flare
        for q, sm in enumerate(self.g.mid_slots):
            v_in_mid = qtot * sh[q + 1] / P.slot_w
            if v_in_mid <= 0:
                continue
            m = (np.abs(sa - sm) < wcap / 2) & (na > 0) & (na < r + P.cap_depth * P.flare) & (self.status[A] == ACTIVE)
            for k in np.nonzero(m)[0]:
                if self.slot_timer[q + 1, lay[k]] <= 0:
                    self.slot_timer[q + 1, lay[k]] = self.d[A[k]] / max(v_in_mid, 0.005)
                    self._capture(A[[k]], BYPASS)
                    self.slot_hits[q + 1] += 1

    def entrance_counts(self):
        """bells captured per entrance (0 = apex). Needs slot_hits; apex = BYPASS total - mids."""
        mids = self.slot_hits[1:].sum()
        return np.concatenate([[int((self.status == BYPASS).sum()) - mids], self.slot_hits[1:]])

    def run(self, T, early_stop=True, callback=None):
        if not hasattr(self, "slot_hits"):
            self.slot_hits = np.zeros(1 + len(self.g.mid_slots), int)
        return super().run(T, early_stop, callback)


def metrics(s, ids=None):
    ids = np.arange(s.N) if ids is None else np.asarray(ids)
    sm = s.summary(ids)
    n = max(len(ids) - sm["exit_up"], 1)   # bells that swam back out of the lane inlet never reached the screen
    st = s.status[ids]
    return dict(n=n, bypass=sm["bypass"], stuck=sm["stuck"], intake=sm["intake"], lost=sm["lost"],
                exit_up=sm["exit_up"], eta=sm["bypass"] / n, jam=sm["stuck"] / n,
                contacts=float(s.ncont[ids].mean()) if len(ids) else 0.0,
                tface=float(s.tface[ids].mean()) if len(ids) else 0.0,
                tface_guided=float(s.tface[ids][st == BYPASS].mean()) if np.any(st == BYPASS) else float("nan"))


def design_rate_per_min(n_p=0.3):
    """Same dimensionless face loading as 07/run_protocols.design_rate_per_min (0.3 /m3 -> ~37/min)."""
    U_p, W_p, D_p = 0.5, 28.0, 7.0
    flux_p = n_p * U_p * W_p * D_p
    a_p = np.pi * 0.3 ** 2 / 4
    Pi_m = flux_p * a_p / 1000.0 * np.sqrt(SCALE)
    g = Geometry(Params())
    return float(Pi_m * g.Ls * Params().H / (np.pi * 0.05 ** 2 / 4) * 60)
