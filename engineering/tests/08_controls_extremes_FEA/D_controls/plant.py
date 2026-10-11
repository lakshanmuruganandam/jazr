"""Plant + sensing models for the time-domain simulation (1 s scan).

Hydraulics: the screen bays and the always-open relief bay are PARALLEL paths between a common
upstream lane and a common downstream channel, so they share ONE head difference (line dP):
    dP = 1/2 rho (Q / sum_i A_i K_i^-1/2)^2
K_i (Idelchik woven screen, effective porosity eps*(1-b_i)) = 1.3(1-e) + (1/e - 1)^2,
raised/open bays K = 0.2, relief bay K_relief = 1.0 (entrance + exit) [ENG].
=> per-bay dP transmitters all read (almost) the same value: they detect LINE blinding, not which
bay is blinded. Bay choice must come from round-robin / oldest-cleaned / per-bay flow or camera.

Face biomass per DOWN bay: arrivals in proportion to bay flow; bells slide to bypass with
residence tau [V3: entrances every 30 m at 0.5 m/s -> ~60 s]; a fraction sticks:
s(dP) = s0 + (1-s0) * clip((dP-100)/(240-100), 0, 1)  (audit #2 friction-vs-sweep numbers:
friction dP*A*mu equals sweep drag ~8 N at ~240 Pa) [ASM from audit].
Blockage b = bells x 0.11 m2 / A_bay [audit]. Raising a bay releases its whole face load into the
plant (the pulse) spread over the raise time.
"""
import numpy as np
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from common import params as P
from common import gantry as GT

EPS = 0.64
BELL_AREA = 0.11


def k_screen(b):
    e = max(EPS * (1 - min(b, 0.995)), 1e-3)
    return 1.3 * (1 - e) + (1 / e - 1) ** 2


