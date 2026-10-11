"""JAZR Gate v3 - economics, risk and emissions model (05_economics_risk).

Pure functions; run_all.py produces the outputs. Every input lives in inputs.py with its source label.
Monetary unit: USD million (M) unless stated; AED shown via the fixed peg.
"""
from __future__ import annotations
import csv
import math
import os
import numpy as np
from scipy.optimize import minimize
from scipy.special import gammaln

import inputs as I

HERE = os.path.dirname(os.path.abspath(__file__))
CURRENT_YEAR = 2026.75
CLOSED = {"Fugen ATR": 2003, "Hunterston": 2022, "Chinshan": 2019, "Kuosheng": 2023, "Maanshan": 2025}


# ---------------------------------------------------------------- helpers
def tri(rng, lmh, n):
    lo, mo, hi = lmh
    if hi == lo:
        return np.full(n, lo)
    return rng.triangular(lo, mo, hi, n)


def tri_mean(lmh):
    return sum(lmh) / 3.0


def crf(r, n):
    """Capital recovery factor."""
    if r == 0:
        return 1.0 / n
    return r * (1 + r) ** n / ((1 + r) ** n - 1)


def annuity_pv(r, n):
    return 1.0 / crf(r, n)


# ---------------------------------------------------------------- incident data
def load_sites():
    rows = []
    with open(os.path.join(HERE, "data", "site_event_counts.csv")) as f:
        for r in csv.DictReader(f):
            end = next((v for k, v in CLOSED.items() if r["site"].startswith(k)), CURRENT_YEAR)
            T = max(end - float(r["first_cod_year_approx"]), 1.0)
            rows.append(dict(site=r["site"], n=int(r["n_gen_events"]), T=T))
    return rows


def load_severity():
    rows = []
    with open(os.path.join(HERE, "data", "event_severity.csv")) as f:
        for r in csv.DictReader(f):
            rows.append((float(r["unit_days_low"]), float(r["unit_days_high"])))
    return np.array(rows)


def fit_gamma_poisson(sites):
    """MLE of Gamma(alpha, beta) prior on site event rate (events/site-yr) from counts n_i over exposure T_i
    (negative-binomial marginal likelihood)."""
    n = np.array([s["n"] for s in sites], float)
    T = np.array([s["T"] for s in sites], float)

    def nll(p):
        a, b = np.exp(p)
        ll = (gammaln(n + a) - gammaln(a) - gammaln(n + 1)
              + a * np.log(b / (b + T)) + n * np.log(T / (b + T)))
        return -ll.sum()

    res = minimize(nll, x0=np.log([0.5, 10.0]), method="Nelder-Mead")
    a, b = np.exp(res.x)
    return float(a), float(b)


def site_posterior(a, b, n_obs=0, T_obs=I.PLANT["site_site_years_observed"]):
    return a + n_obs, b + T_obs


# ---------------------------------------------------------------- cost model
def capex_case_b(rng, n):
    direct = sum(tri(rng, v, n) for v in I.CAPEX_COMPONENTS_MUSD.values())
    eng = tri(rng, I.CAPEX_MARKUPS["engineering_nuclearQA_licensing_seismic"], n)
    cont = tri(rng, I.CAPEX_MARKUPS["contingency"], n)
    total = direct * (1 + eng) * (1 + cont)
    return direct, total


def capex_case_a(rng, n):
    total = tri(rng, I.CAPEX_CASE_A_AED_M, n) / I.AED_PER_USD
    direct = total / 1.6  # implied direct share (assumes ~60% markups, consistent with case B modes)
    return direct, total


def line_power_kw(rng, n):
    P = I.POWER
    head = tri(rng, P["screw_head_m"], n)
    eff = tri(rng, P["screw_eff"], n)
    screw = 1025 * 9.81 * P["flow_m3s"] * head / eff / 1000.0
    return screw + tri(rng, P["pipe_pump_kw"], n) + tri(rng, P["aux_kw"], n)


