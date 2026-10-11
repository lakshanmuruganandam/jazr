"""Operator procedures for the Bloom Incident OS, one entry per OS transition.
Clarity rules tested in tests/test_human_factors.py:
  each step = one imperative verb + one object; has a cue (what tells the operator to act),
  a check (how success is confirmed), a time budget, and an abort/fallback path.
"""
PROCEDURES = {
    ("IDLE", "ALERT"): dict(cue="Bloom early-warning notification received (auto)", action="Acknowledge alert",
                            check="OS shows ALERT; 72 h forecast panel loads", time_s=60, abort="Press STAND-DOWN to return to IDLE"),
    ("ALERT", "READY"): dict(cue="ALERT active", action="Run pre-deploy checklist",
                             check="All drums HEALTHY, wind < 20 m/s gust, comms OK, cameras OK", time_s=120,
                             abort="Leave in ALERT; call maintenance for any red item"),
    ("READY", "DEPLOYING"): dict(cue="Checklist green", action="Press DEPLOY",
                                 check="Bays lowering (max 6 at once); deploy timer < 10 min", time_s=600,
                                 abort="Press STAND-DOWN (bays return up, staged)"),
    ("DEPLOYING", "OPERATE"): dict(cue="All healthy bays DOWN (auto)", action="Confirm OPERATE",
                                   check="Screw RUN, outlet chosen, line dP < 500 Pa", time_s=60,
                                   abort="Press STAND-DOWN"),
    ("DEPLOYING", "STANDDOWN"): dict(cue="Deploy aborted or bloom cancelled", action="Press STAND-DOWN",
                                     check="Bays raising one at a time", time_s=60, abort="Press E-STOP (SAFE)"),
    ("OPERATE", "STANDDOWN"): dict(cue="Bloom over (counts below threshold for 6 h)", action="Press STAND-DOWN",
                                   check="Bays raising one at a time; pulse < 1 t each", time_s=2400, abort="Press E-STOP (SAFE)"),
    ("STANDDOWN", "IDLE"): dict(cue="All bays UP (auto)", action="Log bloom summary",
                                check="OS shows IDLE; drums stowed dry", time_s=300, abort="Call maintenance for any bay not UP"),
    ("ALERT", "IDLE"): dict(cue="Alert withdrawn", action="Press STAND-DOWN", check="OS shows IDLE", time_s=30, abort="None needed"),
    ("READY", "IDLE"): dict(cue="Alert withdrawn", action="Press STAND-DOWN", check="OS shows IDLE", time_s=30, abort="None needed"),
    ("ANY", "SAFE"): dict(cue="Seismic trip or E-STOP (auto)", action="Verify bays raising",
                          check="All bays UP within ~35 min; relief path open", time_s=2400,
                          abort="Notify shift supervisor; isolate drive power if a bay stalls"),
    ("SAFE", "IDLE"): dict(cue="Seismic trip cleared and all bays UP", action="Approve reset",
                           check="OS shows IDLE; walk-down inspection ordered", time_s=600, abort="Stay in SAFE"),
}
ALARM_RESPONSES = {
    "DRUM_STUCK": "Dispatch technician to bay; bay stays as is; check dP trend",
    "COMMS_LOSS_LOCAL_MODE": "Call I&C; bays run local rules (no lowering)",
    "CAMERA_FAULT_SCREW_STOPPED": "Call I&C; screw stays stopped; diverter to chute",
    "OUTLET_RECOVER_MODE": "Confirm recovery skip/compost route open",
    "SEISMIC_TRIP": "Follow SAFE procedure",
    "ESTOP": "Follow SAFE procedure",
    "WIND_HIGH_MOTION_BLOCKED": "Wait; no action unless a bay is mid-travel",
    "LINE_DP_HIGH": "Watch cleaning rate; prepare stand-down if rising for 30 min",
    "LINE_DP_HARD": "Confirm relief path open; inform plant control room",
    "SENSOR_DISAGREE": "Call I&C; voting continues on remaining channels",
}