class Plant:
    def __init__(self, n=15, Q=P.Q_UNIT, depth=7.0, density=P.DESIGN_DENSITY, tau=60.0, s0=0.02,
                 speed=P.DRUM_LINE_SPEED, drop=P.MESH_DROP, relief_area=None, seed=0,
                 relief_mode="open", relief_open_dp=600.0, relief_band=200.0):
        self.relief_mode, self.relief_open_dp, self.relief_band = relief_mode, relief_open_dp, relief_band
        self.n, self.Q, self.density, self.tau, self.s0 = n, Q, density, tau, s0
        self.A = P.SCREEN_AREA / n                    # m2 per bay (wetted)
        self.relief_area = relief_area if relief_area is not None else self.A
        self.travel = drop / speed                    # s per full raise/lower
        self.x = np.full(n, 0.0)                      # 0 = top (stowed) .. 1 = bottom (deployed)
        self.slide = np.zeros(n)                      # kg sliding on face
        self.stuck = np.zeros(n)                      # kg stuck on face
        self.release_rate = np.zeros(n)               # kg/s being released while raising
        self.stuck_drum = np.zeros(n, bool)
        self.rng = np.random.default_rng(seed)
        self.dp = 0.0
        self.to_plant_kg = 0.0
        self.to_bypass_kg = 0.0
        self.relief_kg = 0.0

    def pos_code(self, bottom=30):
        c = np.clip(np.round(self.x * bottom), 1, bottom - 1).astype(int)
        return np.where(self.x <= 1e-9, 0, np.where(self.x >= 1 - 1e-9, bottom, c))

    def blockage(self):
        return np.clip((self.slide + self.stuck) / P.BELL_MASS * BELL_AREA / self.A, 0, 0.995)

    def step(self, cmds, dt=1.0):
        rate = dt / self.travel
        for k, c in enumerate(cmds):
            if self.stuck_drum[k]:
                continue
            if c == "UP" and self.x[k] > 0:
                if self.release_rate[k] == 0:
                    self.release_rate[k] = (self.slide[k] + self.stuck[k]) / max(self.x[k] * self.travel, 1.0)
                self.x[k] = max(0.0, self.x[k] - rate)
            elif c == "DOWN" and self.x[k] < 1:
                self.x[k] = min(1.0, self.x[k] + rate)
        # hydraulics: effective deployed fraction = x (mesh covers that fraction of the depth)
        b = self.blockage()
        K = np.array([k_screen(bi) for bi in b])
        conduct = self.A * (self.x / np.sqrt(K) + (1 - self.x) / np.sqrt(0.2))
        if self.relief_mode == "open":       # v3: permanently open relief bay
            C_relief = self.relief_area / np.sqrt(1.0)
            self.dp = 0.5 * P.RHO_W * (self.Q / (conduct.sum() + C_relief)) ** 2
        else:                                 # passive flap/overflow: closed below relief_open_dp
            dp = self.dp
            for _ in range(30):
                op = np.clip((dp - self.relief_open_dp) / self.relief_band, 0, 1)
                C_relief = self.relief_area * op
                dpn = 0.5 * P.RHO_W * (self.Q / (conduct.sum() + C_relief)) ** 2
                dp = 0.5 * dp + 0.5 * dpn
            self.dp = dp
            C_relief = self.relief_area * np.clip((dp - self.relief_open_dp) / self.relief_band, 0, 1)
        v = np.sqrt(2 * self.dp / P.RHO_W)
        q_screen = self.A * self.x * v / np.sqrt(K)
        q_open = self.A * (1 - self.x) * v / np.sqrt(0.2)
        q_relief = C_relief * v
        conc = self.density * P.BELL_MASS            # kg/m3
        arr = conc * q_screen * dt                    # kg arriving on deployed face
        s = self.s0 + (1 - self.s0) * np.clip((self.dp - 100) / 140, 0, 1)
        out_slide = self.slide / self.tau * dt
        self.to_bypass_kg += out_slide.sum()
        self.slide += arr * (1 - s) - out_slide
        self.stuck += arr * s
        # release while raising (pulse)
        rel = np.minimum(self.release_rate * dt, self.slide + self.stuck)
        raising = np.array([c == "UP" for c in cmds]) & ~self.stuck_drum
        rel = np.where(raising, rel, 0.0)
        frac = np.where(self.slide + self.stuck > 0, rel / np.maximum(self.slide + self.stuck, 1e-9), 0)
        self.slide *= (1 - frac); self.stuck *= (1 - frac)
        self.release_rate = np.where(self.x <= 0, 0.0, np.where(raising, self.release_rate, 0.0))
        self.to_plant_kg += rel.sum() + conc * (q_open.sum() + q_relief) * dt
        self.relief_kg += conc * (q_open.sum() + q_relief) * dt
        return rel  # kg released per bay this second


class WaveDP:
    """Wave-induced dP fluctuation at each bay (random-phase JONSWAP-like, 30 deg obliquity)."""

    def __init__(self, n, Hs, Tp, seed=1, depth=7.0, spacing=10.0):
        rng = np.random.default_rng(seed)
        f = np.linspace(0.6 / Tp, 3.0 / Tp, 40)
        fp = 1 / Tp
        sig = np.where(f <= fp, 0.07, 0.09)
        S = (f ** -5) * np.exp(-1.25 * (fp / f) ** 4) * 3.3 ** np.exp(-(f - fp) ** 2 / (2 * sig**2 * fp**2))
        df = f[1] - f[0]
        S *= (Hs / 4) ** 2 / (S.sum() * df)
        self.amp_eta = np.sqrt(2 * S * df)
        self.f = f
        self.ph = rng.uniform(0, 2 * np.pi, len(f))
        k = np.array([GT.wave_number(1 / fi, depth) for fi in f])
        zz = np.linspace(-depth, 0, 20)
        w = 2 * np.pi * f
        self.u_per_eta = np.array([np.mean(wi * np.cosh(ki * (zz + depth)) / np.sinh(ki * depth)) for wi, ki in zip(w, k)])
        self.kx = k * np.cos(np.radians(30)) * spacing
        self.n = n

    def dp(self, t, v0=P.V_APPROACH_SCREEN, kmesh=0.78):
        bays = np.arange(self.n)[:, None]
        u = (self.amp_eta * self.u_per_eta * np.cos(2 * np.pi * self.f * t - self.kx * bays + self.ph)).sum(1)
        un = u * np.sin(np.radians(30))
        return kmesh * 0.5 * P.RHO_W * ((v0 + un) * np.abs(v0 + un) - v0**2)


