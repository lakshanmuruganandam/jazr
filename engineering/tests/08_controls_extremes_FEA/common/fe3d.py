"""Minimal 3D Euler-Bernoulli frame finite-element solver (12 DOF/element).

DOF order per node: ux, uy, uz, rx, ry, rz.
Features: linear static, modal (lumped mass with direction-dependent added mass),
linear buckling (geometric stiffness from axial force), member force recovery.
Verified against closed-form solutions in tests/test_fe3d.py.
"""
import numpy as np
import scipy.linalg as sla


class Section:
    def __init__(self, A, Iy, Iz, J, mat, Wy=None, Wz=None, name=""):
        self.A, self.Iy, self.Iz, self.J = A, Iy, Iz, J
        self.mat, self.name = mat, name
        self.Wy, self.Wz = Wy, Wz

    @staticmethod
    def chs(D, t, mat, name="CHS"):
        Di = D - 2 * t
        A = np.pi / 4 * (D**2 - Di**2)
        I = np.pi / 64 * (D**4 - Di**4)
        return Section(A, I, I, 2 * I, mat, Wy=I / (D / 2), Wz=I / (D / 2), name=name)

    @staticmethod
    def box(H, B, t, mat, name="BOX"):
        # local y = width direction (B), local z = height direction (H)
        A = H * B - (H - 2 * t) * (B - 2 * t)
        Iy = (B * H**3 - (B - 2 * t) * (H - 2 * t) ** 3) / 12  # bending about local y (z-deflection)
        Iz = (H * B**3 - (H - 2 * t) * (B - 2 * t) ** 3) / 12
        Am = (H - t) * (B - t)
        J = 4 * Am**2 / (2 * (H - t) / t + 2 * (B - t) / t)
        return Section(A, Iy, Iz, J, mat, Wy=Iy / (H / 2), Wz=Iz / (B / 2), name=name)


