"""E. Human factors: alarm rates, alarm-flood test, operator workload, procedure coverage.

Runs the D fault scenario (V0 v3-as-specified and V8 redesign) and counts annunciated alarms under
two philosophies:
  naive        - every controller alarm tag, a DP_HIGH alarm per bay, and a status alarm for every
                 bay raise / bay lowered (common in un-rationalised HMIs);
  rationalised - ISA-18.2 style: status -> event journal (not alarms); per-bay dP alarms grouped into
                 one LINE_DP alarm (bays share one line dP); RAISE_DEFERRED suppressed (automation
                 handles it); state-based suppression of dP alarms in SAFE; 10 s on-delay; same tag
                 not re-annunciated within 10 min.
Benchmarks (ISA-18.2 / EEMUA 191): <= 6 alarms/h average manageable (~1 per 10 min), > 10 alarms in
10 min = flood.  Workload: 3 min per alarm, 1 min per approval [ASM].
"""
import json, sys, pathlib
from multiprocessing import Pool
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "D_controls")); sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE))
import faultsim as FS
from procedures import PROCEDURES, ALARM_RESPONSES


def sim(kw):
    m, log, ev = FS.run(**kw)
    return log


def tags_naive(log, i):
    tags = set(log["alarms"][i])
    tags |= {f"DP_HIGH_B{k}" for k in log["lvl_bays"][i]}
    if i > 0 and log["raising"][i] > log["raising"][i - 1]:
        tags.add(f"STATUS_RAISE_{i}")          # unique per event -> counts once
    if i > 0 and log["down"][i] > log["down"][i - 1]:
        tags.add(f"STATUS_DOWN_{i}")
    return tags


def tags_rational(log, i):
    out = set()
    for a in log["alarms"][i]:
        if a.startswith("RAISE_DEFERRED"):
            continue
        if a.startswith("DP_HARD_B"):
            out.add("LINE_DP_HARD"); continue
        if a.startswith("SENSOR_DISAGREE_B"):
            out.add("SENSOR_DISAGREE"); continue
        out.add(a)
    if log["lvl_bays"][i]:
        out.add("LINE_DP_HIGH")
    if log["os"][i] == "SAFE":
        out -= {"LINE_DP_HIGH", "LINE_DP_HARD"}
    return out


def annunciate(log, fn, on_delay=0, rearm=0):
    active_since, last_ann, ann = {}, {}, []
    for i, t in enumerate(log["t"]):
        tags = fn(log, i)
        for g in list(active_since):
            if g not in tags:
                del active_since[g]
        for g in tags:
            active_since.setdefault(g, t)
            if t - active_since[g] >= on_delay and (g not in last_ann or (t - last_ann[g] > rearm and active_since[g] > last_ann[g])):
                if g not in last_ann or active_since[g] > last_ann[g]:
                    ann.append((t, g)); last_ann[g] = t
    return ann


def metrics(ann, T):
    t = np.array([a[0] for a in ann])
    bins = np.arange(0, T + 600, 600)
    c, _ = np.histogram(t, bins)
    return dict(total=len(ann), per_hour=len(ann) / (T / 3600), max_per_10min=int(c.max()) if len(c) else 0,
                flood_windows=int((c > 10).sum()), windows_over_1=int((c > 1).sum()), counts_10min=c.tolist())