def opex_per_unit(rng, n, direct, price):
    O = I.OPEX
    kw = line_power_kw(rng, n)
    hours = tri(rng, O["operating_hours"], n)
    energy_musd = kw * hours / 1000.0 * price / 1e6  # MWh x USD/MWh
    return (direct * tri(rng, O["maintenance_frac_of_direct"], n)
            + tri(rng, O["staff_drills_musd"], n)
            + tri(rng, O["pigging_inspection_musd"], n)
            + energy_musd), kw, hours


def cost_table_modes():
    """Deterministic cost table at mode values (Case B) - used in README and pytest consistency checks."""
    rows = [(k, v[1]) for k, v in I.CAPEX_COMPONENTS_MUSD.items()]
    direct = sum(v for _, v in rows)
    eng = direct * I.CAPEX_MARKUPS["engineering_nuclearQA_licensing_seismic"][1]
    cont = (direct + eng) * I.CAPEX_MARKUPS["contingency"][1]
    total = direct + eng + cont
    rows += [("SUBTOTAL direct", direct), ("engineering/nuclear QA/licensing/seismic", eng),
             ("contingency", cont), ("TOTAL per unit", total)]
    return rows, direct, total


def cost_table_ranges():
    """Low / mode / high per component + total (low & high totals use all-low / all-high, a bounding case)."""
    out = []
    for i, lab in enumerate(("low", "mode", "high")):
        d = sum(v[i] for v in I.CAPEX_COMPONENTS_MUSD.values())
        t = d * (1 + I.CAPEX_MARKUPS["engineering_nuclearQA_licensing_seismic"][i]) * \
            (1 + I.CAPEX_MARKUPS["contingency"][i])
        out.append((lab, d, t))
    return out


# ---------------------------------------------------------------- benefit model
def simulate(n=20000, seed=7, case="B", units=4, horizon=None, rates=None, outer_guide=False,
             reach_override=None, lam_scale=1.0, return_paths=False, lam_fixed=None):
    """Monte Carlo of NPV for building JAZR on `units` units now.

    Each draw: a true site event rate lambda ~ the plant posterior; for each year events ~ Poisson(lambda);
    severity per event bootstrapped from the global catalogue (uniform in each event's [low, high] unit-days);
    a share units/4 of each site event's unit-days is on JAZR-protected units (events hit units independently).
    JAZR scales protected losses by m = A*(reach/0.95) + (1-A).
    """
    rng = np.random.default_rng(seed)
    horizon = horizon or I.ECON["horizon_years"]
    rates = rates or I.ECON["discount_rates"]
    build = I.ECON["build_years"]
    a, b = fit_gamma_poisson(load_sites())
    ap, bp = site_posterior(a, b)
    lam = rng.gamma(ap, 1.0 / bp, n) * lam_scale
    if lam_fixed is not None:
        lam = np.full(n, float(lam_fixed))
    sev = load_severity()
    price = tri(rng, I.ECON["value_usd_per_mwh"], n)
    fixed = tri(rng, I.ECON["fixed_cost_per_event_musd"], n)
    reach = tri(rng, I.JAZR["reach_frac"], n) if reach_override is None else np.full(n, reach_override)
    avail = tri(rng, I.JAZR["availability"], n)
    m = avail * np.minimum(reach / I.JAZR["reach_frac_today"], 1.0) + (1 - avail)
    resp = tri(rng, I.ECON["response_cost_musd_per_site_yr"], n) * tri(rng, I.ECON["response_cost_saved_frac"], n)

    direct, capex_u = (capex_case_b if case == "B" else capex_case_a)(rng, n)
    capex = capex_u * units
    if outer_guide:
        capex = capex + tri(rng, I.OUTER_GUIDE_MUSD_SITE, n) * (units / 4.0)
    opex_u, kw, hours = opex_per_unit(rng, n, direct, price)
    opex = opex_u * units
    ud_mwh = I.unit_day_mwh()
    share = units / 4.0

    annual_benefit = np.zeros((horizon, n))
    annual_ud_avoided = np.zeros((horizon, n))
    for y in range(horizon):
        k = rng.poisson(lam)
        kmax = int(k.max()) if k.size else 0
        ud = np.zeros(n)
        if kmax > 0:
            idx = rng.integers(0, len(sev), (n, kmax))
            u = rng.random((n, kmax))
            draws = sev[idx, 0] + u * (sev[idx, 1] - sev[idx, 0])
            mask = np.arange(kmax)[None, :] < k[:, None]
            ud = (draws * mask).sum(1)
        loss = ud * share * ud_mwh * price / 1e6 + k * share * fixed  # USD M on protected units
        avoided = loss * (1 - m)
        if y >= I.ECON["build_years"]:  # no protection while building
            annual_benefit[y] = avoided + resp * share
            annual_ud_avoided[y] = ud * share * (1 - m)

    res = {"lambda": lam, "capex": capex, "opex": opex, "price": price, "reach": reach, "avail": avail,
           "m": m, "kw": kw, "hours": hours, "alpha": a, "beta": b, "alpha_post": ap, "beta_post": bp,
           "ud_avoided_total": annual_ud_avoided.sum(0), "benefit_mean_yr": annual_benefit.mean(0)}
    for r in rates:
        cf = np.zeros(n)
        disc_years = np.arange(horizon)
        # capex spread evenly over build years (years 0..build-1); opex + benefits from year `build`
        for y in range(build):
            cf -= capex / build / (1 + r) ** y
        for y in range(build, horizon):
            cf += (annual_benefit[y] - opex) / (1 + r) ** y
        res[f"npv_{r}"] = cf
        # discounted payback year
        cum = np.zeros(n)
        pay = np.full(n, np.inf)
        for y in range(horizon):
            flow = -(capex / build) if y < build else (annual_benefit[y] - opex)
            cum += flow / (1 + r) ** y
            hit = (cum >= 0) & np.isinf(pay)
            pay[hit] = y
        res[f"payback_{r}"] = pay
    if return_paths:
        res["annual_benefit"] = annual_benefit
    return res


