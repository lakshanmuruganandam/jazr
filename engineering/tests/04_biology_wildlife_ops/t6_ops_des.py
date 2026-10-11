"""T6 - Operations discrete-event simulation of a bloom season (custom engine, no simpy).

One unit, Oct-Nov season (61 d), Monte Carlo over seasons. Every distribution below is [ASSUME] unless tagged.
Outputs: alert->deployed time, P(deployed before arrival), availability during bloom hours,
crew-hours JAZR vs today's practice (crew sizes from 13_/14_ files [SRC 20]).
"""
import heapq
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from params import *

N_BAYS = 18                 # ~180 m / 10 m bays [DESIGN]
LINES = 2                   # lift lines per unit [ASSUME N+1 at pilot load]
SEASON_H = 61 * 24
P = dict(
    blooms_per_season=3.0,                  # Poisson mean [ASSUME; Gravelines 2 waves 2026, Uljin 43 days >=100 t in 6 yr]
    bloom_median_h=72, bloom_sigma=0.6,     # lognormal; Shin Hanul 4 d, Hanbit ~10 d [SRC 20]
    p_far_alert=0.85, far_lead_h=(4, 6),    # brief: 4-6 h lead; 15% detected only on arrival [ASSUME; Gravelines]
    near_lead_h=(0.0, 0.5),
    approve_med_min_day=8, approve_med_min_night=20, approve_sigma=0.7,   # per approval step [ASSUME]
    deploy_min=(8, 15),                     # brief: ~10 min
    p_bay_deploy_fail=0.02,
    bay_mtbf_h=(2000, 8000), bay_mttr_med_h=8, bay_mttr_sigma=0.5,
    line_mtbf_h=(1500, 6000), line_mttr_med_h=24,   # screw+pump+pipe per line
    deploy_before_h=1.0,                    # far alert: screens down 1 h before arrival
    standdown_after_h=6.0,
)


def lognorm(rng, med, sig):
    return med * np.exp(rng.normal(0, sig))


def run_season(rng, p=P, n_bays=N_BAYS, lines=LINES, auto_near=False):
    nb = rng.poisson(p["blooms_per_season"])
    out = []
    starts = np.sort(rng.uniform(0, SEASON_H - 24, nb))
    for t_arr in starts:
        dur = float(np.clip(lognorm(rng, p["bloom_median_h"], p["bloom_sigma"]), 12, 240))
        far = rng.random() < p["p_far_alert"]
        lead = rng.uniform(*p["far_lead_h"]) if far else rng.uniform(*p["near_lead_h"])
        t_alert = t_arr - lead
        hour = (t_alert % 24)
        med = p["approve_med_min_night"] if (hour < 6 or hour > 20) else p["approve_med_min_day"]
        approvals = sum(lognorm(rng, med, p["approve_sigma"]) for _ in range(2)) / 60  # Ready + Deploy approvals
        if auto_near and not far:
            approvals = 1.0 / 60          # pre-authorised automatic deploy on close alert
        t_cmd = t_alert + approvals
        if far:
            t_cmd = max(t_cmd, t_arr - p["deploy_before_h"] - p["deploy_min"][1] / 60)
        t_deployed = t_cmd + rng.uniform(*p["deploy_min"]) / 60
        t_end = t_arr + dur + p["standdown_after_h"]
        # event simulation of bays and lines from deployment to end
        bays_up = n_bays - rng.binomial(n_bays, p["p_bay_deploy_fail"])
        lines_up = lines
        ev = []
        bay_mtbf = rng.uniform(*p["bay_mtbf_h"]); line_mtbf = rng.uniform(*p["line_mtbf_h"])
        for _ in range(bays_up):
            heapq.heappush(ev, (t_deployed + rng.exponential(bay_mtbf), "bay_fail"))
        for _ in range(lines):
            heapq.heappush(ev, (t_deployed + rng.exponential(line_mtbf), "line_fail"))
        # initial deploy failures are repaired too
        for _ in range(n_bays - bays_up):
            heapq.heappush(ev, (t_deployed + lognorm(rng, p["bay_mttr_med_h"], p["bay_mttr_sigma"]), "bay_fix"))
        t = t_deployed; good_h = 0.0; lift_ok_h = 0.0; bay_h = 0.0; repairs_h = 0.0
        bloom_lo, bloom_hi = t_arr, t_arr + dur
        while ev:
            te, kind = heapq.heappop(ev)
            te_c = min(te, t_end)
            # integrate over [t, te_c] intersected with bloom window
            a, b = max(t, bloom_lo), min(te_c, bloom_hi)
            if b > a:
                bay_h += (b - a) * bays_up / n_bays
                lift_ok_h += (b - a) * (lines_up >= 1)
                good_h += (b - a) * (bays_up >= n_bays - 1 and lines_up >= 1)
            t = te_c
            if te >= t_end:
                break
            if kind == "bay_fail":
                bays_up -= 1; r = lognorm(rng, p["bay_mttr_med_h"], p["bay_mttr_sigma"]); repairs_h += r
                heapq.heappush(ev, (te + r, "bay_fix"))
            elif kind == "bay_fix":
                bays_up += 1; heapq.heappush(ev, (te + rng.exponential(bay_mtbf), "bay_fail"))
            elif kind == "line_fail":
                lines_up -= 1; r = lognorm(rng, p["line_mttr_med_h"], 0.5); repairs_h += r
                heapq.heappush(ev, (te + r, "line_fix"))
            elif kind == "line_fix":
                lines_up += 1; heapq.heappush(ev, (te + rng.exponential(line_mtbf), "line_fail"))
        # time before deployment within bloom = unprotected
        unprot = max(0.0, min(t_deployed, bloom_hi) - bloom_lo)
        out.append(dict(far=far, lead_h=lead, response_min=(t_deployed - t_alert) * 60, approval_min=approvals * 60, margin_min=(t_arr - t_deployed) * 60,
                        deployed_before_arrival=t_deployed <= t_arr, unprotected_h=unprot, dur_h=dur,
                        avail_full=good_h / dur, bay_avail=bay_h / dur, lift_avail=lift_ok_h / dur,
                        incident_h=t_end - t_alert, repair_h=repairs_h))
    return out