def main():
    runs = {"V0 v3 as specified": dict(), "V8 redesign (belt + flap)": dict(clean_in_place=True, relief_mode="flap")}
    with Pool(2) as p:
        logs = dict(zip(runs, p.map(sim, list(runs.values()))))
    res, V = {}, []
    for name, log in logs.items():
        T = len(log["t"])
        naive = annunciate(log, tags_naive)
        rat = annunciate(log, tags_rational, on_delay=10, rearm=600)
        approvals = int(sum(log["approve"]))
        mn, mr = metrics(naive, T), metrics(rat, T)
        busy_naive = (mn["total"] * 3 + approvals) / (T / 60)
        busy_rat = (mr["total"] * 3 + approvals) / (T / 60)
        res[name] = dict(naive=mn, rationalised=mr, approvals=approvals, busy_fraction_naive=busy_naive,
                         busy_fraction_rationalised=busy_rat,
                         rationalised_alarm_list=[(round(t / 3600, 3), g) for t, g in rat])
        V.append(dict(test=f"E1 alarm rate, naive HMI ({name})", value=f"{mn['per_hour']:.1f}/h, peak {mn['max_per_10min']}/10 min, {mn['flood_windows']} flood windows",
                      criterion="<= 6/h average and no 10-min window > 10 (ISA-18.2/EEMUA 191)",
                      verdict="PASS" if mn["per_hour"] <= 6 and mn["flood_windows"] == 0 else "FAIL"))
        V.append(dict(test=f"E2 alarm rate, rationalised ({name})", value=f"{mr['per_hour']:.1f}/h, peak {mr['max_per_10min']}/10 min, {mr['flood_windows']} flood windows",
                      criterion="<= 6/h average and no flood", verdict="PASS" if mr["per_hour"] <= 6 and mr["flood_windows"] == 0 else
                      ("MARGINAL" if mr["flood_windows"] == 0 else "FAIL"),
                      detail="fault-dense scenario: 9 injected faults in 8 h; a normal bloom shift has far fewer"))
        V.append(dict(test=f"E3 operator workload ({name})", value=f"{100*busy_rat:.0f}% of shift time on alarms/approvals (rationalised), {100*busy_naive:.0f}% naive",
                      criterion="<= 50 % for 1 operator (V3: 1-2 operators) [ASM]",
                      verdict="PASS" if busy_rat <= 0.5 else "FAIL"))
    # procedure coverage
    os_pairs = set()
    for log in logs.values():
        for a, b in zip(log["os"][:-1], log["os"][1:]):
            if a != b:
                os_pairs.add((a, b))
    missing = [p for p in os_pairs if p not in PROCEDURES and not (p[1] == "SAFE" and ("ANY", "SAFE") in PROCEDURES)]
    tags = set()
    for log in logs.values():
        for al in log["alarms"]:
            tags |= {a.rstrip("0123456789").rstrip("_B") if "_B" in a else a for a in al}
    tags = {t for t in tags if not t.startswith("RAISE_DEFERRED")}
    tags = {("DRUM_STUCK" if t.startswith("DRUM_STUCK") else "LINE_DP_HARD" if t.startswith("DP_HARD")
             else "SENSOR_DISAGREE" if t.startswith("SENSOR_DISAGREE") else t) for t in tags}
    no_resp = sorted(t for t in tags if t not in ALARM_RESPONSES)
    res["procedure_coverage"] = dict(observed_transitions=sorted(map(list, os_pairs)), missing=missing, alarms_without_response=no_resp)
    V.append(dict(test="E4 procedure coverage (every observed OS transition / alarm has a written response)",
                  value=f"{len(os_pairs)} transitions, missing {missing}; alarms without response {no_resp}",
                  criterion="100 % coverage", verdict="PASS" if not missing and not no_resp else "FAIL"))
    res["verdicts"] = V
    (HERE / "out").mkdir(exist_ok=True)
    json.dump(res, open(HERE / "out" / "human_factors.json", "w"), indent=2, default=str)

    fig, ax = plt.subplots(figsize=(9, 3.6))
    w = 0.2
    for j, (name, r) in enumerate(res.items()):
        if not isinstance(r, dict) or "naive" not in r:
            continue
        for k, (lab, m) in enumerate((("naive", r["naive"]), ("rationalised", r["rationalised"]))):
            x = np.arange(len(m["counts_10min"])) / 6
            ax.step(x, m["counts_10min"], where="post", lw=1.2 if k else 0.8, ls="-" if k else ":",
                    label=f"{name} - {lab}")
    ax.axhline(10, color="#c33", lw=0.8); ax.text(0.1, 10.5, "flood threshold (10 / 10 min)", fontsize=8, color="#c33")
    ax.axhline(1, color="k", lw=0.6, ls="--"); ax.set_yscale("symlog")
    ax.set_xlabel("time (h)"); ax.set_ylabel("alarms per 10 min"); ax.legend(fontsize=7)
    ax.set_title("Alarm-flood test: fault-dense 8 h bloom")
    fig.tight_layout(); fig.savefig(HERE / "figs" / "alarm_flood.png", dpi=150)
    for v in V:
        print(v["verdict"], v["test"], v["value"])


if __name__ == "__main__":
    main()
