"""D. Control-system test campaign: fault injection, design variants, filter test, timing tests.
Runs simulations in parallel (multiprocessing). Writes out/controls_results.json, out/baseline_log.json.gz, figs/.
"""
import json, gzip, sys, pathlib, time
from multiprocessing import Pool
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent))
import faultsim as FS
from plant import Sensing, WaveDP
from common import params as P

VARIANTS = {
    "V0 v3 as specified (open relief bay, 2oo3+filter, hard 2oo2, TDMA+busy)": dict(),
    "V1 passive flap relief (closed below 600 Pa)": dict(relief_mode="flap"),
    "V2 naive sensing: 1 transmitter, no filter/persistence": dict(raw_mode=True),
    "V3 hard-wired trip on single transmitter (1oo1)": dict(hard_vote="1oo1"),
    "V4 comms-loss rule without busy line (TDMA only)": dict(busy_line=False),
    "V5 audit residence tau=300 s": dict(tau=300.0),
    "V6 drum speed 0.2 m/s": dict(speed=0.2),
    "V7 sticking s0=10 %": dict(s0=0.10),
    "V8 redesign: endless-belt clean-in-place + flap relief": dict(clean_in_place=True, relief_mode="flap"),
    "V9 redesign V8 at 1.0 ind/m3 whole bloom": dict(clean_in_place=True, relief_mode="flap", density=1.0),
}
SWEEP = [dict(density=d, clean_age=a, faults=False, surge=False, hours=4.0, record=False, clean_in_place=cip,
              relief_mode="flap" if cip else "open")
         for cip in (False, True) for d in (0.1, 0.3, 1.0) for a in (600, 1200, 2400, 4800)]


def _run(kw):
    kw = dict(kw)
    m, log, ev = FS.run(**kw)
    return m, (log if kw.get("record", True) and kw.get("keep_log") else None), ev


def run_variant(item):
    name, kw = item
    rec = name.startswith("V0")
    m, log, ev = FS.run(record=True, **kw)
    if rec:
        return name, m, log, ev
    return name, m, None, None


def run_sweep(kw):
    m, _, _ = FS.run(**kw)
    return kw, m


def filter_test():
    """False trips (no real blinding, true dP 300 Pa = 60 % of trip) and detection latency
    (true dP ramps 300 -> 1500 Pa in 120 s: audit 'blinds in < 2 min at 1/m3')."""
    res = []
    n = 15
    for Hs, Tp in ((0.5, 4.0), (1.0, 4.5), (1.5, 5.0), (2.0, 5.5)):
        wv = WaveDP(n, Hs, Tp, seed=7)
        wave = np.array([wv.dp(t) for t in range(7200)])
        for tau, pers in ((0, 0), (5, 5), (15, 10), (30, 20), (60, 30), (120, 30)):
            for raw in (False,):
                sn = Sensing(n, tau=float(tau), pers=pers, seed=11)
                trips = 0
                prev = np.zeros(n, bool)
                for t in range(7200):
                    lvl, _ = sn.read(300.0 + wave[t])
                    on = lvl >= 1
                    trips += int((on & ~prev).sum())
                    prev = on
                sn = Sensing(n, tau=float(tau), pers=pers, seed=12)
                lat = []
                det = np.full(n, -1)
                for t in range(900):
                    true = 300.0 + np.clip((t - 300) / 120, 0, 1) * 1200 if t >= 300 else 300.0
                    lvl, _ = sn.read(true + wave[t])
                    det = np.where((det < 0) & (lvl >= 1) & (t >= 300), t, det)
                t_cross = 300 + (500 - 300) / 1200 * 120
                lat = det[det > 0] - t_cross
                res.append(dict(Hs=Hs, tau=tau, pers=pers, false_trips_per_bay_day=trips / n * 12,
                                latency_s=float(np.median(lat)) if len(lat) else None))
        # naive single transmitter
        sn = Sensing(n, raw_mode=True, seed=11)
        trips = 0; prev = np.zeros(n, bool)
        for t in range(7200):
            lvl, _ = sn.read(300.0 + wave[t]); on = lvl >= 1
            trips += int((on & ~prev).sum()); prev = on
        res.append(dict(Hs=Hs, tau="raw", pers=0, false_trips_per_bay_day=trips / n * 12, latency_s=0.0))
    return res


