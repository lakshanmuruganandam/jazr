"""
jzcfd.py - small 2D CFD core for the JAZR Gate v3 CFD tests (numpy + scipy only).

Model: 2D incompressible depth-averaged (shallow, rigid-lid) Navier-Stokes on a uniform staggered (MAC) grid,
    du/dt + (u.grad)u = -grad(p) + nu_t lap(u) - (Cf/h)|u|u - R_screen(u),   div(u) = -s (bypass sinks)
  * advection: 2nd-order upwind (linear-upwind) in advective form, Heun (RK2) time stepping
  * pressure: Chorin projection, sparse LU (scipy splu) factorised once
  * porous screen: anisotropic Darcy-Forchheimer band (a smeared porous jump).  Normal: Forchheimer loss
    k*rho*u_n^2/2 distributed over the band (integral of the coefficient across the band = k/2).  Tangential:
    loss proportional to |u_n|*u_t calibrated so that fluid crossing the screen keeps a fraction
    alpha = 1.1/sqrt(1+k) of its tangential velocity (gauze 'refraction', Schubauer et al. 1950 / Laws & Livesey
    1978).  Optional constant tangential damping lam (sensitivity bound).  Point-implicit, unconditionally stable.
  * boundaries: inlet = prescribed velocity, outlet = p = 0 (Dirichlet), walls = free-slip, solid cells allowed.
  * sinks (bypass entrances) enter the continuity equation, so mass balance is exact to solver precision.
Units SI, rho = 1 (pressures are kinematic, m^2/s^2).  nu_t is a depth-averaged eddy viscosity (Elder-type).
"""
import numpy as np, scipy.sparse as sp, scipy.sparse.linalg as spla, time


def alpha_refr(k):
    """fraction of tangential velocity kept by flow crossing a gauze of loss coefficient k (<=1)."""
    return np.minimum(1.0, 1.1/np.sqrt(1.0 + np.asarray(k, float)))


def k_wire(beta):
    """Loss coefficient of a woven-wire screen vs open-area ratio beta (Idelchik-type correlation, high Re):
       k = 1.3(1-beta) + (1/beta - 1)^2.  Used only to map 'porosity' to k; k itself is what the CFD uses."""
    beta = np.asarray(beta, float)
    return 1.3*(1 - beta) + (1/beta - 1)**2


