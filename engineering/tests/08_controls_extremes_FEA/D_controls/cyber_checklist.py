"""Cybersecurity review of the JAZR control architecture against IEC 62443-3-3 foundational
requirements and nuclear computer-security principles (IAEA NSS 17-T; US NRC RG 5.71 defensive
levels). Desk review of the v3 concept + our controller; PASS = satisfied by design and/or tested
here; RISK = not specified in v3 / needs implementation evidence. Writes out/cyber_checklist.md.
"""
import json, pathlib

HERE = pathlib.Path(__file__).resolve().parent
ITEMS = [
    ("Zones & conduits", "IEC 62443-3-2", "JAZR OT (PLC + per-bay LBCs) is its own zone, separate from plant I&C and from the IT/twin zone",
     "RISK", "v3 silent; Nawah must also decide whether JAZR is 'important to safety' (it is in the CW/UHS path) -> sets the security level"),
    ("No remote control of safety-relevant actions", "NSS 17-T / RG 5.71", "No internet/vendor remote path; every bay or OS command originates at the control-room HMI or in hard-wired local logic",
     "PASS", "controller has no network command input; D5 shows forecast/twin data cannot alter bay commands or OS state (159,798 checks)"),
    ("One-way data flow OT -> IT", "FR5 restricted data flow / RG 5.71 level 4->3", "Data diode exports load cells, counts and video to the twin; the forecast reaches OT only as an advisory outlet score",
     "PASS", "design rule; outlet choice is the only OT output the forecast can move, and stale/unsafe -> RECOVER (D4)"),
    ("Local protection independent of network", "FR7 resource availability", "Hard dP trip, seismic trip, TDMA + busy-loop staging and screw-stop are hard-wired / local",
     "PASS", "D3c model check under comms loss: 0 pulse-rule violations; D14 same-scan responses"),
    ("Identification & authentication", "FR1", "Named operator log-in; approvals bound to user; 2-person rule for SAFE reset",
     "RISK", "v3 says 'human approval at every step' but not who or how authenticated"),
    ("Use control", "FR2", "Role-based permissions (operator, shift supervisor, maintenance); maintenance mode locks out motion",
     "RISK", "not specified"),
    ("System integrity", "FR3", "Signed PLC/LBC logic, version control, change only through Nawah modification process; camera-AI model frozen & validated",
     "RISK", "not specified; AI model updates are a supply-chain vector"),
    ("Data confidentiality", "FR4", "Video of a nuclear marine security zone and protected species handled as restricted",
     "RISK", "CICPA/coast-guard sensitivities (site security zone)"),
    ("Timely response to events", "FR6", "OT event logging, time-synced, reviewed; alarm on config change",
     "RISK", "not specified"),
    ("Time source integrity", "FR3/FR7", "TDMA staging needs synchronised clocks; GNSS spoofing/drift could align two bays' slots",
     "RISK", "busy loop alone races (D3b); use local holdover oscillators, slot guard bands > 2x max skew, plausibility checks"),
    ("Wireless links", "FR5", "No radio for control; outlet valves 5 km offshore controlled via cable in the pipe bundle",
     "RISK", "v3 silent on offshore outlet-valve telemetry"),
    ("Common-mode across units", "defence in depth", "Separate PLC, LBCs and power per unit; no shared controller",
     "PASS", "v3: 'each unit has its own lane and controls'"),
    ("Physical security", "NSS 17-T", "Gantry cabinets locked, inside the maritime security zone; tamper switches",
     "RISK", "coordination with site security needed"),
]


def build():
    V = []
    lines = ["# Cybersecurity checklist (IEC 62443-3-3 / nuclear computer security)", "",
             "| # | Item | Reference | Requirement | Status | Evidence / gap |", "|---|---|---|---|---|---|"]
    for i, (item, ref, req, st, ev) in enumerate(ITEMS, 1):
        lines.append(f"| {i} | {item} | {ref} | {req} | **{st}** | {ev} |")
    n_pass = sum(1 for x in ITEMS if x[3] == "PASS")
    lines += ["", f"PASS {n_pass} / RISK {len(ITEMS) - n_pass}. RISK items are specification gaps for the detailed design, not demonstrated failures."]
    (HERE / "out").mkdir(exist_ok=True)
    open(HERE / "out" / "cyber_checklist.md", "w").write("\n".join(lines) + "\n")
    V.append(dict(test="D16 cybersecurity checklist (13 items)", value=f"PASS {n_pass}, RISK {len(ITEMS) - n_pass}",
                  criterion="no RISK on items that move bays", verdict="MARGINAL",
                  detail="architecture PASS (no remote control, one-way flow, local protection); identity, integrity, time-source and offshore telemetry are unspecified"))
    return V


if __name__ == "__main__":
    for v in build():
        print(v)