class Sensing:
    """Per bay: dP-A, dP-B transmitters + load-cell-derived dP estimate -> low-pass -> 2oo3 vote ->
    persistence. Hard-wired channel: dP-A, tau 10 s, persistence 10 s -> hard level."""

    def __init__(self, n, tau=30.0, pers=20, trip=P.DP_TRIP, hard=P.DP_HARD, seed=2, raw_mode=False, hard_vote="2oo2"):
        self.hard_vote = hard_vote
        self.n, self.tau, self.pers_req, self.trip, self.hard = n, tau, pers, trip, hard
        self.lp = np.zeros((n, 3))
        self.lph = np.zeros(n)
        self.cnt = np.zeros(n, int)
        self.hcnt = np.zeros(n, int)
        self.rng = np.random.default_rng(seed)
        self.fault = {}   # (bay, ch) -> ('stuck', value) | ('nan',)
        self.raw_mode = raw_mode
        self.disagree = np.zeros(n, bool)

    def read(self, dp_bays, dt=1.0):
        raw = np.stack([dp_bays + self.rng.normal(0, 5, self.n),
                        dp_bays + self.rng.normal(0, 5, self.n),
                        dp_bays * (1 + self.rng.normal(0, 0.2, self.n)) + self.rng.normal(0, 20, self.n)], 1)
        for (b, ch), f in self.fault.items():
            raw[b, ch] = f[1] if f[0] == "stuck" else np.nan
        if self.raw_mode:  # naive: single transmitter, no filter, no persistence
            lvl = np.where(raw[:, 0] > self.hard, 2, np.where(raw[:, 0] > self.trip, 1, 0))
            return lvl, raw
        a = dt / (self.tau + dt) if self.tau > 0 else 1.0
        good = np.isfinite(raw)
        self.lp = np.where(good, self.lp + a * (np.nan_to_num(raw) - self.lp), self.lp)
        votes = np.where(good, self.lp > self.trip, True)     # failed channel votes 'trip' (fail-safe)
        hi = votes.sum(1) >= 2
        self.disagree = (np.nanmax(np.where(good, self.lp, np.nan), 1) - np.nanmin(np.where(good, self.lp, np.nan), 1) > 0.5 * self.trip) | ~good.all(1)
        self.cnt = np.where(hi, self.cnt + 1, 0)
        ah = dt / (10.0 + dt)
        if not hasattr(self, "lphb"):
            self.lphb = np.zeros(self.n)
        ra = np.where(np.isfinite(raw[:, 0]), raw[:, 0], self.lph)
        rb = np.where(np.isfinite(raw[:, 1]), raw[:, 1], self.lphb)
        self.lph = self.lph + ah * (ra - self.lph)
        self.lphb = self.lphb + ah * (rb - self.lphb)
        if self.hard_vote == "1oo1":       # single hard-wired transmitter (dP-A)
            hh = self.lph > self.hard
        else:                              # 2oo2 of A and B (a failed/NaN channel counts as 'trip')
            ha = np.where(np.isfinite(raw[:, 0]), self.lph > self.hard, True)
            hb = np.where(np.isfinite(raw[:, 1]), self.lphb > self.hard, True)
            hh = ha & hb
        self.hcnt = np.where(hh, self.hcnt + 1, 0)
        lvl = np.where(self.hcnt >= 10, 2, np.where(self.cnt >= max(self.pers_req, 1), 1, 0))
        return lvl, raw
