# D. Control-system tests: model checking, fault injection, timing, traceability, cyber

## Code

| File | What it is |
|---|---|
| `controller.py` | A **pure PLC-style step function** (one scan). It covers the Bloom Incident OS (IDLE, ALERT, READY, DEPLOYING, OPERATE, STANDDOWN, SAFE; approval needed for every forward step), the per-bay logic (UP, LOWERING, DOWN, RAISING, FAULT), the pulse rule (at most K = 1 bay raising), the comms-loss local rules (TDMA slots and a hard-wired busy loop), stuck-drum timeout, wind/seismic interlocks, screw stop and diverter, and outlet selection with hysteresis and RECOVER |
| `model_check.py` | Explicit-state BFS of the controller **(the same code)** combined with an adversarial drum plant (drums may stall) and an environment that toggles events |
| `plant.py` | Hydraulics, biomass and sensing model for simulation |
| `faultsim.py` | 8-hour, 15-bay bloom simulation with 9 injected faults |
| `run_controls.py` | Runs 10 design variants, a sweep of cleaning interval x density, and the filter trade-off |
| `verdicts.py`, `cyber_checklist.py` | Turn outputs into PASS/FAIL rows; write `out/cyber_checklist.md` |

**Model checking results** (`out/model_check.json`):

- MC1a (n = 1 bay, all events and inputs): 1,114 states.
- MC1b (n = 2): 26,633 states and 638,588 transitions. **0 invariant violations, 0 deadlocks**, and every state can reach a safe IDLE.
- Invariants checked:
  - I1 pulse rule;
  - I2 approval for every forward step;
  - I3 screw never runs with a turtle present or the camera failed;
  - I5 no lowering under wind, seismic, comms loss or outside DEPLOYING/OPERATE;
  - I6 seismic or E-stop leads to SAFE;
  - I8 bounded response to a hard dP;
  - I9 FAULT is latched and alarmed.
- **MC2, comms loss with n = 3 and slow drums.**
  - v3 as written (no local staging rule): 510k violating transitions. **FAIL.**
  - TDMA slots alone: **FAIL**. A slow drum overruns its slot.
  - Busy loop alone: **FAIL**. Two bays race in the same scan.
  - **TDMA + hard-wired busy loop: 0 violations. PASS.** This is the design fix.
- MC3: exhaustive wildlife and outlet table, 16,800 cases, 0 violations.
- MC4: forecast/twin inputs never change bay commands or OS state (159,798 checks). This is the IT/OT separation evidence.

## Simulation physics (labelled assumptions)

- Bays and the relief bay are **parallel paths between common pools, so they share one line dP**. Per-bay transmitters therefore cannot tell which bay is blinded.
- Mesh loss coefficient: Idelchik, with effective porosity.
- Bell residence on the face: 60 s [V3 sweep]. Sensitivity case: 300 s [audit].
- Sticking: 2 % at low dP, rising to 100 % at 240 Pa (audit's friction-vs-sweep numbers).
- Raising a bay dumps its face load into the plant (the pulse).
- Wave dP comes from a JONSWAP sea at 30° obliquity.
- Sensing: two dP transmitters and a load-cell estimate per bay, low-pass filtered, 2oo3 vote, plus a hard-wired 2oo2 channel.

## Key findings (`out/controls_results.json`; full table in `../SUMMARY.md`)

| Test | Result |
|---|---|
| D6 filter (τ 30 s, 2oo3, 20 s persistence) | 0 false trips up to Hs 2 m; latency 42 s. **PASS.** A naive single threshold gives 52-828 false trips per bay-day at Hs 1.5-2 m. **FAIL** |
| D7 stuck-high transmitter | Masked by 2oo3 voting. **PASS.** A single-channel hard trip loses the bay for the rest of the bloom. **FAIL** |
| D8 seized drum | Detected only when next commanded: 1,868 s (a latent fault). **MARGINAL** |
| D9 deploy time | Alert to OPERATE in 573 s with 0.1 m/s drums and 6 at once. **MARGINAL** against the 10-minute claim |
| D10 pulse < 1 t | Holds at 0.3/m³ (max 812 kg). Fails at 1/m³, with 300 s residence, or with 10 % sticking. **MARGINAL** |
| D11 leakage | Roll-up cleaning plus an open relief bay lets **18-29 % of biomass reach the plant** at 0.3/m³: raised bays pass about 2x their flow share, and the open relief bay takes about 5 %. **FAIL** against the twin's η = 0.9 |
| D15 redesign (endless-belt clean-in-place + passive flap relief) | 1.2 % leakage with no faults; 9.5 % in the full fault scenario; pulses up to 372 kg |
| D13 seismic staged all-up | 34 min. **MARGINAL**: hydraulically tolerable, but it conflicts with the pulse rule |

Run: `python3 model_check.py` (~5 min), `python3 run_controls.py` (~3-7 min, parallel), `python3 verdicts.py`, `python3 cyber_checklist.py`.
