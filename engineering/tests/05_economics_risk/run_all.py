"""Run every economics / risk / emissions / rubric test and write out/*.json|csv and charts/*.png.
Usage:  python3 run_all.py
"""
import csv
import json
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import inputs as I
import econ as E

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
CH = os.path.join(HERE, "charts")
os.makedirs(OUT, exist_ok=True)
os.makedirs(CH, exist_ok=True)
N = 20000
C1, C2, C3, GREY, INK, INK2 = "#2a78d6", "#eb6834", "#1baf7a", "#9a9890", "#0b0b0b", "#52514e"
plt.rcParams.update({"figure.facecolor": "#fcfcfb", "axes.facecolor": "#fcfcfb", "axes.edgecolor": GREY,
                     "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2, "font.size": 10,
                     "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
                     "grid.color": "#e6e5e0", "grid.linewidth": 0.6})
R = {}

# ------------------------------------------------------------- T1 cost model
rows, direct, total = E.cost_table_modes()
R["T1_cost_table_mode_musd_per_unit"] = {k: round(v, 2) for k, v in rows}
R["T1_cost_bounds_musd_per_unit"] = {lab: {"direct": round(d, 1), "total": round(t, 1),
                                           "total_AED_M": round(t * I.AED_PER_USD)} for lab, d, t in
                                     E.cost_table_ranges()}
lev = {}
for case in "AB":
    s = E.simulate(n=N, case=case, units=4, seed=1)
    cap = s["capex"] / 4
    op = s["opex"] / 4
    lev[case] = {"capex_per_unit_musd_p10_p50_p90": np.percentile(cap, [10, 50, 90]).round(1).tolist(),
                 "capex_per_unit_AEDm_p10_p50_p90": (np.percentile(cap, [10, 50, 90]) * I.AED_PER_USD).round(0).tolist(),
                 "opex_per_unit_musd_yr_p10_p50_p90": np.percentile(op, [10, 50, 90]).round(2).tolist(),
                 "line_power_kw_p10_p50_p90": np.percentile(s["kw"], [10, 50, 90]).round(0).tolist()}
    for r in I.ECON["discount_rates"]:
        lc = cap * E.crf(r, I.ECON["horizon_years"]) + op
        lev[case][f"levelised_cost_per_unit_musd_yr_r{r}"] = np.percentile(lc, [10, 50, 90]).round(2).tolist()
R["T1_cost_MC"] = lev
gcid_2025 = 75 * 1.93
R["T1_crosscheck_GCID"] = {"GCID_1998_2001_musd": 75, "approx_2025_musd": round(gcid_2025), "flow_m3s": 85,
                           "note": "Includes river gradient facility; CPI ratio ~1.93 approximate"}

# ------------------------------------------------------------- T2 frequency / severity
sites = E.load_sites()
a, b = E.fit_gamma_poisson(sites)
ap, bp = E.site_posterior(a, b)
sev = E.load_severity()
rng = np.random.default_rng(3)
post = rng.gamma(ap, 1 / bp, 200000)
ev_sites = [s for s in sites if s["n"] > 0]
lam_prone = sum(s["n"] for s in ev_sites) / sum(s["T"] for s in ev_sites)
SCEN = {"S0 base (global Gamma-Poisson + the plant 0 events/5.5 yr)": None,
        "S1 jellyfish-prone site (pooled rate of sites with >=1 event)": lam_prone,
        "S2 Hanul-like (9 shutdowns 1996-2006)": 9 / 11,
        "S3 Gravelines-like (3 events 2025-26)": 1.5}