def main():
    t0 = time.time()
    with Pool(9) as pool:
        var = pool.map(run_variant, list(VARIANTS.items()))
        sweep = pool.map(run_sweep, SWEEP)
    ft = filter_test()
    out = {"variants": {}, "sweep": [], "filter": ft}
    base_log = None
    for name, m, log, ev in var:
        out["variants"][name] = m
        if log is not None:
            base_log, base_ev = log, ev
    for kw, m in sweep:
        out["sweep"].append(dict(density=kw["density"], clean_age=kw["clean_age"], clean_in_place=kw["clean_in_place"], **{k: m[k] for k in
                                 ("max_event_kg", "events_over_1t", "mean_event_kg", "leakage_to_plant_fraction", "raises", "max_line_dp")}))
    # timing / fault-response from the baseline log
    H = 3600
    tm = {}
    tm["deploy_s_from_final_approval"] = out["variants"][list(VARIANTS)[0]]["deploy_time_s"]
    tm["deploy_s_from_alert"] = tm["deploy_s_from_final_approval"] + 120 if tm["deploy_s_from_final_approval"] else None
    tm["stuck_drum_alarm_latency_s"] = FS.first_alarm_time(base_log, "DRUM_STUCK_B7", int(2.0 * H))
    tm["comms_loss_alarm_latency_s"] = FS.first_alarm_time(base_log, "COMMS_LOSS_LOCAL_MODE", int(3.0 * H))
    tm["camera_fault_alarm_latency_s"] = FS.first_alarm_time(base_log, "CAMERA_FAULT_SCREW_STOPPED", int(5.6 * H))
    tm["recover_mode_latency_s"] = FS.first_alarm_time(base_log, "OUTLET_RECOVER_MODE", int(6.0 * H))
    tm["seismic_all_up_s"] = out["variants"][list(VARIANTS)[0]]["seismic_all_up_s"]
    i_t = int(6.2 * H) + 5
    tm["outlet_after_A_unsafe"] = base_log["outlet"][i_t] if i_t < len(base_log["outlet"]) else None
    i_t = int(6.5 * H) + 5
    tm["outlet_after_forecast_fresh_and_A_unsafe"] = base_log["outlet"][i_t]
    out["timing"] = tm
    out["runtime_s"] = round(time.time() - t0, 1)
    (HERE / "out").mkdir(exist_ok=True)
    json.dump(out, open(HERE / "out" / "controls_results.json", "w"), indent=2, default=str)
    with gzip.open(HERE / "out" / "baseline_log.json.gz", "wt") as f:
        json.dump(base_log, f)
    json.dump(base_ev, open(HERE / "out" / "baseline_raise_events.json", "w"))

    # ---------------- figures ----------------
    t = np.array(base_log["t"]) / H
    fig, ax = plt.subplots(4, 1, figsize=(10, 8), sharex=True)
    ax[0].plot(t, base_log["dp"], lw=0.6); ax[0].set_ylabel("line dP (Pa)")
    ax[0].set_title("V0 baseline bloom with fault injection (1 unit, 15 bays)")
    ax[1].plot(t, base_log["down"], lw=0.8, label="bays fully down"); ax[1].plot(t, base_log["raising"], lw=0.8, label="bays raising")
    ax[1].legend(fontsize=7, loc="upper right"); ax[1].set_ylabel("bays")
    evt = np.array([e[0] for e in base_ev]) / H; evk = np.array([e[2] for e in base_ev])
    ax[2].scatter(evt, evk, s=6, c=np.where(evk > 1000, "#c33", "#36c")); ax[2].axhline(1000, color="k", lw=0.8)
    ax[2].set_ylabel("pulse per raise (kg)")
    na = [len(a) for a in base_log["alarms"]]
    ax[3].plot(t, na, lw=0.6); ax[3].set_ylabel("active alarms"); ax[3].set_xlabel("time (h)")
    for a_, (t1, lab) in zip([ax[0]] * 9, [(1.0, "F1"), (1.5, "F2"), (2.0, "F3"), (2.5, "surge"), (3.0, "F4"), (4.0, "F5"), (5.5, "F6"), (6.0, "F7"), (7.0, "F9")]):
        for a2 in ax:
            a2.axvline(t1, color="#aaa", lw=0.5)
        ax[0].text(t1, ax[0].get_ylim()[1] * 0.9, lab, fontsize=7)
    fig.tight_layout(); fig.savefig(HERE / "figs" / "faultsim_timeline.png", dpi=140); plt.close(fig)

    fig, ax = plt.subplots(1, 2, figsize=(10, 3.8))
    for cip, ls in ((False, "o-"), (True, "s--")):
        for d, c in ((0.1, "#5b8fc9"), (0.3, "#e39a4f"), (1.0, "#c33")):
            rows = [r for r in out["sweep"] if r["density"] == d and r["clean_in_place"] == cip]
            lab = f"{d}/m3 " + ("belt+flap" if cip else "roll-up (v3)")
            if not cip:
                ax[0].plot([r["clean_age"] / 60 for r in rows], [r["max_event_kg"] for r in rows], ls, color=c, label=lab)
            ax[1].plot([r["clean_age"] / 60 for r in rows], [100 * r["leakage_to_plant_fraction"] for r in rows], ls, color=c, label=lab)
    ax[0].axhline(1000, color="k", lw=0.8); ax[0].set_xlabel("max cleaning interval per bay (min)"); ax[0].set_ylabel("largest pulse (kg)")
    ax[0].set_yscale("log"); ax[0].legend(fontsize=8); ax[0].set_title("Pulse vs cleaning interval")
    ax[1].set_xlabel("max cleaning interval per bay (min)"); ax[1].set_ylabel("biomass reaching plant (%)")
    ax[1].set_title("Biomass reaching the plant"); ax[1].legend(fontsize=6)
    fig.tight_layout(); fig.savefig(HERE / "figs" / "pulse_leakage_tradeoff.png", dpi=140); plt.close(fig)

    fig, ax = plt.subplots(1, 2, figsize=(10, 3.8))
    for Hs in (0.5, 1.0, 1.5, 2.0):
        rows = [r for r in ft if r["Hs"] == Hs and r["tau"] != "raw"]
        ax[0].plot([r["tau"] for r in rows], [max(r["false_trips_per_bay_day"], 0.01) for r in rows], "o-", label=f"Hs {Hs} m")
    raw = [r for r in ft if r["tau"] == "raw"]
    ax[0].scatter([0] * len(raw), [max(r["false_trips_per_bay_day"], 0.01) for r in raw], marker="x", c="k", label="raw single sensor")
    ax[0].set_yscale("log"); ax[0].set_xlabel("low-pass tau (s)"); ax[0].set_ylabel("false trips per bay-day")
    ax[0].legend(fontsize=7); ax[0].set_title("Wave-spike rejection (true dP = 60 % of trip)")
    rows = [r for r in ft if r["Hs"] == 1.0 and r["tau"] != "raw"]
    ax[1].plot([r["tau"] for r in rows], [r["latency_s"] for r in rows], "o-")
    ax[1].axhline(60, color="#c33", lw=0.8); ax[1].text(2, 62, "60 s target [ASM]", fontsize=8)
    ax[1].set_xlabel("low-pass tau (s)"); ax[1].set_ylabel("detection latency (s)"); ax[1].set_title("Blinding ramp 300->1500 Pa in 120 s (Hs 1 m)")
    fig.tight_layout(); fig.savefig(HERE / "figs" / "filter_tradeoff.png", dpi=140); plt.close(fig)
    print(json.dumps({k: v for k, v in out.items() if k != "filter"}, indent=1, default=str)[:6000])
    print("filter rows:", json.dumps(ft)[:2500])


if __name__ == "__main__":
    main()
