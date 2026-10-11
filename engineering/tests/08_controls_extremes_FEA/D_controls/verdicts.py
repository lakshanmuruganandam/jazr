"""Turn D_controls outputs (model_check.json, controls_results.json) into PASS/FAIL/MARGINAL/INFO rows."""
import json, pathlib

HERE = pathlib.Path(__file__).resolve().parent


def build():
    mc = json.load(open(HERE / "out" / "model_check.json"))
    cr = json.load(open(HERE / "out" / "controls_results.json"))
    V = []
    for k, r in mc.items():
        if k.startswith("MC1"):
            V.append(dict(test=f"D1 model check {k.split(' (')[0]}: invariants I1-I9", value=f"{r['states']} states, {r['distinct_transitions']} transitions, violations {list(r['violations'])}",
                          criterion="0 violations", verdict="PASS" if not r["violations"] else "FAIL", detail=r["cfg"]))
            V.append(dict(test=f"D2 deadlock/liveness {k.split(' (')[0]}", value=f"deadlocks {r['deadlocks']}, states unable to reach safe IDLE {r['states_that_cannot_reach_safe_idle']}",
                          criterion="0 and 0", verdict="PASS" if r["deadlocks"] == 0 and r["states_that_cannot_reach_safe_idle"] == 0 else "FAIL"))
    m2 = mc["MC2"]
    v3 = m2["none (each LBC free)"]
    V.append(dict(test="D3a pulse rule (<=1 bay raising) under comms loss - v3 as written (no local staging rule)",
                  value=f"{v3['pulse_violations']} violating transitions", criterion="0", verdict="FAIL" if v3["pulse_violations"] else "PASS",
                  detail="v3 specifies staging but not how it survives loss of the central PLC"))
    for nm in ("TDMA only", "busy-line only"):
        V.append(dict(test=f"D3b pulse rule under comms loss - {nm}", value=f"{m2[nm]['pulse_violations']} violating transitions",
                      criterion="0", verdict="FAIL" if m2[nm]["pulse_violations"] else "PASS",
                      detail=(m2[nm]["counterexample"] or "")[:300]))
    fx = m2["TDMA + busy-line"]
    V.append(dict(test="D3c pulse rule under comms loss - TDMA slots + hard-wired busy loop (proposed)",
                  value=f"{fx['states']} states, {fx['pulse_violations']} violations", criterion="0",
                  verdict="PASS" if fx["pulse_violations"] == 0 else "FAIL"))
    m3 = mc["MC3"]
    V.append(dict(test="D4 wildlife (screw stop / diverter) + outlet selection exhaustive table", value=f"{m3['cases']} cases, {m3['violations']} violations",
                  criterion="0 (screw never runs with turtle/camera fault; outlet always safe or RECOVER; no flapping)",
                  verdict="PASS" if m3["violations"] == 0 else "FAIL"))
    m4 = mc.get("MC4 IT/OT separation", {})
    V.append(dict(test="D5 IT/OT separation: forecast/twin inputs cannot change bay commands or OS", value=f"{m4.get('checked')} checks, {m4.get('differing')} differences",
                  criterion="0 differences", verdict="PASS" if m4.get("differing") == 0 else "FAIL"))
    ft = cr["filter"]
    des = [r for r in ft if r["tau"] == 30]
    raw = [r for r in ft if r["tau"] == "raw"]
    worst_false = max(r["false_trips_per_bay_day"] for r in des)
    lat = max(r["latency_s"] for r in des)
    V.append(dict(test="D6 dP filter (tau 30 s, 2oo3, 20 s persistence) vs wave spikes Hs 0.5-2.0 m", value=f"false trips {worst_false}/bay-day; latency {lat:.0f} s",
                  criterion="0 false trips/day and latency <= 60 s [ASM: audit 'blinds in <2 min at 1/m3']",
                  verdict="PASS" if worst_false == 0 and lat <= 60 else "FAIL"))
    V.append(dict(test="D6b naive single-transmitter threshold vs waves", value=", ".join(f"Hs {r['Hs']}: {r['false_trips_per_bay_day']:.0f}/bay-day" for r in raw),
                  criterion="0 false trips/day", verdict="FAIL" if max(r["false_trips_per_bay_day"] for r in raw) > 0 else "PASS",
                  detail="what an unfiltered 'roll up on high dP' does when dP sits at 60 % of trip"))
    var = cr["variants"]
    b = var[[k for k in var if k.startswith("V0")][0]]
    v3h = var[[k for k in var if k.startswith("V3")][0]]
    V.append(dict(test="D7 stuck-high transmitter (F1) with 2oo3 + 2oo2 hard channel", value=f"false dP raises {b['false_dp_raises']}",
                  criterion="0", verdict="PASS" if b["false_dp_raises"] == 0 else "FAIL"))
    V.append(dict(test="D7b same fault with single-transmitter hard-wired trip (1oo1)", value=f"false dP raises {v3h['false_dp_raises']} (bay lost for the rest of the bloom)",
                  criterion="0", verdict="FAIL" if v3h["false_dp_raises"] else "PASS"))
    tm = cr["timing"]
    V.append(dict(test="D8 stuck-drum detection latency (F3 seized drive)", value=f"{tm['stuck_drum_alarm_latency_s']} s",
                  criterion="<= 300 s [ASM]", verdict="PASS" if (tm["stuck_drum_alarm_latency_s"] or 1e9) <= 300 else "MARGINAL",
                  detail="latent until the bay is next commanded; add hourly inch-test / motor-current & brake-torque monitoring"))
    V.append(dict(test="D9 deploy time alert -> OPERATE (2 approvals, 6 drums at once, 0.1 m/s)", value=f"{tm['deploy_s_from_alert']} s",
                  criterion="<= 600 s [V3 'about 10 min']", verdict="PASS" if tm["deploy_s_from_alert"] <= 540 else ("MARGINAL" if tm["deploy_s_from_alert"] <= 600 else "FAIL"),
                  detail=f"0.2 m/s drums: {var[[k for k in var if k.startswith('V6')][0]]['deploy_time_s'] + 120} s"))
    sw = [r for r in cr["sweep"] if not r["clean_in_place"]]
    p03 = max(r["max_event_kg"] for r in sw if r["density"] == 0.3)
    p10 = min(r["max_event_kg"] for r in sw if r["density"] == 1.0)
    v5 = var[[k for k in var if k.startswith("V5")][0]]["max_event_kg"]
    v7 = var[[k for k in var if k.startswith("V7")][0]]["max_event_kg"]
    V.append(dict(test="D10 roll-up pulse < 1 t (v3 claim)", value=f"0.3/m3: max {p03:.0f} kg; 1/m3: >= {p10:.0f} kg; audit residence 300 s: {v5:.0f} kg; sticking 10 %: {v7:.0f} kg",
                  criterion="every pulse < 1000 kg", verdict="MARGINAL" if p03 < 1000 else "FAIL",
                  detail="holds only at <=0.3/m3 with 60 s residence and <=2 % sticking; fails at 1/m3 ('high-flux mode')"))
    l03 = [r["leakage_to_plant_fraction"] for r in sw if r["density"] == 0.3]
    cip = [r["leakage_to_plant_fraction"] for r in cr["sweep"] if r["clean_in_place"] and r["density"] == 0.3]
    V.append(dict(test="D11 biomass reaching plant with roll-up cleaning + open relief bay (no faults, 0.3/m3)",
                  value=f"{100*min(l03):.0f}-{100*max(l03):.0f} % (belt clean-in-place + flap relief: {100*max(cip):.1f} %)",
                  criterion="<= 10 % (v3 twin assumes inner-screen efficiency 0.9)", verdict="FAIL" if min(l03) > 0.10 else "PASS",
                  detail="raised bays pass ~2x their share of flow (no mesh) and the open relief bay takes ~5 % of flow even when clean"))
    V.append(dict(test="D12 per-bay dP trigger selectivity", value=f"bays are parallel paths: all transmitters read one line dP (max line dP in V0 {b['max_line_dp']:.0f} Pa)",
                  criterion="trigger must identify the blinded bay", verdict="MARGINAL",
                  detail="v3 'on high dP that one bay rolls up' is not bay-selective; use line dP + round-robin/oldest-cleaned + per-bay flow or camera"))
    V.append(dict(test="D13 seismic/E-stop fail-open time (all bays up, staged 1 at a time)", value=f"{tm['seismic_all_up_s']} s",
                  criterion="<= 600 s [ASM]", verdict="MARGINAL",
                  detail="pulse rule and fast fail-open conflict; hydraulically tolerable because relief path caps line dP (~1 kPa) below the 3 kPa structural accident case"))
    V.append(dict(test="D14 immediate responses: comms-loss alarm, camera fault screw stop, RECOVER on stale forecast", value=f"{tm['comms_loss_alarm_latency_s']} / {tm['camera_fault_alarm_latency_s']} / {tm['recover_mode_latency_s']} s",
                  criterion="same scan (<= 1 s)", verdict="PASS" if max(tm['comms_loss_alarm_latency_s'], tm['camera_fault_alarm_latency_s'], tm['recover_mode_latency_s']) <= 1 else "FAIL",
                  detail=f"outlet after A unsafe + stale: {tm['outlet_after_A_unsafe']}; after forecast fresh: {tm['outlet_after_forecast_fresh_and_A_unsafe']}"))
    v8 = var[[k for k in var if k.startswith("V8")][0]]
    v9 = var[[k for k in var if k.startswith("V9")][0]]
    V.append(dict(test="D15 redesign check: belt clean-in-place + flap relief, full fault scenario", value=f"0.3/m3: leakage {100*v8['leakage_to_plant_fraction']:.1f} %, max pulse {v8['max_event_kg']:.0f} kg; 1/m3: leakage {100*v9['leakage_to_plant_fraction']:.1f} %, max pulse {v9['max_event_kg']:.0f} kg",
                  criterion="leakage <= 10 %, pulses < 1 t", verdict="PASS" if v8["leakage_to_plant_fraction"] <= 0.1 and v8["max_event_kg"] < 1000 else "MARGINAL",
                  detail="remaining 1/m3 pulses come from the seismic raise-all with loaded faces -> clean-then-raise sequence"))
    return V


if __name__ == "__main__":
    for v in build():
        print(v["verdict"], v["test"], v["value"])
