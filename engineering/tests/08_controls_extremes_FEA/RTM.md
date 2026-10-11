# Requirement traceability matrix (auto-generated)

Status = worst verdict among linked tests of the design as specified in v3 (FAIL > MARGINAL > PASS; INFO ignored).
Rows D3b, D6b, D7b, E1 test rejected alternatives (naive filter, 1oo1 trip, partial comms-loss rules, un-rationalised HMI) and are excluded.
| ID | Requirement | Source | Tests | Status |
|---|---|---|---|---|
| R1 | Whole line deploys in ~10 min from the control room, no crane/divers/boats | v3 §2 Deployment | D9 (1 rows) | **MARGINAL** |
| R2 | Human approval at every Incident-OS step | v3 §2 Control | D1, E4 (3 rows) | **PASS** |
| R3 | Each roll-up pulse < 1 t | v3 §2 Fail-safe; audit #8 | D3, D10, D15 (6 rows) | **FAIL** |
| R4 | Per-bay roll-up on high dP, filtered against tide/wave transients | v3 §2 Fail-safe; precedent 9; audit #3 | D6, D7, D12 (5 rows) | **MARGINAL** |
| R5 | Never block a lane fully (always-open relief) | v3 §2 Nuclear framing; audit #3 | D11, D13, A1 (7 rows) | **FAIL** |
| R6 | No common-mode failure across units | v3 §2 Fail-safe | D16 (1 rows) | **MARGINAL** |
| R7 | Camera-triggered diverter and screw auto-stop on turtles | v3 §2 Lift; audit #12 | D4, D14 (2 rows) | **PASS** |
| R8 | Outlet chosen from 72 h forecast; RECOVER when none safe | v3 §2 Outlets; audit #14 | D4, D14 (2 rows) | **PASS** |
| R9 | Stuck drum detected, alarmed, others continue | audit FMEA (ours) | D1, D8 (3 rows) | **MARGINAL** |
| R10 | Safe operation on loss of central comms | ours (IEC 62443 FR7) | D3, D14 (5 rows) | **FAIL** |
| R11 | Seismic II/I structure; fail-open on seismic trip | v3 §2 Nuclear framing; audit #3 | B1, B2, D13 (5 rows) | **MARGINAL** |
| R12 | No remote control of safety-relevant actions; IT/OT separation | nuclear cyber principles | D5, D16 (2 rows) | **MARGINAL** |
| R13 | Gantry survives stowed 100-yr storm; operates within stated envelope | audit #16, #23 | A1, A2, A3, A5, A6, A7, C1, C2, C3, C4, C5, C11 (23 rows) | **FAIL** |
| R14 | Screen mesh survives dP and roll-up for 60 y | v3 §2 Screen type | A8 (10 rows) | **FAIL** |
| R15 | Materials fit 36-38 C seawater, 41-50 C air, dust | brief / audit #16 | C7, C8, C9, C10, G3 (5 rows) | **FAIL** |
| R16 | Approach velocity <= 0.10-0.12 m/s at all tides | v3 precedent 1 (NMFS) | C6 (2 rows) | **FAIL** |
| R17 | 1-2 operators; alarms manageable | v3 §3 | E1, E2, E3 (6 rows) | **PASS** |
| R18 | Lower life-cycle CO2 than boats/crews; net benefit | v3 sustainability | F1, F2, F3 (3 rows) | **PASS** |
| R19 | Capacity headroom for future blooms/warmer seas | v3 capacity; brief criterion 7 | G1, G2, G4 (3 rows) | **MARGINAL** |