class Flow2D:
    def __init__(self, nx, ny, dx, fluid=None, sink=None, Kq=None, lam=None, Kt=None, nvec=None,
                 u_in=0.0, nu=0.012, fric=0.0, cfl=0.3, umax=1.0, dt_max=None):
        self.nx, self.ny, self.dx = nx, ny, dx
        self.fluid = np.ones((nx, ny), bool) if fluid is None else fluid.astype(bool)
        self.sink = np.zeros((nx, ny)) if sink is None else sink.astype(float)
        Kq = np.zeros((nx, ny)) if Kq is None else Kq
        lam = np.zeros((nx, ny)) if lam is None else lam
        Kt = np.zeros((nx, ny)) if Kt is None else Kt
        if nvec is None:
            nvec = np.zeros((nx, ny, 2)); nvec[..., 0] = 1.0
        self.nu, self.fric = nu, fric
        self.u_in = np.broadcast_to(np.asarray(u_in, float), (ny,)).copy()
        f = self.fluid
        # open faces
        uo = np.zeros((nx+1, ny), bool); uo[1:nx] = f[:-1] & f[1:]; uo[0] = f[0]; uo[nx] = f[-1]
        vo = np.zeros((nx, ny+1), bool); vo[:, 1:ny] = f[:, :-1] & f[:, 1:]
        self.uo, self.vo = uo, vo
        self.uint = uo.copy(); self.uint[0] = False; self.uint[nx] = False   # interior (solved) u faces
        # face resistance coefficients
        def favg_u(a):
            out = np.zeros((nx+1, ny)); out[1:nx] = 0.5*(a[:-1]+a[1:]); out[0] = a[0]; out[nx] = a[-1]; return out
        def favg_v(a):
            out = np.zeros((nx, ny+1)); out[:, 1:ny] = 0.5*(a[:, :-1]+a[:, 1:]); out[:, 0] = a[:, 0]; out[:, ny] = a[:, -1]; return out
        self.Kq_u, self.Kq_v = favg_u(Kq), favg_v(Kq)
        self.lam_u, self.lam_v = favg_u(lam), favg_v(lam)
        self.Kt_u, self.Kt_v = favg_u(Kt), favg_v(Kt)
        # face normals: average over adjacent RESISTIVE cells only (sign-aligned), default (1,0)
        w = ((Kq + Kt + lam) > 0).astype(float)
        sgn = np.where(nvec[..., 0] + 1e-9*nvec[..., 1] >= 0, 1.0, -1.0)      # make n_x >= 0 (sign irrelevant)
        n0, n1 = nvec[..., 0]*sgn*w, nvec[..., 1]*sgn*w
        def fnorm(a0, a1):
            nn = np.hypot(a0, a1); ok = nn > 1e-12
            return np.where(ok, a0/np.where(ok, nn, 1), 1.0), np.where(ok, a1/np.where(ok, nn, 1), 0.0)
        self.nx_u, self.ny_u = fnorm(favg_u(n0), favg_u(n1))
        self.nx_v, self.ny_v = fnorm(favg_v(n0), favg_v(n1))
        self.u = np.zeros((nx+1, ny)); self.v = np.zeros((nx, ny+1))
        self.u[:] = self.u_in.mean()*uo
        self.u[0] = self.u_in*uo[0]
        self.dt = min(cfl*dx/umax, 0.2*dx*dx/max(nu, 1e-12), dt_max or np.inf)
        self._build_poisson()
        self.t = 0.0

    # ------------------------------------------------------------------ pressure Poisson
    def _build_poisson(self):
        nx, ny, dx, f = self.nx, self.ny, self.dx, self.fluid
        idx = -np.ones((nx, ny), int); idx[f] = np.arange(f.sum()); self.idx = idx
        N = int(f.sum()); rows, cols, vals = [], [], []
        diag = np.zeros(N)
        I, J = np.nonzero(f)
        p = idx[I, J]
        for di, dj, omask in ((1, 0, None), (-1, 0, None), (0, 1, None), (0, -1, None)):
            I2, J2 = I+di, J+dj
            ok = (I2 >= 0) & (I2 < nx) & (J2 >= 0) & (J2 < ny)
            ok2 = ok.copy(); ok2[ok] = f[I2[ok], J2[ok]]
            rows.append(p[ok2]); cols.append(idx[I2[ok2], J2[ok2]]); vals.append(np.ones(ok2.sum()))
            diag[p[ok2]] -= 1.0
        # outlet Dirichlet p=0 at east boundary face
        out = (I == nx-1) & self.uo[nx, J]
        diag[p[out]] -= 2.0
        rows.append(np.arange(N)); cols.append(np.arange(N)); vals.append(diag)
        A = sp.csc_matrix((np.concatenate(vals)/dx**2, (np.concatenate(rows), np.concatenate(cols))), shape=(N, N))
        if not out.any():
            raise ValueError("no outlet: Poisson singular")
        self.lu = spla.splu(A)
        self.I, self.J = I, J

    # ------------------------------------------------------------------ helpers
    @staticmethod
    def _adv(phi, a, b, dx):
        P = np.pad(phi, 2, mode='edge'); c = P[2:-2, 2:-2]
        dxm = (3*c - 4*P[1:-3, 2:-2] + P[0:-4, 2:-2])/(2*dx)
        dxp = (-3*c + 4*P[3:-1, 2:-2] - P[4:, 2:-2])/(2*dx)
        dym = (3*c - 4*P[2:-2, 1:-3] + P[2:-2, 0:-4])/(2*dx)
        dyp = (-3*c + 4*P[2:-2, 3:-1] - P[2:-2, 4:])/(2*dx)
        return np.where(a > 0, a*dxm, a*dxp) + np.where(b > 0, b*dym, b*dyp)

    @staticmethod
    def _lap(phi, dx):
        P = np.pad(phi, 1, mode='edge'); c = P[1:-1, 1:-1]
        return (P[2:, 1:-1] + P[:-2, 1:-1] + P[1:-1, 2:] + P[1:-1, :-2] - 4*c)/dx**2

    def v_at_u(self, v):
        nx, ny = self.nx, self.ny
        vc = 0.5*(v[:, :-1] + v[:, 1:])                         # (nx, ny) cell centres
        out = np.empty((nx+1, ny)); out[1:nx] = 0.5*(vc[:-1] + vc[1:]); out[0] = vc[0]; out[nx] = vc[-1]
        return out

    def u_at_v(self, u):
        nx, ny = self.nx, self.ny
        uc = 0.5*(u[:-1] + u[1:])
        out = np.empty((nx, ny+1)); out[:, 1:ny] = 0.5*(uc[:, :-1] + uc[:, 1:]); out[:, 0] = uc[:, 0]; out[:, ny] = uc[:, -1]
        return out

    def _rhs(self, u, v):
        dx = self.dx
        Fu = -self._adv(u, u, self.v_at_u(v), dx) + self.nu*self._lap(u, dx)
        Fv = -self._adv(v, self.u_at_v(u), v, dx) + self.nu*self._lap(v, dx)
        return Fu, Fv

    def _bc(self, u, v):
        u[~self.uo] = 0.0; v[~self.vo] = 0.0
        u[0] = self.u_in*self.uo[0]
        u[self.nx] = np.where(self.uo[self.nx], u[self.nx-1], 0.0)    # zero-gradient predictor
        return u, v

    @staticmethod
    def _c(x):
        """steady-state-consistent implicit coefficient: with the fractional step, a point-implicit damping
        dt*a acts at steady state as a/(1+dt*a); using x/(1-x) (x = dt*a, capped) restores the target a."""
        x = np.minimum(x, 0.95)
        return x/(1 - x)

    def _resist(self, u, v, dt):
        # u faces
        vv = self.v_at_u(v); nxu, nyu = self.nx_u, self.ny_u
        un = u*nxu + vv*nyu; ut = -u*nyu + vv*nxu
        un2 = un/(1 + self._c(dt*self.Kq_u*np.abs(un))); ut2 = ut/(1 + self._c(dt*(self.lam_u + self.Kt_u*np.abs(un))))
        unew = un2*nxu - ut2*nyu
        unew /= (1 + dt*self.fric*np.hypot(u, vv))
        # v faces
        uu = self.u_at_v(u); nxv, nyv = self.nx_v, self.ny_v
        un = uu*nxv + v*nyv; ut = -uu*nyv + v*nxv
        un2 = un/(1 + self._c(dt*self.Kq_v*np.abs(un))); ut2 = ut/(1 + self._c(dt*(self.lam_v + self.Kt_v*np.abs(un))))
        vnew = un2*nyv + ut2*nxv
        vnew /= (1 + dt*self.fric*np.hypot(uu, v))
        return np.where(self.uint, unew, u), np.where(self.vo, vnew, v)

    def divergence(self, u=None, v=None):
        u = self.u if u is None else u; v = self.v if v is None else v
        return (u[1:] - u[:-1] + v[:, 1:] - v[:, :-1])/self.dx

    def _project(self, u, v, dt):
        dx, nx = self.dx, self.nx
        rhs = (self.divergence(u, v) + self.sink)[self.I, self.J]/dt
        phi = np.zeros((self.nx, self.ny)); phi[self.I, self.J] = self.lu.solve(rhs)
        gx = (phi[1:] - phi[:-1])/dx
        u[1:nx] -= dt*np.where(self.uint[1:nx], gx, 0.0)
        u[nx] -= dt*np.where(self.uo[nx], -2*phi[nx-1]/dx, 0.0)
        gy = (phi[:, 1:] - phi[:, :-1])/dx
        v[:, 1:self.ny] -= dt*np.where(self.vo[:, 1:self.ny], gy, 0.0)
        self.p = phi
        return u, v

    def step(self):
        dt = self.dt; u, v = self.u, self.v
        Fu, Fv = self._rhs(u, v)
        u1 = u + dt*Fu; v1 = v + dt*Fv; u1, v1 = self._bc(u1, v1)
        Fu1, Fv1 = self._rhs(u1, v1)
        u2 = 0.5*(u + u1 + dt*Fu1); v2 = 0.5*(v + v1 + dt*Fv1); u2, v2 = self._bc(u2, v2)
        u2, v2 = self._resist(u2, v2, dt)
        u2, v2 = self._project(u2, v2, dt)
        res = max(np.abs(u2 - u).max(), np.abs(v2 - v).max())/dt
        self.u, self.v = u2, v2; self.t += dt
        return res

    def initialise(self):
        self.u, self.v = self._bc(self.u, self.v)
        self.u, self.v = self._project(self.u, self.v, self.dt)

    def run(self, t_min=300.0, t_max=2000.0, tol=2e-5, wall_max=500.0, avg=0.0, verbose=False):
        """march to steady state; if the flow is unsteady (vortex shedding) and avg > 0, the returned fields are
        time averages over the last `avg` seconds of t_max (instantaneous fields kept in u_inst, v_inst)."""
        self.initialise(); t0 = time.time(); res = np.inf; hist = []
        n = 0; su = np.zeros_like(self.u); sv = np.zeros_like(self.v); sp_ = np.zeros((self.nx, self.ny)); na = 0
        converged = False
        while self.t < t_max:
            res = self.step(); n += 1
            if avg > 0 and (self.t >= t_max - avg or (time.time() - t0 > 0.6*wall_max and self.t > 0.5*t_max)):
                su += self.u; sv += self.v; sp_ += self.p; na += 1
            if n % 50 == 0:
                hist.append((self.t, res))
                if verbose: print(f"  t={self.t:7.1f}s res={res:.2e}")
                if not np.isfinite(res): raise FloatingPointError("diverged")
                if self.t > t_min and res < tol: converged = True; break
                if time.time() - t0 > wall_max: break
        self.u_inst, self.v_inst = self.u.copy(), self.v.copy()
        if na > 0 and not converged:
            self.u, self.v, self.p = su/na, sv/na, sp_/na
        self.res = res; self.hist = np.array(hist); self.wall = time.time() - t0; self.nsteps = n
        self.converged = converged; self.n_avg = na if not converged else 0
        return self

    # ------------------------------------------------------------------ diagnostics
    def centred(self):
        uc = 0.5*(self.u[:-1] + self.u[1:]); vc = 0.5*(self.v[:, :-1] + self.v[:, 1:])
        uc = np.where(self.fluid, uc, 0.0); vc = np.where(self.fluid, vc, 0.0)
        return uc, vc

    def mass_balance(self):
        dx = self.dx
        qin = self.u[0].sum()*dx; qout = self.u[self.nx].sum()*dx; qs = self.sink.sum()*dx*dx
        div = self.divergence() + self.sink
        return dict(q_in=qin, q_out=qout, q_sink=qs, imbalance=(qin - qout - qs)/qin,
                    max_cell_div=float(np.abs(div[self.fluid]).max()))


class Interp:
    """bilinear interpolation of cell-centred fields (uc, vc) on a uniform grid with spacing dx."""
    def __init__(self, uc, vc, dx):
        self.uc, self.vc, self.dx = uc, vc, dx; self.nx, self.ny = uc.shape

    def __call__(self, x, y):
        dx = self.dx
        fx = np.clip(x/dx - 0.5, 0, self.nx - 1.000001); fy = np.clip(y/dx - 0.5, 0, self.ny - 1.000001)
        i = fx.astype(int); j = fy.astype(int); a = fx - i; b = fy - j
        def g(F):
            return (F[i, j]*(1-a)*(1-b) + F[i+1, j]*a*(1-b) + F[i, j+1]*(1-a)*b + F[i+1, j+1]*a*b)
        return g(self.uc), g(self.vc)