class Frame:
    def __init__(self):
        self.nodes = []        # xyz
        self.elems = []        # dict(n1, n2, sec, ref, madd)
        self.fixed = {}        # node -> list of dof idx
        self.lumped = {}       # node -> mass (translational)

    def node(self, xyz):
        self.nodes.append(np.asarray(xyz, float))
        return len(self.nodes) - 1

    def elem(self, n1, n2, sec, ref=None, madd=0.0):
        """madd = added transverse mass per length (hydrodynamic + entrained), kg/m."""
        self.elems.append(dict(n1=n1, n2=n2, sec=sec, ref=ref, madd=madd))
        return len(self.elems) - 1

    def line(self, p1, p2, nseg, sec, ref=None, madd_fn=None, n1=None, n2=None):
        """Mesh a straight member; returns node ids. madd_fn(z_mid)->kg/m."""
        p1, p2 = np.asarray(p1, float), np.asarray(p2, float)
        ids = []
        for i in range(nseg + 1):
            if i == 0 and n1 is not None:
                ids.append(n1); continue
            if i == nseg and n2 is not None:
                ids.append(n2); continue
            ids.append(self.node(p1 + (p2 - p1) * i / nseg))
        for a, b in zip(ids[:-1], ids[1:]):
            zm = 0.5 * (self.nodes[a][2] + self.nodes[b][2])
            self.elem(a, b, sec, ref, madd_fn(zm) if madd_fn else 0.0)
        return ids

    def fix(self, n, dofs=(0, 1, 2, 3, 4, 5)):
        self.fixed[n] = list(dofs)

    def add_mass(self, n, m):
        self.lumped[n] = self.lumped.get(n, 0.0) + m

    @property
    def ndof(self):
        return 6 * len(self.nodes)

    # ---------------- element matrices ----------------
    def _geom(self, e):
        p1, p2 = self.nodes[e["n1"]], self.nodes[e["n2"]]
        d = p2 - p1
        L = np.linalg.norm(d)
        ex = d / L
        ref = e["ref"]
        if ref is None:
            ref = np.array([0, 0, 1.0]) if abs(ex[2]) < 0.99 else np.array([1.0, 0, 0])
        ey = np.cross(ref, ex); ey /= np.linalg.norm(ey)
        ez = np.cross(ex, ey)
        R = np.vstack([ex, ey, ez])
        T = np.zeros((12, 12))
        for k in range(4):
            T[3 * k:3 * k + 3, 3 * k:3 * k + 3] = R
        return L, T

    @staticmethod
    def _kl(sec, L):
        E, Gm = sec.mat["E"], sec.mat["G"]
        A, Iy, Iz, J = sec.A, sec.Iy, sec.Iz, sec.J
        k = np.zeros((12, 12))
        a = E * A / L
        k[0, 0] = k[6, 6] = a; k[0, 6] = k[6, 0] = -a
        t = Gm * J / L
        k[3, 3] = k[9, 9] = t; k[3, 9] = k[9, 3] = -t
        # bending in local x-y plane (v, rz): dofs 1,5,7,11
        c = E * Iz / L**3
        idx = [1, 5, 7, 11]
        m = c * np.array([[12, 6 * L, -12, 6 * L], [6 * L, 4 * L**2, -6 * L, 2 * L**2],
                          [-12, -6 * L, 12, -6 * L], [6 * L, 2 * L**2, -6 * L, 4 * L**2]])
        k[np.ix_(idx, idx)] += m
        # bending in local x-z plane (w, ry): dofs 2,4,8,10 (sign flip on rotations)
        c = E * Iy / L**3
        idx = [2, 4, 8, 10]
        m = c * np.array([[12, -6 * L, -12, -6 * L], [-6 * L, 4 * L**2, 6 * L, 2 * L**2],
                          [-12, 6 * L, 12, 6 * L], [-6 * L, 2 * L**2, 6 * L, 4 * L**2]])
        k[np.ix_(idx, idx)] += m
        return k

    @staticmethod
    def _kg(P, L):
        """Geometric stiffness, axial force P (tension +)."""
        k = np.zeros((12, 12))
        c = P / (30 * L)
        idx = [1, 5, 7, 11]
        m = c * np.array([[36, 3 * L, -36, 3 * L], [3 * L, 4 * L**2, -3 * L, -L**2],
                          [-36, -3 * L, 36, -3 * L], [3 * L, -L**2, -3 * L, 4 * L**2]])
        k[np.ix_(idx, idx)] += m
        idx = [2, 4, 8, 10]
        m = c * np.array([[36, -3 * L, -36, -3 * L], [-3 * L, 4 * L**2, 3 * L, -L**2],
                          [-36, 3 * L, 36, 3 * L], [-3 * L, -L**2, 3 * L, 4 * L**2]])
        k[np.ix_(idx, idx)] += m
        return k

    def _dofs(self, e):
        a, b = e["n1"], e["n2"]
        return np.r_[6 * a:6 * a + 6, 6 * b:6 * b + 6]

    def K(self):
        K = np.zeros((self.ndof, self.ndof))
        for e in self.elems:
            L, T = self._geom(e)
            d = self._dofs(e)
            K[np.ix_(d, d)] += T.T @ self._kl(e["sec"], L) @ T
        return K

    def M(self):
        """Lumped mass: structural mass all directions, added mass transverse only."""
        M = np.zeros((self.ndof, self.ndof))
        for e in self.elems:
            L, T = self._geom(e)
            d = self._dofs(e)
            ms = e["sec"].mat["rho"] * e["sec"].A * L / 2
            mt = ms + e["madd"] * L / 2
            rot = ms * L**2 / 50.0  # small rotary inertia to keep M positive definite
            ml = np.diag([ms, mt, mt, rot, rot, rot] * 2)
            M[np.ix_(d, d)] += T.T @ ml @ T
        for n, m in self.lumped.items():
            for k in range(3):
                M[6 * n + k, 6 * n + k] += m
        return M

    def free(self):
        fx = set()
        for n, ds in self.fixed.items():
            fx.update(6 * n + k for k in ds)
        return np.array([i for i in range(self.ndof) if i not in fx])

    def solve(self, F):
        K = self.K()
        f = self.free()
        u = np.zeros(self.ndof)
        u[f] = np.linalg.solve(K[np.ix_(f, f)], F[f])
        return u

    def member_forces(self, u):
        """Local end forces per element (12-vector, local axes)."""
        out = []
        for e in self.elems:
            L, T = self._geom(e)
            d = self._dofs(e)
            out.append(self._kl(e["sec"], L) @ (T @ u[d]))
        return out

    def stresses(self, u, extra_axial=None):
        """Max |N/A| + |My/Wy| + |Mz/Wz| at either end per element (conservative linear sum)."""
        fl = self.member_forces(u)
        s = []
        for e, f in zip(self.elems, fl):
            sec = e["sec"]
            vals = []
            for o in (0, 6):
                N, My, Mz = f[o + 0], f[o + 4], f[o + 5]
                vals.append(abs(N) / sec.A + abs(My) / sec.Wy + abs(Mz) / sec.Wz)
            s.append(max(vals))
        return np.array(s), fl

    def modal(self, nmodes=6):
        f = self.free()
        K = self.K()[np.ix_(f, f)]
        M = self.M()[np.ix_(f, f)]
        w2, V = sla.eigh(K, M, subset_by_index=[0, nmodes - 1])
        Phi = np.zeros((self.ndof, nmodes))
        Phi[f] = V
        return np.sqrt(np.maximum(w2, 0)) / (2 * np.pi), Phi, M, f

    def buckling(self, u_ref, nmodes=3):
        """Load factors lambda for the reference load producing displacement u_ref."""
        f = self.free()
        K = self.K()
        Kg = np.zeros_like(K)
        fl = self.member_forces(u_ref)
        for e, fe in zip(self.elems, fl):
            L, T = self._geom(e)
            P = fe[6]  # axial force at end 2 (tension +)
            d = self._dofs(e)
            Kg[np.ix_(d, d)] += T.T @ self._kg(P, L) @ T
        Kf, Kgf = K[np.ix_(f, f)], Kg[np.ix_(f, f)]
        mu = sla.eigvals(-Kgf, Kf)
        mu = np.real(mu[np.isfinite(mu)])
        mu = mu[mu > 1e-12]
        lam = np.sort(1.0 / mu)
        return lam[:nmodes]