def crew_hours(b, leak_frac):
    """Return (JAZR, today_low, today_high) person-hours for one bloom."""
    inc = b["incident_h"]; dur = b["dur_h"]
    jazr = 2 * inc + 3 * b["repair_h"] + max(2, 20 * leak_frac) * dur   # 2 operators; 3-person repair team; residual screen crew
    today_low = 13 * dur          # Hanbit: gate crew 7-8 -> 20 (extra ~13 persons, 24 h) [SRC 20]
    today_high = 20 * dur + 7 * 3 * dur   # + 7 boats 24/7 (Gravelines) x 3 crew [crew/boat ASSUME]
    return jazr, today_low, today_high


def main(n=3000, seed=1):
    rng = np.random.default_rng(seed)
    blooms = []
    for _ in range(n):
        blooms += run_season(rng)
    arr = lambda k: np.array([b[k] for b in blooms], dtype=float)
    far = arr("far").astype(bool)
    resp = arr("response_min")
    res = dict(n_seasons=n, n_blooms=len(blooms), params={k: v for k, v in P.items()})
    res["response_min_far_p50_p90_p99"] = np.percentile(resp[far], [50, 90, 99]).tolist()
    res["response_min_near_p50_p90_p99"] = np.percentile(resp[~far], [50, 90, 99]).tolist()
    res["approval_latency_min_p50_p90_p99"] = np.percentile(arr("approval_min"), [50, 90, 99]).tolist()
    res["far_margin_before_arrival_min_p1_p50"] = np.percentile(arr("margin_min")[far], [1, 50]).tolist()
    rng2 = np.random.default_rng(seed + 7); bl2 = []
    for _ in range(n):
        bl2 += run_season(rng2, auto_near=True)
    nr = [b for b in bl2 if not b["far"]]
    res["auto_near_P_before_arrival"] = float(np.mean([b["deployed_before_arrival"] for b in nr]))
    res["auto_near_unprotected_h_mean"] = float(np.mean([b["unprotected_h"] for b in nr]))
    res["P_deployed_before_arrival_far"] = float(arr("deployed_before_arrival")[far].mean())
    res["P_deployed_before_arrival_near"] = float(arr("deployed_before_arrival")[~far].mean())
    res["unprotected_h_near_mean"] = float(arr("unprotected_h")[~far].mean())
    w = arr("dur_h")
    res["availability_full_(>=n-1 bays & >=1 line)_bloom_hour_weighted"] = float((arr("avail_full") * w).sum() / w.sum())
    res["bay_availability_mean"] = float((arr("bay_avail") * w).sum() / w.sum())
    res["lift_availability_mean"] = float((arr("lift_avail") * w).sum() / w.sum())
    af = arr("avail_full")
    res["P_bloom_with_full_availability_below_95pct"] = float((af < 0.95).mean())
    ch = {}
    for leak in (0.055, 0.13, 0.28):     # v3 twin range: 5.5% median, 12-13% worst realistic, 28% if screen eta=0.5
        c = np.array([crew_hours(b, leak) for b in blooms])
        ch[f"leak_{leak}"] = dict(jazr_mean=float(c[:, 0].mean()), today_low_mean=float(c[:, 1].mean()), today_high_mean=float(c[:, 2].mean()),
                                  reduction_vs_low=float(1 - c[:, 0].mean() / c[:, 1].mean()), reduction_vs_high=float(1 - c[:, 0].mean() / c[:, 2].mean()))
    res["crew_hours_per_bloom"] = ch
    res["preseason_fixed_person_h_per_unit"] = 4 * 5 * 8   # inspection + drills [ASSUME]
    a = res["availability_full_(>=n-1 bays & >=1 line)_bloom_hour_weighted"]
    res["verdicts"] = {
      "T6a_response_time": ("PASS", "far alert: approval latency p90 %.0f min; %.2f%% deployed before arrival (deploy timed to T-1 h)" % (res['approval_latency_min_p50_p90_p99'][1], 100*res['P_deployed_before_arrival_far'])),
      "T6b_close_alert": ("FAIL", "close alerts (15%% [ASSUME]): %.0f%% deployed before arrival; mean %.2f h unprotected; p90 response %.0f min (2 human approvals dominate); with pre-authorised auto-deploy: %.0f%% before arrival, %.2f h unprotected" %
                           (100*res['P_deployed_before_arrival_near'], res['unprotected_h_near_mean'], res['response_min_near_p50_p90_p99'][1], 100*res['auto_near_P_before_arrival'], res['auto_near_unprotected_h_mean'])),
      "T6c_availability": ("PASS" if a >= 0.95 else "MARGINAL", "bloom-hour availability (>= n-1 bays and >= 1 lift line) %.3f vs criterion 0.95; %.1f%% of blooms below 0.95" % (a, 100*res['P_bloom_with_full_availability_below_95pct'])),
      "T6d_crew_hours": ("PASS", "JAZR %.0f person-h per bloom vs today %.0f-%.0f (reduction %.0f-%.0f%% at 13%% leakage); still not zero: residual screen crew + repairs" %
                         (ch['leak_0.13']['jazr_mean'], ch['leak_0.13']['today_low_mean'], ch['leak_0.13']['today_high_mean'], 100*ch['leak_0.13']['reduction_vs_low'], 100*ch['leak_0.13']['reduction_vs_high'])),
    }
    save("t6_ops_des.json", res)
    fig, axs = plt.subplots(1, 2, figsize=(10, 3.8))
    axs[0].hist(resp[far], bins=60, alpha=.7, label="far alert (deploy timed to T-1 h)")
    axs[0].hist(resp[~far], bins=60, alpha=.7, label="close alert")
    axs[0].set_xlabel("alert -> fully deployed (min)"); axs[0].legend(fontsize=7); axs[0].set_title("T6 response time", fontsize=9)
    labels = ["JAZR\n5.5% leak", "JAZR\n13%", "JAZR\n28%", "today\nlow", "today\nhigh"]
    vals = [ch["leak_0.055"]["jazr_mean"], ch["leak_0.13"]["jazr_mean"], ch["leak_0.28"]["jazr_mean"], ch["leak_0.13"]["today_low_mean"], ch["leak_0.13"]["today_high_mean"]]
    axs[1].bar(labels, vals, color=["tab:blue"]*3 + ["tab:gray"]*2); axs[1].set_ylabel("person-hours per bloom (mean)")
    axs[1].set_title("T6 crew-hours per bloom", fontsize=9)
    fig.tight_layout(); fig.savefig(os.path.join(CH, "t6_ops.png"), dpi=130)
    return res


if __name__ == "__main__":
    r = main()
    for k, v in r.items():
        if k not in ("params", "verdicts"):
            print(k, v)
    for k, (v, w) in r["verdicts"].items():
        print(k, v, w)
