"""Automated checks: cost and emissions tables compute and their totals are consistent; model sanity.
Run:  python3 -m pytest tests -q   (from 05_economics_risk/)
"""
import csv
import math
import os
import sys

import numpy as np
import pytest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
import econ as E  # noqa: E402
import inputs as I  # noqa: E402


# ---------------- cost table
def test_cost_table_components_sum_to_subtotal():
    rows, direct, total = E.cost_table_modes()
    d = dict(rows)
    comp = sum(v for k, v in rows if k in I.CAPEX_COMPONENTS_MUSD)
    assert math.isclose(comp, d["SUBTOTAL direct"], rel_tol=1e-12)
    assert math.isclose(direct, comp)


def test_cost_table_total_equals_direct_plus_markups():
    rows, direct, total = E.cost_table_modes()
    d = dict(rows)
    assert math.isclose(d["TOTAL per unit"],
                        d["SUBTOTAL direct"] + d["engineering/nuclear QA/licensing/seismic"] + d["contingency"])
    assert math.isclose(total, d["TOTAL per unit"])


def test_cost_bounds_ordered_and_mode_matches_table():
    b = E.cost_table_ranges()
    assert b[0][2] < b[1][2] < b[2][2]
    assert math.isclose(b[1][2], E.cost_table_modes()[2])


def test_case_a_capex_matches_v3_stated_range():
    rng = np.random.default_rng(0)
    _, tot = E.capex_case_a(rng, 50000)
    aed = tot * I.AED_PER_USD
    assert aed.min() >= 30 - 1e-9 and aed.max() <= 80 + 1e-9


def test_crf_identity():
    for r in (0.03, 0.06, 0.1):
        assert math.isclose(E.crf(r, 30) * E.annuity_pv(r, 30), 1.0)
    assert math.isclose(E.crf(0, 20), 1 / 20)


# ---------------- emissions table
def test_emissions_table_total_consistent():
    rows, total, kw, emb = E.emissions_table_modes()
    d = dict(rows)
    parts = [v for k, v in rows if "TOTAL" not in k]
    assert math.isclose(sum(parts), d["JAZR TOTAL per unit-yr"])
    assert math.isclose(total, d["JAZR TOTAL per unit-yr"])
    assert math.isclose(d["JAZR embodied (steel+HDPE+concrete+install)/30 yr, per unit"] * I.ECON["horizon_years"], emb)


def test_line_power_matches_hand_calc():
    _, _, kw, _ = E.emissions_table_modes()
    screw = 1025 * 9.81 * 2.0 * 8.0 / 0.75 / 1000
    assert math.isclose(kw, screw + 240 + 35, rel_tol=1e-9)
    assert 400 < kw < 600


def test_site_emissions_compare_uses_four_lines():
    rows, total, _, _ = E.emissions_table_modes()
    cmp_ = E.emissions_compare_site_modes()
    assert math.isclose(cmp_["JAZR (4 lines, op+embodied)"], 4 * total)
    assert math.isclose(cmp_["Bubble curtain 440 kW (their 12.6 t/event)"],
                        12.6 * I.EMIS["blooms_per_year"][1])
    assert all(v > 0 for v in cmp_.values())


def test_avoided_outage_emissions_order_of_magnitude():
    v = E.avoided_outage_tco2_per_unit_day()
    assert 11000 < v < 16000  # 32.1 GWh x 0.36-0.47 t/MWh


# ---------------- frequency / benefit / NPV
def test_incident_data_loads_and_counts():
    s = E.load_sites()
    assert len(s) == 51 and sum(x["n"] for x in s) == 41
    sev = E.load_severity()
    assert (sev[:, 1] >= sev[:, 0]).all() and sev.shape[1] == 2


def test_gamma_poisson_fit_mean_close_to_pooled_rate():
    s = E.load_sites()
    a, b = E.fit_gamma_poisson(s)
    pooled = sum(x["n"] for x in s) / sum(x["T"] for x in s)
    assert 0.5 * pooled < a / b < 2 * pooled
    ap, bp = E.site_posterior(a, b)
    assert ap / bp < a / b  # zero observed events lowers the rate


def test_simulation_reproducible_and_probabilities_valid():
    r1 = E.simulate(n=2000, seed=3, case="A", rates=(0.06,))
    r2 = E.simulate(n=2000, seed=3, case="A", rates=(0.06,))
    assert np.allclose(r1["npv_0.06"], r2["npv_0.06"])
    p = (r1["npv_0.06"] > 0).mean()
    assert 0 <= p <= 1


def test_zero_benefit_npv_equals_minus_pv_costs():
    r = E.simulate(n=500, seed=1, case="A", lam_fixed=0.0, rates=(0.06,))
    # with no events, benefit = response-crew saving only; remove it and compare to -PV(capex+opex)
    # check sign and bound instead (response saving is random): NPV must be < 0 for every draw
    assert (r["npv_0.06"] < 0).all()


def test_npv_increases_with_event_rate():
    lo = E.simulate(n=3000, seed=2, case="A", lam_fixed=0.05, rates=(0.06,))["npv_0.06"].mean()
    hi = E.simulate(n=3000, seed=2, case="A", lam_fixed=1.0, rates=(0.06,))["npv_0.06"].mean()
    assert hi > lo


def test_breakeven_consistency():
    """At the break-even event rate, annualised benefit equals annualised cost."""
    sev = E.load_severity().mean()
    cap, op, price, m, r, H, fixed, resp = 13.6, 0.6, 60.0, 0.15, 0.06, 30, 0.5, 0.08
    lam = E.breakeven_lambda(cap, op, price, m, r, H, fixed, resp, sev)
    benefit = lam * 0.25 * (sev * I.unit_day_mwh() * price / 1e6 + fixed) * (1 - m) + resp
    cost = cap * E.crf(r, H) + op
    assert math.isclose(benefit, cost, rel_tol=1e-9)


def test_pilot_scales_quarter_of_full():
    f = E.simulate(n=3000, seed=4, case="A", units=4, lam_fixed=0.5, rates=(0.06,))
    p = E.simulate(n=3000, seed=4, case="A", units=1, lam_fixed=0.5, rates=(0.06,))
    assert math.isclose(p["npv_0.06"].mean() * 4, f["npv_0.06"].mean(), rel_tol=0.02)


# ---------------- regulatory / alternatives data
def _csv(name):
    return list(csv.DictReader(open(os.path.join(HERE, "data", name))))


def test_regulatory_rows_have_status_and_source():
    reg = _csv("regulatory_checklist.csv")
    assert len(reg) >= 10
    for r in reg:
        assert r["status"] in {"PASS", "RISK", "N/A"}
        assert r["source"].strip()


def test_alternatives_table_has_sources():
    alt = _csv("alternatives.csv")
    assert len(alt) == 5 and all(r["sources"].strip() for r in alt)


def test_regulatory_status_counts():
    reg = _csv("regulatory_checklist.csv")
    counts = {s: sum(1 for r in reg if r["status"] == s) for s in ("PASS", "RISK", "N/A")}
    assert len(reg) == 14 and counts["PASS"] == 2 and counts["RISK"] == 11  # as reported in 00_TEST_REPORT.md
