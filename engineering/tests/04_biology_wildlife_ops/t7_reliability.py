"""T7 - Reliability: bay (drum/motor) k-out-of-n, roll-up-on-demand, load-cell voting, required MTBF.
All failure rates are [ASSUME] ranges (no vendor data); results are requirements, not predictions.
"""
import numpy as np
from math import comb
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from params import *

n = 18
bloom_h = 240.0   # 10-day bloom (Hanbit-type)
res = {}

# 1) P(>=1 and >=2 bays failed during a bloom) vs MTBF, and steady-state P(>=2 down) vs MTTR
mtbfs = [500, 1000, 2000, 4000, 8000, 16000]
tab = {}
for m in mtbfs:
    p_fail = 1 - np.exp(-bloom_h / m)
    for mttr in (4, 8, 24, 72):
        u = mttr / (m + mttr)
        p2 = 1 - sum(comb(n, k) * u**k * (1-u)**(n-k) for k in range(2))
        tab[f"MTBF{m}_MTTR{mttr}"] = dict(P_bay_fails_in_bloom=p_fail, expected_failures_in_bloom=n*bloom_h/m,
                                          unavail_per_bay=u, P_ge2_bays_down=p2)
res["bays"] = tab
# requirement: P(>=2 bays down at any instant) <= 1%
req = {}
for mttr in (4, 8, 24, 72):
    for m in range(100, 200000, 100):
        u = mttr / (m + mttr)
        p2 = 1 - sum(comb(n, k) * u**k * (1-u)**(n-k) for k in range(2))
        if p2 <= 0.01:
            req[mttr] = m; break
res["required_bay_MTBF_h_for_P(>=2 down)<=1%"] = req

# 2) roll-up on demand (fail-open): motor+brake+VFD vs independent gravity/shear-pin release
pfd_motor = (0.01, 0.05)        # per demand [ASSUME]
pfd_gravity = (0.001, 0.01)     # [ASSUME]
res["rollup_on_demand"] = dict(motor_only=pfd_motor, motor_plus_independent_release=[a*b for a, b in zip(pfd_motor, pfd_gravity)],
                              demands_per_bloom_per_unit="~ n_bays x cycling (30% at high flux) -> tens to hundreds")

# 3) load-cell architecture (dangerous undetected = misses blinding; safe = spurious roll-up)
lam_du = 2e-5   # /h dangerous undetected per load-cell channel [ASSUME, includes drift]
lam_s = 5e-5    # /h spurious [ASSUME]
T = 24 * 7      # weekly proof/zero check in season [ASSUME]
beta = 0.05
arch = {
  "1oo1": dict(PFDavg=lam_du*T/2, spurious_per_yr=lam_s*8760),
  "1oo2": dict(PFDavg=((1-beta)*lam_du*T)**2/3 + beta*lam_du*T/2, spurious_per_yr=2*lam_s*8760),
  "2oo3 (2 cells + lane dP)": dict(PFDavg=((1-beta)*lam_du*T)**2 + beta*lam_du*T/2, spurious_per_yr=6*(lam_s**2)*8*8760 + beta*lam_s*8760),
}
res["load_cell_architectures_per_drum"] = arch

# 4) required availability (link to T6 DES and fault tree)
res["required_availability"] = {
  "screen (>= n-1 bays) during bloom hours": ">= 0.95 per bloom, >= 0.99 season [criterion]",
  "lift (>= 1 line)": ">= 0.99 (a lift outage converts the screen into a store that later dumps)",
  "wildlife protection function (camera+diverter+stop)": "PFD <= 1e-3 per demand -> SIL-2-like integrity although not nuclear-safety-related",
}
best = res["required_bay_MTBF_h_for_P(>=2 down)<=1%"]
res["verdicts"] = {
  "T7a_bay_redundancy": ("MARGINAL", "at MTBF 2,000-8,000 h a 10-day bloom sees %.1f-%.1f bay failures per unit; to keep P(>=2 bays down) <= 1%% need MTBF >= %d h at 8 h MTTR or >= %d h at 24 h MTTR -> spare bay drive cassettes on the gantry, MTTR <= 8 h" %
                          (tab['MTBF2000_MTTR8']['expected_failures_in_bloom'], tab['MTBF8000_MTTR8']['expected_failures_in_bloom'], best[8], best[24])),
  "T7b_fail_open": ("FAIL as specified", "motor-driven roll-up has PFD %.2f-%.2f per demand [ASSUME] -> a blinded bay can stay down; add an independent gravity/shear-pin release (PFD -> %.0e-%.0e)" % (pfd_motor[0], pfd_motor[1], res['rollup_on_demand']['motor_plus_independent_release'][0], res['rollup_on_demand']['motor_plus_independent_release'][1])),
  "T7c_load_cells": ("MARGINAL", "single cell PFD %.1e and %.1f spurious/yr per drum; 2oo3 (two cells + lane dP) gives PFD %.1e and %.2f spurious/yr -> specify 2oo3" %
                     (arch['1oo1']['PFDavg'], arch['1oo1']['spurious_per_yr'], arch['2oo3 (2 cells + lane dP)']['PFDavg'], arch['2oo3 (2 cells + lane dP)']['spurious_per_yr'])),
}
save("t7_reliability.json", res)

fig, ax = plt.subplots(figsize=(6.5, 3.8))
for mttr in (4, 8, 24, 72):
    ms = np.logspace(2.5, 5, 60)
    p2 = []
    for m in ms:
        u = mttr / (m + mttr)
        p2.append(1 - sum(comb(n, k) * u**k * (1-u)**(n-k) for k in range(2)))
    ax.loglog(ms, p2, label=f"MTTR {mttr} h")
ax.axhline(0.01, color="r", ls="--"); ax.set_xlabel("bay MTBF (h)"); ax.set_ylabel("P(>=2 of 18 bays down)")
ax.set_title("T7 bay redundancy requirement", fontsize=9); ax.legend(fontsize=7)
fig.tight_layout(); fig.savefig(os.path.join(CH, "t7_bay_redundancy.png"), dpi=130)
if __name__ == "__main__":
    print(best); print(arch)
    for k, (v, w) in res["verdicts"].items(): print(k, v, w)
