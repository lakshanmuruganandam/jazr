# E. Human factors: alarm rates, alarm flood, workload, procedures

**Method.** We re-run the D fault scenario: an 8-hour bloom with 9 injected faults, which is much denser than a normal shift. We run it twice: v3 as specified (V0) and the belt + flap redesign (V8).

Alarms are counted under two philosophies:

- **Naive**: every controller tag, one DP_HIGH per bay, and a status alarm for every bay raise or lowering.
- **Rationalised (ISA-18.2)**:
  - status messages go to the event journal, not the alarm list;
  - the per-bay dP alarms become one LINE_DP alarm, because the bays share one line dP (see D12);
  - RAISE_DEFERRED is suppressed;
  - dP alarms are suppressed in SAFE;
  - 10 s on-delay;
  - the same tag is not re-annunciated within 10 min.

**Benchmarks**: about 6 alarms/h or fewer (EEMUA 191 / ISA-18.2); more than 10 alarms in 10 min counts as a flood. Workload assumption: 3 min per alarm and 1 min per approval [ASM].

**Results** (`out/human_factors.json`, `figs/alarm_flood.png`):

| | Naive | Rationalised |
|---|---|---|
| V0 (v3 roll-up cleaning) | about 40/h (every one of ~160 raises in 8 h is an alarm), operator time ~200 %: **FAIL** | about 1/h, peak 1 per 10 min, workload ~4 %: **PASS** |
| V8 (belt cleaning) | about 3/h: **PASS** | about 1/h: **PASS** |

**Procedures** (`procedures.py`). There is one procedure per OS transition. Each has a cue, a single imperative action, a check, a time budget and an abort path, plus a written response for every alarm family.

Tests confirm full coverage:

- `tests/test_human_factors.py` checks every transition the model checker can reach.
- E4 checks every transition and alarm seen in simulation.

The longest step is SAFE all-up at about 35 min. Operators need to be told that this is expected.

**Design implications.**

- Do not alarm automation status (raise/lower). Group per-bay dP into one line alarm.
- Add sensor-disagreement and stuck-drum diagnostics as alarms. The stuck drum is otherwise latent (see D8).
- One operator is enough in the rationalised design. v3's "1-2 operators" holds.

Run: `python3 run_alarms.py` (~2 min).