R["T2_frequency"] = {
    "sites": len(sites), "events": int(sum(s["n"] for s in sites)), "site_years": round(sum(s["T"] for s in sites)),
    "pooled_rate_all": round(sum(s["n"] for s in sites) / sum(s["T"] for s in sites), 4),
    "gamma_prior_alpha_beta": [round(a, 3), round(b, 2)], "prior_mean": round(a / b, 4),
    "site_posterior_mean": round(ap / bp, 4),
    "site_posterior_p10_p50_p90": np.percentile(post, [10, 50, 90]).round(4).tolist(),
    "P(lambda>0.1/yr)": round(float((post > 0.1).mean()), 3),
    "scenario_lambda": {k: (round(v, 4) if v else round(ap / bp, 4)) for k, v in SCEN.items()},
    "severity_unit_days_mean": round(float(sev.mean()), 2),
    "severity_unit_days_median_of_midpoints": round(float(np.median(sev.mean(1))), 2),
    "severity_max": float(sev[:, 1].max()),
    "unit_day_GWh": round(I.unit_day_mwh() / 1000, 1),
}
mid_price = I.ECON["value_usd_per_mwh"][1]
R["T2_expected_annual_loss_site_musd_no_jazr"] = {
    k: round(E.expected_annual_loss_site(v if v else ap / bp, sev.mean(), mid_price,
                                         I.ECON["fixed_cost_per_event_musd"][1]), 2) for k, v in SCEN.items()}

# ------------------------------------------------------------- T3 NPV / payback / break-even
npv_tab = []
sims = {}
for case in "AB":
    for sk, lamv in SCEN.items():
        for units, lab in ((4, "full"), (1, "pilot")):
            s = E.simulate(n=N, case=case, units=units, lam_fixed=lamv, seed=5)
            sims[(case, sk, lab)] = s
            for r in I.ECON["discount_rates"]:
                npv = s[f"npv_{r}"]
                npv_tab.append(dict(case=case, scenario=sk.split(" ")[0], rollout=lab, rate=r,
                                    p_payback=round(float((npv > 0).mean()), 3),
                                    npv_p10=round(float(np.percentile(npv, 10)), 1),
                                    npv_p50=round(float(np.percentile(npv, 50)), 1),
                                    npv_p90=round(float(np.percentile(npv, 90)), 1),
                                    median_payback_year=(float(np.median(s[f"payback_{r}"]))
                                                         if np.isfinite(np.median(s[f"payback_{r}"])) else None)))