def expected_annual_loss_site(lam_mean, sev_mean_ud, price, fixed):
    """USD M per site-year, no JAZR."""
    return lam_mean * (sev_mean_ud * I.unit_day_mwh() * price / 1e6 + fixed)


def breakeven_unit_days_per_year(capex_unit, opex_unit, price, m, r, horizon, resp_saving_unit=0.0):
    """Unit-days of outage per protected unit per year (WITHOUT JAZR) needed for NPV=0 (annualised, ignores
    build delay and fixed event costs -> slightly favourable to JAZR)."""
    ann_cost = capex_unit * crf(r, horizon) + opex_unit - resp_saving_unit
    value_ud = I.unit_day_mwh() * price / 1e6 * (1 - m)
    return ann_cost / value_ud


# ---------------------------------------------------------------- real option
def real_option(n=20000, seed=11, case="B", r=0.06, decision_year=4, lam_fixed=None, learner="bayes"):
    """Pilot on 1 unit now; at `decision_year` the team knows the true reach (pilot-measured) and the pilot's true
    cost, and has updated lambda with the site's observed events; expand to 3 more units only if the expected NPV of
    expansion > 0. Compares with full rollout now and do-nothing."""
    rng = np.random.default_rng(seed)
    H = I.ECON["horizon_years"]
    a, b = fit_gamma_poisson(load_sites())
    ap, bp = site_posterior(a, b)
    lam = rng.gamma(ap, 1.0 / bp, n) if lam_fixed is None else np.full(n, float(lam_fixed))
    sev = load_severity()
    sev_mean = sev.mean()  # mean of uniform midpoints
    price = tri(rng, I.ECON["value_usd_per_mwh"], n)
    fixed = tri(rng, I.ECON["fixed_cost_per_event_musd"], n)
    reach = tri(rng, I.JAZR["reach_frac"], n)
    avail = tri(rng, I.JAZR["availability"], n)
    m = avail * reach / I.JAZR["reach_frac_today"] + (1 - avail)
    resp = tri(rng, I.ECON["response_cost_musd_per_site_yr"], n) * tri(rng, I.ECON["response_cost_saved_frac"], n)
    direct, capex_u = (capex_case_b if case == "B" else capex_case_a)(rng, n)
    opex_u, _, _ = opex_per_unit(rng, n, direct, price)

    def unit_benefit(lmb):  # expected USD M per protected unit-year
        return lmb * 0.25 * (sev_mean * I.unit_day_mwh() * price / 1e6 + fixed) * (1 - m) + resp * 0.25

    def npv_units(units, start, lmb):
        v = -capex_u * units * sum(1 / (1 + r) ** (start + y) for y in range(2)) / 2
        v += (unit_benefit(lmb) * units - opex_u * units) * sum(1 / (1 + r) ** y for y in range(start + 2, H))
        return v

    full_now = npv_units(4, 0, lam)
    pilot_only = npv_units(1, 0, lam)
    obs = rng.poisson(lam * decision_year)
    if learner == "bayes":   # team keeps the global-catalogue prior (sceptical)
        lam_upd = (ap + obs) / (bp + decision_year)
    else:                    # team trusts site data only (Jeffreys prior)
        lam_upd = (0.5 + obs) / decision_year
    exp_expand = npv_units(3, decision_year, lam_upd)  # what the team expects
    expand = exp_expand > 0
    true_expand = npv_units(3, decision_year, lam)
    pilot_option = pilot_only + np.where(expand, true_expand, 0.0)
    return dict(full_now=full_now, pilot_only=pilot_only, pilot_option=pilot_option, p_expand=expand.mean())


# ---------------------------------------------------------------- emissions
def emissions_table_modes():
    """tCO2 per year per unit-line at mode values. Returns rows + total; used in README and pytest."""
    E, P, O = I.EMIS, I.POWER, I.OPEX
    kw = 1025 * 9.81 * P["flow_m3s"] * P["screw_head_m"][1] / P["screw_eff"][1] / 1000 + P["pipe_pump_kw"][1] + \
        P["aux_kw"][1]
    op = kw * O["operating_hours"][1] / 1000 * E["grid_kg_per_kwh"][1]  # MWh * t/MWh
    emb = (E["steel_t"][1] * E["steel_t_per_t"][1] + E["hdpe_t"][1] * E["hdpe_t_per_t"][1]
           + E["concrete_ballast_t"][1] * E["concrete_t_per_t"][1] + E["marine_install_tco2"][1])
    emb_yr = emb / I.ECON["horizon_years"]
    rows = [("JAZR operation (electricity, displaced gas), per unit", op),
            ("JAZR embodied (steel+HDPE+concrete+install)/30 yr, per unit", emb_yr)]
    total = op + emb_yr
    rows.append(("JAZR TOTAL per unit-yr", total))
    return rows, total, kw, emb


def emissions_compare_site_modes():
    """tCO2/yr per SITE (4 units) at modes, for comparison chart."""
    E = I.EMIS
    rows, jazr_unit, kw, emb = emissions_table_modes()
    boats = E["boats"][1] * E["boat_days_per_bloom"][1] * 24 * E["boat_l_per_h"][1] * E["diesel_kg_per_l"] / 1000 \
        * E["blooms_per_year"][1]
    q_new = E["bubblecurtain_tco2_per_event_reported"] * E["blooms_per_year"][1]
    hours_evt = E["bubblecurtain_mwh_per_event"] / E["bubblecurtain_kw_new"] * 1000
    q_old = E["bubblecurtain_kw_old"] * hours_evt / 1000 * E["grid_kg_per_kwh"][1] * E["blooms_per_year"][1]
    return {"JAZR (4 lines, op+embodied)": jazr_unit * 4,
            "Status quo boats (diesel)": boats,
            "Bubble curtain 440 kW (their 12.6 t/event)": q_new,
            "Bubble curtain 135 kW (older figure)": q_old}


def avoided_outage_tco2_per_unit_day():
    return I.unit_day_mwh() * I.EMIS["grid_kg_per_kwh"][1]  # MWh * t/MWh


def breakeven_lambda(capex_unit, opex_unit, price, m, r, horizon, fixed, resp_unit, sev_mean):
    """Site event rate (events/site-yr) at which annualised NPV of protecting ONE unit = 0."""
    ann_cost = capex_unit * crf(r, horizon) + opex_unit - resp_unit
    per_event_unit = 0.25 * (sev_mean * I.unit_day_mwh() * price / 1e6 + fixed) * (1 - m)
    return ann_cost / per_event_unit