with open(os.path.join(OUT, "npv_table.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(npv_tab[0].keys()))
    w.writeheader()
    w.writerows(npv_tab)
R["T3_npv_6pct_full"] = {f"{d['case']}-{d['scenario']}": dict(p_payback=d["p_payback"], npv_p50=d["npv_p50"])
                         for d in npv_tab if d["rate"] == 0.06 and d["rollout"] == "full"}

# break-even (deterministic, modes)
m_mode = I.JAZR["availability"][1] * I.JAZR["reach_frac"][1] / I.JAZR["reach_frac_today"] + (1 - I.JAZR["availability"][1])
resp_unit = I.ECON["response_cost_musd_per_site_yr"][1] * I.ECON["response_cost_saved_frac"][1] / 4
be = {}
for case in "AB":
    cap_u = (I.CAPEX_CASE_A_AED_M[1] / I.AED_PER_USD) if case == "A" else total
    dir_u = cap_u / 1.6 if case == "A" else direct
    op_u = dir_u * I.OPEX["maintenance_frac_of_direct"][1] + I.OPEX["staff_drills_musd"][1] + \
        I.OPEX["pigging_inspection_musd"][1] + 0.5 * I.OPEX["operating_hours"][1] * mid_price / 1e6
    for r in I.ECON["discount_rates"]:
        ud = E.breakeven_unit_days_per_year(cap_u, op_u, mid_price, m_mode, r, I.ECON["horizon_years"], resp_unit)
        lam_be = E.breakeven_lambda(cap_u, op_u, mid_price, m_mode, r, I.ECON["horizon_years"],
                                    I.ECON["fixed_cost_per_event_musd"][1], resp_unit, sev.mean())
        be[f"{case}_r{r}"] = dict(capex_unit_musd=round(cap_u, 1), opex_unit_musd=round(op_u, 2),
                                 unit_days_per_unit_yr=round(ud, 2),
                                 unit_days_over_life_per_unit=round(ud * I.ECON["horizon_years"], 1),
                                 site_events_per_yr_needed=round(lam_be, 2),
                                 years_between_events_needed=round(1 / lam_be, 1))
R["T3_breakeven"] = be
R["T3_note"] = ("Break-even uses mode inputs and the twin's mode reach (12%) and 95% availability; "
                "unit-days are outage days on the protected unit WITHOUT JAZR.")

# tornado: case A, full rollout, r=6%, around S1 (prone-site) expected values
def npv_det(p):
    H, bld, r = int(p["horizon"]), I.ECON["build_years"], p["r"]
    m = p["avail"] * p["reach"] / 0.95 + (1 - p["avail"])
    B = p["lam"] * (p["sev"] * I.unit_day_mwh() * p["price"] / 1e6 + p["fixed"]) * (1 - m) + p["resp"]
    cap = p["capex_u"] * 4
    v = -sum(cap / bld / (1 + r) ** y for y in range(bld))
    v += sum((B - p["opex_u"] * 4) / (1 + r) ** y for y in range(bld, H))
    return v

capA = I.CAPEX_CASE_A_AED_M[1] / I.AED_PER_USD
base = dict(lam=lam_prone, sev=float(sev.mean()), price=mid_price, fixed=I.ECON["fixed_cost_per_event_musd"][1],
            reach=I.JAZR["reach_frac"][1], avail=I.JAZR["availability"][1], resp=resp_unit * 4,
            capex_u=capA, opex_u=be["A_r0.06"]["opex_unit_musd"], r=0.06, horizon=30)
swings = {"Site event rate (S0 mean .. Hanul 0.82/yr)": ("lam", ap / bp, 9 / 11),
          "Severity unit-days/event (mean of lows..highs)": ("sev", float(sev[:, 0].mean()), float(sev[:, 1].mean())),
          "Value of lost MWh (USD 46..100)": ("price", 46, 100),
          "CAPEX per unit (AED 30..80 M)": ("capex_u", 30 / I.AED_PER_USD, 80 / I.AED_PER_USD),
          "Reach intake with JAZR (28%..5.5%, model)": ("reach", 0.28, 0.055),
          "Availability (85%..99%)": ("avail", 0.85, 0.99),
          "OPEX per unit (x0.5..x1.5)": ("opex_u", base["opex_u"] * 0.5, base["opex_u"] * 1.5),
          "Discount rate (10%..3%)": ("r", 0.10, 0.03),
          "Horizon (20..50 yr)": ("horizon", 20, 50),
          "Response-crew saving (0..1.35 M/yr site)": ("resp", 0.0, 1.35),
          "Fixed cost per event (0.1..2 M)": ("fixed", 0.1, 2.0)}
base_npv = npv_det(base)
tor = []
for lab, (k, lo, hi) in swings.items():
    vlo = npv_det({**base, k: lo})
    vhi = npv_det({**base, k: hi})
    tor.append((lab, vlo, vhi))
tor.sort(key=lambda t: abs(t[2] - t[1]))
R["T3_tornado_caseA_S1_r6"] = {"base_npv_musd": round(base_npv, 1),
                               "swings": {l: [round(a_, 1), round(b_, 1)] for l, a_, b_ in tor}}

fig, ax = plt.subplots(figsize=(8.6, 5.2))
for i, (lab, vlo, vhi) in enumerate(tor):
    ax.barh(i, vlo - base_npv, left=base_npv, color=C2, height=0.6, label="first value in label" if i == 0 else None)
    ax.barh(i, vhi - base_npv, left=base_npv, color=C1, height=0.6, label="second value in label" if i == 0 else None)
ax.axvline(base_npv, color=INK, lw=1)
ax.axvline(0, color=GREY, lw=1, ls="--")
ax.set_yticks(range(len(tor)))
ax.set_yticklabels([t[0] for t in tor], fontsize=8.5)
ax.set_xlabel("NPV, USD M (4 units, 6%, Case A capex)")
ax.set_title(f"Tornado: what moves JAZR's NPV (base = prone-site rate {lam_prone:.3f}/yr, NPV {base_npv:.0f} M)",
             fontsize=10, loc="left", color=INK)
ax.legend(frameon=False, loc="lower right", fontsize=8, title="dashed line = NPV 0", title_fontsize=8)
fig.tight_layout()
fig.savefig(os.path.join(CH, "tornado_npv.png"), dpi=150)
plt.close(fig)

# P(payback) vs event rate curve
lams = np.geomspace(0.005, 3, 30)
fig, ax = plt.subplots(figsize=(8, 4.6))
curve = {}
for case, col in (("A", C1), ("B", C2)):
    ps = []
    for lv in lams:
        s = E.simulate(n=3000, case=case, units=4, lam_fixed=lv, seed=9, rates=(0.06,))
        ps.append(float((s["npv_0.06"] > 0).mean()))
    curve[case] = ps
    ax.plot(lams, ps, color=col, lw=2, label=f"Case {case} ({'v3 AED 30-80 M/unit' if case == 'A' else 'bottom-up'})")
for nm, lv in (("S0 the plant posterior mean", ap / bp), ("S1 prone site", lam_prone), ("S2 Hanul", 9 / 11),
               ("S3 Gravelines", 1.5)):
    ax.axvline(lv, color=GREY, lw=1, ls=":")
    ax.text(lv * 1.06, 0.97, nm, rotation=90, fontsize=7.5, color=INK2, va="top", ha="left")
ax.set_xscale("log")
ax.set_ylim(0, 1)
ax.set_xlabel("Generation-affecting jellyfish events per site-year at the plant (log)")
ax.set_ylabel("P(NPV > 0) at 6%, 30 yr")
ax.legend(frameon=False, loc="center right")
fig.tight_layout()
fig.savefig(os.path.join(CH, "payback_probability_vs_event_rate.png"), dpi=150)
plt.close(fig)
R["T3_payback_curve"] = {"lambda": lams.round(4).tolist(), **{f"P_case{k}": v for k, v in curve.items()}}

# NPV histograms, S2 Hanul-like, 6%
fig, ax = plt.subplots(figsize=(8, 4.2))
for case, col in (("A", C1), ("B", C2)):
    v = sims[(case, list(SCEN)[2], "full")]["npv_0.06"]
    ax.hist(v, bins=80, color=col, alpha=0.75, label=f"Case {case}: P(NPV>0) = {(v > 0).mean():.0%}")
ax.axvline(0, color=INK, lw=1)
ax.set_xlabel("NPV, USD M (4 units, 6%, 30 yr) under S2 Hanul-like event rate 0.82/yr")
ax.set_ylabel("Monte Carlo draws")
ax.legend(frameon=False)
fig.tight_layout()
fig.savefig(os.path.join(CH, "npv_hist_S2.png"), dpi=150)
plt.close(fig)

# ------------------------------------------------------------- T4 alternatives (table only; read CSV)
R["T4_alternatives_rows"] = sum(1 for _ in open(os.path.join(HERE, "data", "alternatives.csv"))) - 1

# ------------------------------------------------------------- T5 phasing / real options
ro = {}
for case in "AB":
    for sk in list(SCEN):
      for learner in ("bayes", "observed"):
        o = E.real_option(n=N, case=case, lam_fixed=SCEN[sk], learner=learner)
        ro[f"{case}-{sk.split(' ')[0]}-{learner}"] = {
            "E[NPV] full now": round(float(o["full_now"].mean()), 1),
            "E[NPV] pilot only": round(float(o["pilot_only"].mean()), 1),
            "E[NPV] pilot + option to expand": round(float(o["pilot_option"].mean()), 1),
            "P(expand)": round(float(o["p_expand"]), 3),
            "option value vs full now": round(float(o["pilot_option"].mean() - o["full_now"].mean()), 1),
            "option value vs pilot only": round(float(o["pilot_option"].mean() - o["pilot_only"].mean()), 1)}
R["T5_phasing_real_option_r6"] = ro

# ------------------------------------------------------------- T6 emissions
erows, etot, kw_mode, emb = E.emissions_table_modes()
cmp_ = E.emissions_compare_site_modes()
aud = E.avoided_outage_tco2_per_unit_day()
s_exp = sims[("A", list(SCEN)[0], "full")]
s_pr = sims[("A", list(SCEN)[1], "full")]
R["T6_emissions"] = {"per_unit_rows_tco2_yr": {k: round(v, 1) for k, v in erows},
                     "line_power_kw_mode": round(kw_mode), "embodied_tco2_per_unit": round(emb),
                     "site_compare_tco2_yr": {k: round(v, 1) for k, v in cmp_.items()},
                     "avoided_tco2_per_unit_day_outage": round(aud),
                     "avoided_tco2_yr_S0_mean": round(float(s_exp["ud_avoided_total"].mean() / 28 * aud)),
                     "avoided_tco2_yr_S1_mean": round(float(s_pr["ud_avoided_total"].mean() / 28 * aud)),
                     "avoided_tco2_yr_S2_mean": round(float(sims[("A", list(SCEN)[2], "full")]["ud_avoided_total"].mean() / 28 * aud))}
op4 = erows[0][1] * 4
for sc in ("S0", "S1", "S2"):
    net = R["T6_emissions"][f"avoided_tco2_yr_{sc}_mean"] - op4
    R["T6_emissions"][f"carbon_payback_years_{sc}"] = round(emb * 4 / net, 1) if net > 0 else None
fig, ax = plt.subplots(figsize=(8, 3.8))
labs = list(cmp_.keys()) + ["Avoided outages, S1 prone site (JAZR, 4 units)"]
vals = list(cmp_.values()) + [-R["T6_emissions"]["avoided_tco2_yr_S1_mean"]]
cols = [C1, GREY, C2, C2, C3]
ax.barh(range(len(vals)), vals, color=cols, height=0.6)
for i, v in enumerate(vals):
    ax.text(v if v >= 0 else -150, i, f" {v:,.0f} " if v >= 0 else f"{v:,.0f}", va="center",
            ha="left" if v >= 0 else "right", fontsize=8.5, color=INK if v >= 0 else "#ffffff")
ax.set_yticks(range(len(vals)))
ax.set_yticklabels(labs, fontsize=8.5)
ax.set_xscale("symlog", linthresh=100)
ax.set_xlabel("tCO2 per year per site (negative = avoided), mode values, symlog")
ax.axvline(0, color=INK, lw=0.8)
fig.tight_layout()
fig.savefig(os.path.join(CH, "emissions_compare.png"), dpi=150)
plt.close(fig)

# ------------------------------------------------------------- T7 rubric
rub = list(csv.DictReader(open(os.path.join(HERE, "data", "rubric.csv"))))
def wscore(col):
    return round(sum(float(r["weight"]) * float(r[col]) / 10 for r in rub), 1)
R["T7_rubric"] = {c: wscore(c) for c in ("v3_self_score", "redteam_score_with_tank", "redteam_score_no_tank",
                                         "benchmark_estimate")}

# ------------------------------------------------------------- T8 regulatory summary
reg = list(csv.DictReader(open(os.path.join(HERE, "data", "regulatory_checklist.csv"))))
R["T6b_regulatory_counts"] = {s: sum(1 for r in reg if r["status"] == s) for s in ("PASS", "RISK", "N/A")}

with open(os.path.join(OUT, "results.json"), "w") as f:
    json.dump(R, f, indent=1, default=float)
print(json.dumps(R, indent=1, default=float))
