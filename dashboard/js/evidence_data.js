window.JZ_EVIDENCE = {
 "scoreboard": {
  "source": "TESTS/00_TEST_REPORT.md",
  "rows": [
   {
    "id": "00",
    "stream": "Real data: currents, waves, SST, wind, jellyfish, turtles",
    "checks": "10 assumptions",
    "pass": "6 OK",
    "marginal": "—",
    "fail": "4 CHANGE",
    "info": "—",
    "pytest": "—"
   },
   {
    "id": "01",
    "stream": "Twin verification & validation",
    "checks": "10 test families",
    "pass": "analytic within 0.7%; converged; 23/23 rows reproduced",
    "marginal": "—",
    "fail": "dt ≥ 300 s skips the capture zone",
    "info": "no field validation",
    "pytest": "pytest 54/54"
   },
   {
    "id": "02",
    "stream": "Hydraulics & structures",
    "checks": "300",
    "pass": "180",
    "marginal": "43",
    "fail": "77 (many deliberate stress cases)",
    "info": "—",
    "pytest": "`run_all.py` (~50 s)"
   },
   {
    "id": "03",
    "stream": "CFD of the angled screen and outer line",
    "checks": "5 tests",
    "pass": "screen sweep at 11° ✔, mass ~1e-13",
    "marginal": "through-velocity uneven",
    "fail": "outer line 0–14%",
    "info": "2D only",
    "pytest": "—"
   },
   {
    "id": "04",
    "stream": "Biology, wildlife, FMEA, operations",
    "checks": "41",
    "pass": "12",
    "marginal": "11",
    "fail": "8",
    "info": "9",
    "pytest": "pytest 16/16"
   },
   {
    "id": "05",
    "stream": "Economics, risk, regulatory, rubric, compliance",
    "checks": "19 tests + 14 permit items",
    "pass": "19 tests pass; 2 permits PASS",
    "marginal": "—",
    "fail": "—",
    "info": "11 permit RISK",
    "pytest": "pytest 19/19"
   },
   {
    "id": "06",
    "stream": "Physical test protocols (pre-registered)",
    "checks": "16 tank + 8 flume + 5 pilot",
    "pass": "—",
    "marginal": "—",
    "fail": "—",
    "info": "to run",
    "pytest": "data sheets ready"
   },
   {
    "id": "07",
    "stream": "Virtual tank (SIMULATED T01–T16)",
    "checks": "16 protocols × ≥3 runs",
    "pass": "7",
    "marginal": "—",
    "fail": "5 (+1 kill: turtle, camera only)",
    "info": "3 report-only",
    "pytest": "—"
   },
   {
    "id": "08",
    "stream": "FEA, seismic, extremes, controls, human factors, LCA, climate",
    "checks": "81",
    "pass": "48",
    "marginal": "12",
    "fail": "15 (4 are rejected alternatives)",
    "info": "6",
    "pytest": "pytest 23/23"
   }
  ],
  "totals": {
   "checks_approx": 600,
   "pytest_pass": 112
  }
 },
 "twin_results": {
  "source": "JAZR_v4.md §3 'Results, honestly'",
  "rows": [
   {
    "scenario": "Real-current hindcast, 292 alert windows (v3 config incl. outer line)",
    "today": 0.71,
    "release_only": 0.062,
    "v41": 0.062,
    "raw": [
     "71%",
     "6.2%",
     "≤6.2%"
    ]
   },
   {
    "scenario": "3-day bloom, inner screen η_r = 0.9, no outer line",
    "today": 0.97,
    "release_only": 0.179,
    "v41": 0.101,
    "raw": [
     "97%",
     "17.9%",
     "10.1%"
    ]
   },
   {
    "scenario": "10-day bloom, same",
    "today": 1.0,
    "release_only": 0.499,
    "v41": 0.104,
    "raw": [
     "100%",
     "49.9%",
     "10.4%"
    ]
   },
   {
    "scenario": "10-day bloom, η_r = 0.7",
    "today": 1.0,
    "release_only": null,
    "v41": 0.3,
    "raw": [
     "100%",
     "—",
     "30.0%"
    ]
   },
   {
    "scenario": "10-day bloom, η_r = 0.5",
    "today": 1.0,
    "release_only": null,
    "v41": 0.507,
    "raw": [
     "100%",
     "—",
     "50.7%"
    ]
   },
   {
    "scenario": "Stress drift 5.5 cm/s, 10-day bloom (with outer line 0.4)",
    "today": 1.0,
    "release_only": 0.51,
    "v41": 0.06,
    "raw": [
     "100%",
     "51.0%",
     "6.0%"
    ]
   }
  ],
  "note": "Fractions of swarm reaching intake; v41 for hindcast row is an upper bound (≤6.2%).",
  "v5_note": "No v5 twin result with eta_r 0.95-0.99 found. twin/out/v5_far.json and v5_noharm.json (scripts twin/v5far.py, twin/v5nh.py) use eta_r=0.9 fixed; no JAZR_v5*.md exists. v5_rows not provided."
 },
 "hindcast": {
  "source": "TESTS/01_twin_VV/out/t9_hindcast.json",
  "n_windows": 292,
  "period": [
   "2022-01-01T00",
   "2025-12-31T23"
  ],
  "n_missing_hours_interpolated": 96,
  "mean_u_along_m_s": -0.00382,
  "mean_v_offshore_m_s": -0.02915,
  "cases": {
   "current only": {
    "Today": {
     "mean": 0.713233,
     "P10": 0.3974,
     "P50": 0.7175,
     "P90": 0.9939,
     "mean_OctNov": 0.737083
    },
    "v2 Gate": {
     "mean": 0.134,
     "P10": 0.0391,
     "P50": 0.1225,
     "P90": 0.258,
     "mean_OctNov": 0.140063
    },
    "v3": {
     "mean": 0.062151,
     "P10": 0.0221,
     "P50": 0.0555,
     "P90": 0.111,
     "mean_OctNov": 0.067292
    }
   },
   "current+wind2%": {
    "Today": {
     "mean": 0.579842,
     "P10": 0.019,
     "P50": 0.626,
     "P90": 0.9978,
     "mean_OctNov": 0.523958
    },
    "v2 Gate": {
     "mean": 0.112856,
     "P10": 0.002,
     "P50": 0.0835,
     "P90": 0.2568,
     "mean_OctNov": 0.105771
    },
    "v3": {
     "mean": 0.060445,
     "P10": 0.001,
     "P50": 0.042,
     "P90": 0.1308,
     "mean_OctNov": 0.058146
    }
   }
  },
  "frac_order": {
   "current only": {
    "frac_windows_Today>v2>v3": 0.989726,
    "frac_windows_Today>v2>=v3": 1.0,
    "frac_windows_v3<Today": 1.0,
    "ordering_of_means_holds": true
   },
   "current+wind2%": {
    "frac_windows_Today>v2>v3": 0.907534,
    "frac_windows_Today>v2>=v3": 0.972603,
    "frac_windows_v3<Today": 0.972603,
    "ordering_of_means_holds": true
   }
  }
 },
 "far_release": {
  "source": "twin/out/v5_far.json (script twin/v5far.py: eta_r=0.9, vr=-0.025, 240 h)",
  "rows": [
   {
    "label": "outlet x=1200 y=5000 ur=0.0",
    "x_km": 1.2,
    "y_km": 5.0,
    "ur_cm_s": 0.0,
    "mean": 0.499417,
    "lo": 0.485333,
    "hi": 0.518
   },
   {
    "label": "outlet x=1200 y=5000 ur=0.01",
    "x_km": 1.2,
    "y_km": 5.0,
    "ur_cm_s": 1.0,
    "mean": 0.408167,
    "lo": 0.352,
    "hi": 0.444667
   },
   {
    "label": "outlet x=1200 y=10000 ur=0.0",
    "x_km": 1.2,
    "y_km": 10.0,
    "ur_cm_s": 0.0,
    "mean": 0.280583,
    "lo": 0.265333,
    "hi": 0.295333
   },
   {
    "label": "outlet x=1200 y=10000 ur=0.01",
    "x_km": 1.2,
    "y_km": 10.0,
    "ur_cm_s": 1.0,
    "mean": 0.192417,
    "lo": 0.173333,
    "hi": 0.214
   },
   {
    "label": "outlet x=5000 y=3000 ur=0.0",
    "x_km": 5.0,
    "y_km": 3.0,
    "ur_cm_s": 0.0,
    "mean": 0.270833,
    "lo": 0.259333,
    "hi": 0.296
   },
   {
    "label": "outlet x=5000 y=3000 ur=0.01",
    "x_km": 5.0,
    "y_km": 3.0,
    "ur_cm_s": 1.0,
    "mean": 0.142417,
    "lo": 0.125333,
    "hi": 0.166
   },
   {
    "label": "outlet x=10000 y=3000 ur=0.0",
    "x_km": 10.0,
    "y_km": 3.0,
    "ur_cm_s": 0.0,
    "mean": 0.106417,
    "lo": 0.096667,
    "hi": 0.112
   },
   {
    "label": "outlet x=10000 y=3000 ur=0.01",
    "x_km": 10.0,
    "y_km": 3.0,
    "ur_cm_s": 1.0,
    "mean": 0.128833,
    "lo": 0.115333,
    "hi": 0.149333
   },
   {
    "label": "outlet x=15000 y=3000 ur=0.0",
    "x_km": 15.0,
    "y_km": 3.0,
    "ur_cm_s": 0.0,
    "mean": 0.104417,
    "lo": 0.095333,
    "hi": 0.111333
   },
   {
    "label": "outlet x=15000 y=3000 ur=0.01",
    "x_km": 15.0,
    "y_km": 3.0,
    "ur_cm_s": 1.0,
    "mean": 0.099917,
    "lo": 0.086,
    "hi": 0.121333
   }
  ],
  "note": "Share of swarm reaching intake vs release outlet position; [mean, lo, hi]."
 },
 "noharm": {
  "source": "twin/out/v5_noharm.json (script twin/v5nh.py: eta_r=0.9, outlet x=1200 y=5000, 240 h)",
  "rows": [
   {
    "label": "release only",
    "mean": 0.499417,
    "lo": 0.485333,
    "hi": 0.518
   },
   {
    "label": "hold unlimited (=no release during bloom)",
    "mean": 0.104417,
    "lo": 0.095333,
    "hi": 0.111333
   },
   {
    "label": "hold-alive cap 25 t real",
    "mean": 0.483,
    "lo": 0.466,
    "hi": 0.500667
   },
   {
    "label": "hold-alive cap 50 t real",
    "mean": 0.469583,
    "lo": 0.451333,
    "hi": 0.488
   },
   {
    "label": "hold-alive cap 100 t real",
    "mean": 0.429417,
    "lo": 0.412,
    "hi": 0.449333
   },
   {
    "label": "hold-alive cap 200 t real",
    "mean": 0.3625,
    "lo": 0.353333,
    "hi": 0.388667
   },
   {
    "label": "hold-alive cap 400 t real",
    "mean": 0.226,
    "lo": 0.21,
    "hi": 0.242667
   }
  ]
 },
 "mechanisms": {
  "source": "TESTS/10_mechanisms/results/sim_mechanisms.json",
  "label": "SIMULATED virtual tank - not physical evidence",
  "T_run_s": 150.0,
  "n_bells": 30,
  "seeds": 4,
  "rows": [
   {
    "config": "A0 baseline 10% bypass, 2 entr, 4-6 cm bells",
    "eta_mean": 0.425,
    "eta_se": 0.016,
    "stuck_mean": 0.508,
    "intake_mean": 0.0,
    "n_seeds": 4
   },
   {
    "config": "A1 belt 0.5x sweep",
    "eta_mean": 1.0,
    "eta_se": 0.0,
    "stuck_mean": 0.0,
    "intake_mean": 0.0,
    "n_seeds": 4
   },
   {
    "config": "A2 belt 1.0x sweep",
    "eta_mean": 1.0,
    "eta_se": 0.0,
    "stuck_mean": 0.0,
    "intake_mean": 0.0,
    "n_seeds": 4
   },
   {
    "config": "A3 belt 1.2x sweep",
    "eta_mean": 1.0,
    "eta_se": 0.0,
    "stuck_mean": 0.0,
    "intake_mean": 0.0,
    "n_seeds": 4
   },
   {
    "config": "A4 belt 0.25x sweep",
    "eta_mean": 1.0,
    "eta_se": 0.0,
    "stuck_mean": 0.0,
    "intake_mean": 0.0,
    "n_seeds": 4
   },
   {
    "config": "A5 belt 1.0x, sticky: mu 1.0 + adhesion 3 Pa",
    "eta_mean": 1.0,
    "eta_se": 0.0,
    "stuck_mean": 0.0,
    "intake_mean": 0.0,
    "n_seeds": 4
   },
   {
    "config": "A6 belt 1.0x, bypass only 3%",
    "eta_mean": 1.0,
    "eta_se": 0.0,
    "stuck_mean": 0.0,
    "intake_mean": 0.0,
    "n_seeds": 4
   },
   {
    "config": "A7 belt 1.0x, 15 deg",
    "eta_mean": 1.0,
    "eta_se": 0.0,
    "stuck_mean": 0.0,
    "intake_mean": 0.0,
    "n_seeds": 4
   },
   {
    "config": "B0 coating mu 0.1",
    "eta_mean": 0.65,
    "eta_se": 0.017,
    "stuck_mean": 0.317,
    "intake_mean": 0.0,
    "n_seeds": 4
   },
   {
    "config": "B1 coating mu 0.05",
    "eta_mean": 0.667,
    "eta_se": 0.024,
    "stuck_mean": 0.258,
    "intake_mean": 0.0,
    "n_seeds": 4
   },
   {
    "config": "C1 agitation turb 25% (jet proxy)",
    "eta_mean": 0.533,
    "eta_se": 0.036,
    "stuck_mean": 0.2,
    "intake_mean": 0.0,
    "n_seeds": 4
   },
   {
    "config": "D0 v4: 4 entr, 20% bypass",
    "eta_mean": 0.767,
    "eta_se": 0.0,
    "stuck_mean": 0.233,
    "intake_mean": 0.0,
    "n_seeds": 4
   },
   {
    "config": "D1 v4 + belt 1.0x",
    "eta_mean": 1.0,
    "eta_se": 0.0,
    "stuck_mean": 0.0,
    "intake_mean": 0.0,
    "n_seeds": 4
   },
   {
    "config": "D2 v4 + belt 1.0x + 10 cm apex mouth",
    "eta_mean": 1.0,
    "eta_se": 0.0,
    "stuck_mean": 0.0,
    "intake_mean": 0.0,
    "n_seeds": 4
   },
   {
    "config": "D3 v4 + coating mu 0.05",
    "eta_mean": 0.85,
    "eta_se": 0.022,
    "stuck_mean": 0.15,
    "intake_mean": 0.0,
    "n_seeds": 4
   },
   {
    "config": "E0 scaled bells 1.5-2.5 cm, v4",
    "eta_mean": 0.717,
    "eta_se": 0.029,
    "stuck_mean": 0.283,
    "intake_mean": 0.0,
    "n_seeds": 4
   },
   {
    "config": "E1 scaled bells, v4 + belt 1.0x",
    "eta_mean": 1.0,
    "eta_se": 0.0,
    "stuck_mean": 0.0,
    "intake_mean": 0.0,
    "n_seeds": 4
   },
   {
    "config": "E2 scaled bells, 10% + belt 1.0x",
    "eta_mean": 1.0,
    "eta_se": 0.0,
    "stuck_mean": 0.0,
    "intake_mean": 0.0,
    "n_seeds": 4
   }
  ]
 },
 "vt_guidance": {
  "source": "TESTS/07_virtual_tank/results/SIM_T02_T03_guidance.csv; TESTS/07_virtual_tank/results/SIM_sensitivity.json",
  "label": "SIMULATED virtual tank - not physical evidence",
  "columns_used": [
   "test",
   "screen_angle_deg",
   "approach_speed_cm_s",
   "n_released",
   "n_bypass",
   "n_intake",
   "n_stuck_on_screen",
   "n_lost"
  ],
  "derivation": "eta_r = n_bypass/n_released (mean over protocol runs); T02 rows 1-3 = bypass off, rows 4-6 = bypass on (order matches sim_results.json T02 conditions)",
  "rows": [
   {
    "config": "T02 no screen, bypass off",
    "screen_angle_deg": "none",
    "approach_speed_cm_s": 11.0,
    "n_runs": 3,
    "eta_r_mean": 0.0,
    "intake_frac_mean": 0.966667,
    "stuck_frac_mean": 0.0,
    "lost_frac_mean": 0.033333
   },
   {
    "config": "T02 no screen, bypass on (control)",
    "screen_angle_deg": "none",
    "approach_speed_cm_s": 11.0,
    "n_runs": 3,
    "eta_r_mean": 0.211111,
    "intake_frac_mean": 0.766667,
    "stuck_frac_mean": 0.0,
    "lost_frac_mean": 0.022222
   },
   {
    "config": "T03 screen 8 deg",
    "screen_angle_deg": "8",
    "approach_speed_cm_s": 11.0,
    "n_runs": 3,
    "eta_r_mean": 0.466667,
    "intake_frac_mean": 0.0,
    "stuck_frac_mean": 0.433333,
    "lost_frac_mean": 0.1
   },
   {
    "config": "T03 screen 11 deg",
    "screen_angle_deg": "11",
    "approach_speed_cm_s": 11.0,
    "n_runs": 3,
    "eta_r_mean": 0.5,
    "intake_frac_mean": 0.0,
    "stuck_frac_mean": 0.444444,
    "lost_frac_mean": 0.055556
   },
   {
    "config": "T03 screen 15 deg",
    "screen_angle_deg": "15",
    "approach_speed_cm_s": 11.0,
    "n_runs": 3,
    "eta_r_mean": 0.555556,
    "intake_frac_mean": 0.0,
    "stuck_frac_mean": 0.355556,
    "lost_frac_mean": 0.088889
   },
   {
    "config": "T03 screen 20 deg",
    "screen_angle_deg": "20",
    "approach_speed_cm_s": 11.0,
    "n_runs": 3,
    "eta_r_mean": 0.688889,
    "intake_frac_mean": 0.0,
    "stuck_frac_mean": 0.311111,
    "lost_frac_mean": 0.0
   }
  ],
  "bypass_scan": {
   "source": "TESTS/07_virtual_tank/results/SIM_sensitivity.json 'bypass' (key angle|bypass fraction; 120 s runs, 3 seeds)",
   "rows": [
    {
     "screen_angle_deg": 11.0,
     "bypass_flow_frac": 0.03,
     "bypass_pct": 3.0,
     "eta_mean": 0.3,
     "eta_sem": 0.019245,
     "stuck_mean": 0.555556
    },
    {
     "screen_angle_deg": 11.0,
     "bypass_flow_frac": 0.1,
     "bypass_pct": 10.0,
     "eta_mean": 0.433333,
     "eta_sem": 0.019245,
     "stuck_mean": 0.388889
    },
    {
     "screen_angle_deg": 11.0,
     "bypass_flow_frac": 0.2,
     "bypass_pct": 20.0,
     "eta_mean": 0.588889,
     "eta_sem": 0.011111,
     "stuck_mean": 0.322222
    },
    {
     "screen_angle_deg": 11.0,
     "bypass_flow_frac": 0.35,
     "bypass_pct": 35.0,
     "eta_mean": 0.822222,
     "eta_sem": 0.011111,
     "stuck_mean": 0.166667
    }
   ]
  },
  "design_variants": {
   "source": "TESTS/07_virtual_tank/results/SIM_sensitivity.json 'design'",
   "rows": [
    {
     "config": "bells 1.5-2.5 cm",
     "eta_mean": 0.633333,
     "eta_sem": 0.019245,
     "stuck_mean": 0.366667
    },
    {
     "config": "bells 1.5-2.5 cm, bypass 3%",
     "eta_mean": 0.444444,
     "eta_sem": 0.011111,
     "stuck_mean": 0.533333
    },
    {
     "config": "4 entrances, bypass 20%",
     "eta_mean": 0.733333,
     "eta_sem": 0.033333,
     "stuck_mean": 0.266667
    },
    {
     "config": "bells 1.5-2.5 cm, 20 deg",
     "eta_mean": 0.533333,
     "eta_sem": 0.033333,
     "stuck_mean": 0.466667
    },
    {
     "config": "entrance 10 cm",
     "eta_mean": 0.611111,
     "eta_sem": 0.022222,
     "stuck_mean": 0.311111
    },
    {
     "config": "entrance 10 cm, bypass 3%",
     "eta_mean": 0.522222,
     "eta_sem": 0.011111,
     "stuck_mean": 0.377778
    }
   ]
  }
 },
 "sensitivity": {
  "source": "TESTS/01_twin_VV/out/t5_sensitivity.json",
  "which": "morris_v3 (protected v3 design; output = % of swarm reaching intake). morris_today also given for the unprotected baseline.",
  "morris": [
   {
    "param": "eta_r",
    "mu": -37.155,
    "mu_star": 37.155,
    "sigma": 25.85664,
    "ci_lo": 27.086156,
    "ci_hi": 49.386281
   },
   {
    "param": "eta_g",
    "mu": -31.64625,
    "mu_star": 31.64625,
    "sigma": 18.789077,
    "ci_lo": 24.01125,
    "ci_hi": 39.682594
   },
   {
    "param": "ur",
    "mu": -7.5075,
    "mu_star": 24.195,
    "sigma": 31.540133,
    "ci_lo": 15.408281,
    "ci_hi": 33.56025
   },
   {
    "param": "vr",
    "mu": -15.84375,
    "mu_star": 15.84375,
    "sigma": 13.272756,
    "ci_lo": 10.417031,
    "ci_hi": 21.548906
   },
   {
    "param": "gate_y",
    "mu": -15.3975,
    "mu_star": 15.3975,
    "sigma": 10.264293,
    "ci_lo": 11.126156,
    "ci_hi": 19.777969
   },
   {
    "param": "hours",
    "mu": 9.8775,
    "mu_star": 9.8775,
    "sigma": 10.674659,
    "ci_lo": 5.503594,
    "ci_hi": 14.456344
   },
   {
    "param": "swim",
    "mu": -8.4525,
    "mu_star": 9.5175,
    "sigma": 10.582461,
    "ci_lo": 5.433562,
    "ci_hi": 13.541344
   },
   {
    "param": "U0",
    "mu": 0.18375,
    "mu_star": 1.51125,
    "sigma": 2.341492,
    "ci_lo": 0.851156,
    "ci_hi": 2.373844
   }
  ],
  "ranking": [
   "eta_r",
   "eta_g",
   "ur",
   "vr",
   "gate_y",
   "hours",
   "swim",
   "U0"
  ],
  "morris_today": [
   {
    "param": "eta_g",
    "mu_star": 0.0,
    "sigma": 0.0
   },
   {
    "param": "eta_r",
    "mu_star": 0.0,
    "sigma": 0.0
   },
   {
    "param": "swim",
    "mu_star": 5.6025,
    "sigma": 6.085201
   },
   {
    "param": "vr",
    "mu_star": 4.77,
    "sigma": 4.138607
   },
   {
    "param": "ur",
    "mu_star": 30.28125,
    "sigma": 27.558247
   },
   {
    "param": "gate_y",
    "mu_star": 0.0,
    "sigma": 0.0
   },
   {
    "param": "hours",
    "mu_star": 4.2975,
    "sigma": 4.719019
   },
   {
    "param": "U0",
    "mu_star": 1.83375,
    "sigma": 2.511687
   }
  ],
  "ranking_today": [
   "ur",
   "swim",
   "vr",
   "hours",
   "U0",
   "eta_g",
   "eta_r",
   "gate_y"
  ],
  "sobol": [
   {
    "param": "eta_r",
    "S1": 0.273541,
    "S1_ci": [
     0.042885,
     0.52868
    ],
    "ST": 0.368628,
    "ST_ci": [
     0.275279,
     0.47171
    ]
   },
   {
    "param": "eta_g",
    "S1": -0.012228,
    "S1_ci": [
     -0.171858,
     0.151132
    ],
    "ST": 0.187763,
    "ST_ci": [
     0.140514,
     0.252235
    ]
   },
   {
    "param": "ur",
    "S1": 0.00384,
    "S1_ci": [
     -0.153562,
     0.15661
    ],
    "ST": 0.138379,
    "ST_ci": [
     0.104605,
     0.181111
    ]
   },
   {
    "param": "vr",
    "S1": 0.007647,
    "S1_ci": [
     -0.111529,
     0.131781
    ],
    "ST": 0.099749,
    "ST_ci": [
     0.073911,
     0.130931
    ]
   },
   {
    "param": "gate_y",
    "S1": 0.165576,
    "S1_ci": [
     0.02459,
     0.309249
    ],
    "ST": 0.081608,
    "ST_ci": [
     0.061167,
     0.105996
    ]
   },
   {
    "param": "hours",
    "S1": 0.089304,
    "S1_ci": [
     -0.021964,
     0.202364
    ],
    "ST": 0.073955,
    "ST_ci": [
     0.048314,
     0.107036
    ]
   },
   {
    "param": "swim",
    "S1": -0.004024,
    "S1_ci": [
     -0.053763,
     0.054383
    ],
    "ST": 0.01565,
    "ST_ci": [
     0.010942,
     0.022402
    ]
   },
   {
    "param": "U0",
    "S1": -0.004399,
    "S1_ci": [
     -0.030619,
     0.021602
    ],
    "ST": 0.003181,
    "ST_ci": [
     0.002373,
     0.004169
    ]
   }
  ],
  "sobol_ranking_ST": [
   "eta_r",
   "eta_g",
   "ur",
   "vr",
   "gate_y",
   "hours",
   "swim",
   "U0"
  ],
  "sobol_sum_S1": 0.519258,
  "sobol_output_mean_pct": 42.054297,
  "ranges": {
   "eta_g": [
    0.2,
    0.8
   ],
   "eta_r": [
    0.3,
    0.95
   ],
   "swim": [
    0.02,
    0.15
   ],
   "vr": [
    -0.04,
    0.0
   ],
   "ur": [
    -0.02,
    0.02
   ],
   "gate_y": [
    2000,
    6000
   ],
   "hours": [
    72,
    240
   ],
   "U0": [
    0.08,
    0.15
   ]
  },
  "settings": {
   "morris_r": 20,
   "morris_levels": 4,
   "sobol_base": 128,
   "N_particles_morris": 1000,
   "N_particles_sobol": 1000
  }
 },
 "hydraulics": {
  "source": "TESTS/02_hydraulics_structures/out/results_summary.csv; titles from TESTS/02_hydraulics_structures/README.md",
  "n_checks": 300,
  "totals": {
   "PASS": 180,
   "MARGINAL": 43,
   "FAIL": 77
  },
  "by_test": [
   {
    "test": "T01",
    "title": "Screen sizing",
    "PASS": 21,
    "MARGINAL": 4,
    "FAIL": 8
   },
   {
    "test": "T02",
    "title": "Head loss and trigger filtering",
    "PASS": 22,
    "MARGINAL": 3,
    "FAIL": 5
   },
   {
    "test": "T03",
    "title": "Blinding dynamics",
    "PASS": 19,
    "MARGINAL": 9,
    "FAIL": 16
   },
   {
    "test": "T04",
    "title": "Structural loads",
    "PASS": 42,
    "MARGINAL": 5,
    "FAIL": 12
   },
   {
    "test": "T05",
    "title": "Roll-up pulse",
    "PASS": 11,
    "MARGINAL": 3,
    "FAIL": 14
   },
   {
    "test": "T06",
    "title": "Bypass hydraulics",
    "PASS": 6,
    "MARGINAL": 0,
    "FAIL": 6
   },
   {
    "test": "T07",
    "title": "Archimedes screw",
    "PASS": 14,
    "MARGINAL": 5,
    "FAIL": 3
   },
   {
    "test": "T08",
    "title": "Pipe",
    "PASS": 29,
    "MARGINAL": 10,
    "FAIL": 11
   },
   {
    "test": "T09",
    "title": "Energy",
    "PASS": 6,
    "MARGINAL": 0,
    "FAIL": 0
   },
   {
    "test": "T10",
    "title": "Materials",
    "PASS": 10,
    "MARGINAL": 4,
    "FAIL": 2
   }
  ]
 },
 "fea": {
  "source": "TESTS/08_controls_extremes_FEA/RESULTS.json (summary in SUMMARY.md)",
  "rows": [
   {
    "area": "Structure",
    "check": "A1 stress OP1",
    "value": 0.378,
    "unit": "utilisation",
    "criterion": "util <= 1 (0.60 fy); MARGINAL > 0.9",
    "verdict": "PASS",
    "detail": "OP1 operating: D+L+rollup+dP(1.5xtrip)+Hs1.0 wave+0.5 m/s current+20 m/s wind"
   },
   {
    "area": "Structure",
    "check": "A1 stress ACC1",
    "value": 0.805,
    "unit": "utilisation",
    "criterion": "util <= 1 (0.91 fy); MARGINAL > 0.9",
    "verdict": "PASS",
    "detail": "ACC1 stuck drum, blinded bay dP=3 kPa: D+dP_acc+current"
   },
   {
    "area": "Structure",
    "check": "A1 stress SURV45",
    "value": 0.589,
    "unit": "utilisation",
    "criterion": "util <= 1 (0.80 fy); MARGINAL > 0.9",
    "verdict": "PASS",
    "detail": "SURV45 stowed 100-yr, 45 deg"
   },
   {
    "area": "Structure",
    "check": "A2 pile lateral deflection, operating (rail alignment)",
    "value": 21.0,
    "unit": "mm",
    "criterion": "<= 25 mm [ASM: guide-rail/mesh-edge retention]",
    "verdict": "PASS",
    "detail": null
   },
   {
    "area": "Structure",
    "check": "A2b pile lateral deflection, stuck-drum accident",
    "value": 50.2,
    "unit": "mm",
    "criterion": "<= 75 mm (mesh stays in rails) [ASM]",
    "verdict": "PASS",
    "detail": null
   },
   {
    "area": "Modal",
    "check": "A3 modal: f1 vs wave band 0.125-0.5 Hz (2-8 s)",
    "value": 1.498,
    "unit": "Hz",
    "criterion": "no mode within 2-8 s wave band; f1 > 0.5 Hz (T1 < 2 s)",
    "verdict": "PASS",
    "detail": "T1=0.67 s; data waves 1.5-6.25 s (mean period); modes in band: []"
   },
   {
    "area": "Structure",
    "check": "A4 current VIV (in-line onset Vr>1)",
    "value": 0.84,
    "unit": "Vr",
    "criterion": "Vr < 1 (DNV-RP-C205 in-line onset)",
    "verdict": "PASS",
    "detail": "{'U=0.5 m/s': 0.3, 'U=1.0 m/s': 0.6, 'U=1.4 m/s': 0.84}"
   },
   {
    "area": "Structure",
    "check": "A5 linear buckling (gravity + roll-up)",
    "value": 102.7,
    "unit": "load factor",
    "criterion": "load factor >= 10 (sway/global) [ENG]",
    "verdict": "PASS",
    "detail": null
   },
   {
    "area": "Fatigue",
    "check": "A6 fatigue 60 y fixity_freecorr (unsheltered Kt=1)",
    "value": 0.058,
    "unit": "Miner D x DFF",
    "criterion": "Miner D x DFF <= 1 (DNV-RP-C203)",
    "verdict": "PASS",
    "detail": "life ~1.03e+03 y"
   },
   {
    "area": "Fatigue",
    "check": "A6 fatigue 60 y fixity_CP (unsheltered Kt=1)",
    "value": 0.0,
    "unit": "Miner D x DFF",
    "criterion": "Miner D x DFF <= 1 (DNV-RP-C203)",
    "verdict": "PASS",
    "detail": "life ~2.44e+05 y"
   },
   {
    "area": "Structure",
    "check": "A7 sensitivity: pile fixity 3-7 D",
    "value": 0.886,
    "unit": "utilisation",
    "criterion": "worst util <= 1",
    "verdict": "PASS",
    "detail": "{\"fixity 3D\": {\"OP1\": 0.329, \"ACC1\": 0.703, \"SURV0\": 0.272, \"SURV45\": 0.5, \"SURV90\": 0.442}, \"fixity 5D\": {\"OP1\": 0.378, \"ACC1\": 0.805, \"SURV0\": 0.318, \"SURV45\": 0.589, \"SURV90\": 0.521}, \"fixity 7D\": {\"OP1\": 0.419, \"ACC…"
   },
   {
    "area": "Structure",
    "check": "A7 sensitivity: membrane sag 2-8 % of span",
    "value": 1.081,
    "unit": "utilisation",
    "criterion": "worst util <= 1",
    "verdict": "FAIL",
    "detail": "{\"sag 2%\": {\"OP1\": 0.483, \"ACC1\": 1.081, \"SURV0\": 0.318, \"SURV45\": 0.589, \"SURV90\": 0.521}, \"sag 5%\": {\"OP1\": 0.295, \"ACC1\": 0.584, \"SURV0\": 0.318, \"SURV45\": 0.589, \"SURV90\": 0.521}, \"sag 8%\": {\"OP1\": 0.248, \"ACC1\": 0.4…"
   },
   {
    "area": "Mesh",
    "check": "A8 mesh wire tension, stuck-drum accident (elastic-taut)",
    "value": 0.71,
    "unit": "utilisation",
    "criterion": "wire stress <= 410.0 MPa",
    "verdict": "PASS",
    "detail": "T=113.8 kN/m, sag 0.33 m"
   },
   {
    "area": "Mesh",
    "check": "A8c wire bending on drum wrap (roll-up fatigue)",
    "value": 820,
    "unit": "MPa",
    "criterion": "E*d/D <= 0.4 fy = 180 MPa (~56160 wraps in 60 y)",
    "verdict": "FAIL",
    "detail": "D_core=0.61 m, d=2.5 mm -> need D >= 2.78 m or d <= 0.55 mm, or hinged link/balanced-weave belt (no wire bending)"
   },
   {
    "area": "Seismic",
    "check": "B1 seismic RSA S1",
    "value": 0.136,
    "unit": "utilisation",
    "criterion": "stress <= 0.80 fy (elastic, R=1)",
    "verdict": "PASS",
    "detail": "S1 IBC design (2/3 MCE, Site D); Sa(T1)=0.18 g; head disp {'x': 11.8, 'y': 27.9}"
   },
   {
    "area": "Seismic",
    "check": "B1 seismic RSA S2",
    "value": 0.159,
    "unit": "utilisation",
    "criterion": "stress <= 1.00 fy (elastic, R=1)",
    "verdict": "PASS",
    "detail": "S2 MCE 2475-yr (Seismic II/I no-collapse); Sa(T1)=0.27 g; head disp {'x': 17.7, 'y': 41.9}"
   },
   {
    "area": "Seismic",
    "check": "B1 seismic RSA S3",
    "value": 0.388,
    "unit": "utilisation",
    "criterion": "stress <= 1.00 fy (elastic, R=1)",
    "verdict": "PASS",
    "detail": "S3 nuclear envelope PGA 0.3 g; Sa(T1)=0.674 g; head disp {'x': 46.5, 'y': 104.7}"
   },
   {
    "area": "Seismic",
    "check": "B2 nuclear seismic classification",
    "value": "Seismic II/I (assumed)",
    "unit": null,
    "criterion": "Structure in UHS/CW path near safety SSCs must not collapse onto them or block the intake; site SSE & intake layout not public",
    "verdict": "INFO",
    "detail": "Needs: site-specific SSE spectra from Nawah FSAR Ch.2/3; II/I interaction analysis; post-quake fail-open (all bays up) on PLC seismic trip; seismic qualification of drum brakes"
   },
   {
    "area": "Extremes",
    "check": "C1 wind survival (stowed): design gust vs data 100-yr",
    "value": "design 45.0 m/s; ERA5 Gumbel 100-yr 23.5 m/s",
    "unit": null,
    "criterion": "design >= max(code 38-45 m/s, data EVA); FEA SURV cases pass at 45 m/s (A1)",
    "verdict": "PASS",
    "detail": "ERA5 under-estimates gusts; Abu Dhabi municipal basic wind speed not found -> confirm with ADM/DMT"
   },
   {
    "area": "Extremes",
    "check": "C3 100-yr Hs: data POT vs design",
    "value": "design Hs100 4.0 m; data POT near 1.76 m, off 3.96 m",
    "unit": null,
    "criterion": "design >= literature 3.0-4.5 m (9-16 m depth, Neelamani) and data EVA",
    "verdict": "PASS",
    "detail": "only 4 years of data -> data EVA is indicative; literature governs"
   },
   {
    "area": "Climate 2085",
    "check": "C5 air gap 2085 SSP5-8.5 median - inner gantry (sheltered Kt=0.5 ASM)",
    "value": "0.4 m",
    "unit": "m",
    "criterion": "crest below deck soffit +5.6 m MSL with >= 1.0 m margin [ENG]",
    "verdict": "MARGINAL",
    "detail": "SWL 2.41 m, Hmax 3.72 m, crest 5.2 m; raise soffit to 6.2 m MSL"
   },
   {
    "area": "Climate 2085",
    "check": "C5 air gap 2085 SSP5-8.5 median - outer guide line (exposed)",
    "value": "-2.39 m",
    "unit": "m",
    "criterion": "crest below deck soffit +5.6 m MSL with >= 1.0 m margin [ENG]",
    "verdict": "FAIL",
    "detail": "SWL 2.41 m, Hmax 7.44 m, crest 7.99 m; raise soffit to 8.99 m MSL"
   },
   {
    "area": "Climate 2085",
    "check": "C5 air gap 2085 low-confidence high-end - inner gantry (sheltered Kt=0.5 ASM)",
    "value": "-0.49 m",
    "unit": "m",
    "criterion": "crest below deck soffit +5.6 m MSL with >= 1.0 m margin [ENG]",
    "verdict": "FAIL",
    "detail": "SWL 3.3 m, Hmax 3.72 m, crest 6.09 m; raise soffit to 7.09 m MSL"
   },
   {
    "area": "Hydraulics",
    "check": "C6 low tide (LAT) screen approach velocity at nominal 100 m3/s",
    "value": 0.128,
    "unit": "m/s",
    "criterion": "<= 0.12 m/s (NMFS active screen)",
    "verdict": "MARGINAL",
    "detail": "[{\"bed\": -5.5, \"Q\": 100.0, \"depth_LAT\": 4.3, \"lane_v\": 0.83, \"screen_v\": 0.128}, {\"bed\": -5.5, \"Q\": 172.5, \"depth_LAT\": 4.3, \"lane_v\": 1.43, \"screen_v\": 0.221}, {\"bed\": -7.5, \"Q\": 100.0, \"depth_LAT\": 6.3, \"lane_v\": 0.57…"
   },
   {
    "area": "Hydraulics",
    "check": "C6b low tide screen velocity at max 172.5 m3/s",
    "value": 0.221,
    "unit": "m/s",
    "criterion": "<= 0.12 m/s",
    "verdict": "FAIL",
    "detail": "relief: add bays/lengthen line for low-water max-flow, or accept higher approach at LAT"
   },
   {
    "area": "Materials",
    "check": "C7 duplex 2205/2507 mesh & crevices at SST 36-38 C",
    "value": "data max 36.3 C; design 38.0 C",
    "unit": null,
    "criterion": "NORSOK M-001 Rev.5: 25Cr duplex <= 20 C in seawater with crevices (via TWI)",
    "verdict": "FAIL",
    "detail": "woven-mesh knuckles and rail contacts are crevices; immersion is in the hottest months. Use titanium Gr2, Cu-Ni 90/10, or polymer (HDPE/PET/UHMWPE) mesh; keep duplex only above water"
   },
   {
    "area": "Climate 2085",
    "check": "G3 SST 2085 vs material limits",
    "value": "max data 35.9 C + 3.0 C = 38.9 C",
    "unit": null,
    "criterion": "mesh/rail materials rated for >= 40 C seawater",
    "verdict": "FAIL",
    "detail": "reinforces C7: specify titanium or polymer wetted parts"
   },
   {
    "area": "Climate 2085",
    "check": "G2 warmer water -> longer hot season (SST>=32 C proxy)",
    "value": "120 d/yr now -> 174 d/yr (2085, +0.5 C/dec)",
    "unit": null,
    "criterion": "deployed-days margin: fatigue/energy/wear designed for 60 d/yr [V3 ~2 months]",
    "verdict": "MARGINAL",
    "detail": "if blooms track hot season, duty rises; fatigue (A6) has large margin, corrosion (C7) and drum-wrap cycles (A8c) get worse"
   },
   {
    "area": "Human factors",
    "check": "E1 alarm rate, naive HMI (V8 redesign (belt + flap))",
    "value": "3.2/h, peak 6/10 min, 0 flood windows",
    "unit": null,
    "criterion": "<= 6/h average and no 10-min window > 10 (ISA-18.2/EEMUA 191)",
    "verdict": "PASS",
    "detail": null
   },
   {
    "area": "LCA",
    "check": "F1 LCA: JAZR 60-y CO2 vs avoided unit-days",
    "value": "P50 1.6 unit-days (P10-P90 1.3-2.0)",
    "unit": null,
    "criterion": "carbon break-even <= 5 avoided unit-days over 60 y [ASM]",
    "verdict": "PASS",
    "detail": null
   }
  ],
  "totals": {
   "PASS": 48,
   "MARGINAL": 12,
   "FAIL": 15,
   "INFO": 6
  },
  "n_checks": 81,
  "unit_note": "Units assigned from each row's criterion text (utilisation = stress / allowable)."
 },
 "controls": {
  "source": "TESTS/08_controls_extremes_FEA/D_controls/out/model_check.json; controls_results.json; D-rows of TESTS/08_controls_extremes_FEA/RESULTS.json",
  "rows": [
   {
    "check": "MC1a n=1 all events/inputs: states",
    "value": 1114,
    "verdict": "INFO"
   },
   {
    "check": "MC1a n=1 all events/inputs: distinct transitions",
    "value": 15609,
    "verdict": "INFO"
   },
   {
    "check": "MC1a n=1 all events/inputs: invariant violations",
    "value": 0,
    "verdict": "PASS"
   },
   {
    "check": "MC1a n=1 all events/inputs: deadlocks",
    "value": 0,
    "verdict": "PASS"
   },
   {
    "check": "MC1a n=1 all events/inputs: states unable to reach safe IDLE",
    "value": 0,
    "verdict": "PASS"
   },
   {
    "check": "MC1b n=2: states",
    "value": 26633,
    "verdict": "INFO"
   },
   {
    "check": "MC1b n=2: distinct transitions",
    "value": 638588,
    "verdict": "INFO"
   },
   {
    "check": "MC1b n=2: invariant violations",
    "value": 0,
    "verdict": "PASS"
   },
   {
    "check": "MC1b n=2: deadlocks",
    "value": 0,
    "verdict": "PASS"
   },
   {
    "check": "MC1b n=2: states unable to reach safe IDLE",
    "value": 0,
    "verdict": "PASS"
   },
   {
    "check": "MC2 pulse rule under comms loss, TDMA only: violating transitions",
    "value": 276192,
    "verdict": "FAIL"
   },
   {
    "check": "MC2 pulse rule under comms loss, busy-line only: violating transitions",
    "value": 322472,
    "verdict": "FAIL"
   },
   {
    "check": "MC2 pulse rule under comms loss, TDMA + busy-line: violating transitions",
    "value": 0,
    "verdict": "PASS"
   },
   {
    "check": "MC2 pulse rule under comms loss, none (each LBC free): violating transitions",
    "value": 510320,
    "verdict": "FAIL"
   },
   {
    "check": "MC3 wildlife/outlet exhaustive cases (violations)",
    "value": "16800 cases, 0 violations",
    "verdict": "PASS"
   },
   {
    "check": "MC4 IT/OT separation (differences)",
    "value": "159798 checks, 0 differing",
    "verdict": "PASS"
   },
   {
    "check": "D6 dP filter (tau 30 s, 2oo3, 20 s persistence) vs wave spikes Hs 0.5-2.0 m",
    "value": "false trips 0.0/bay-day; latency 42 s",
    "verdict": "PASS",
    "criterion": "0 false trips/day and latency <= 60 s [ASM: audit 'blinds in <2 min at 1/m3']"
   },
   {
    "check": "D6b naive single-transmitter threshold vs waves",
    "value": "Hs 0.5: 0/bay-day, Hs 1.0: 0/bay-day, Hs 1.5: 52/bay-day, Hs 2.0: 828/bay-day",
    "verdict": "FAIL",
    "criterion": "0 false trips/day"
   },
   {
    "check": "D7 stuck-high transmitter (F1) with 2oo3 + 2oo2 hard channel",
    "value": "false dP raises 0",
    "verdict": "PASS",
    "criterion": "0"
   },
   {
    "check": "D7b same fault with single-transmitter hard-wired trip (1oo1)",
    "value": "false dP raises 1 (bay lost for the rest of the bloom)",
    "verdict": "FAIL",
    "criterion": "0"
   },
   {
    "check": "D8 stuck-drum detection latency (F3 seized drive)",
    "value": "1868 s",
    "verdict": "MARGINAL",
    "criterion": "<= 300 s [ASM]"
   },
   {
    "check": "D9 deploy time alert -> OPERATE (2 approvals, 6 drums at once, 0.1 m/s)",
    "value": "573 s",
    "verdict": "MARGINAL",
    "criterion": "<= 600 s [V3 'about 10 min']"
   },
   {
    "check": "D10 roll-up pulse < 1 t (v3 claim)",
    "value": "0.3/m3: max 812 kg; 1/m3: >= 1173 kg; audit residence 300 s: 1615 kg; sticking 10 %: 1724 kg",
    "verdict": "MARGINAL",
    "criterion": "every pulse < 1000 kg"
   },
   {
    "check": "D11 biomass reaching plant with roll-up cleaning + open relief bay (no faults, 0.3/m3)",
    "value": "18-29 % (belt clean-in-place + flap relief: 1.2 %)",
    "verdict": "FAIL",
    "criterion": "<= 10 % (v3 twin assumes inner-screen efficiency 0.9)"
   },
   {
    "check": "D13 seismic/E-stop fail-open time (all bays up, staged 1 at a time)",
    "value": "2046 s",
    "verdict": "MARGINAL",
    "criterion": "<= 600 s [ASM]"
   },
   {
    "check": "D15 redesign check: belt clean-in-place + flap relief, full fault scenario",
    "value": "0.3/m3: leakage 9.5 %, max pulse 372 kg; 1/m3: leakage 12.0 %, max pulse 1639 kg",
    "verdict": "PASS",
    "criterion": "leakage <= 10 %, pulses < 1 t"
   },
   {
    "check": "D16 cybersecurity checklist (13 items)",
    "value": "PASS 4, RISK 9",
    "verdict": "MARGINAL",
    "criterion": "no RISK on items that move bays"
   }
  ],
  "variants": [
   {
    "variant": "V0 v3 as specified (open relief bay, 2oo3+filter, hard 2oo2, TDMA+busy)",
    "leakage_to_plant_fraction": 0.378196,
    "max_event_kg": 1108.146594,
    "events_over_1t": 8,
    "false_dp_raises": 0,
    "deploy_time_s": 453,
    "seismic_all_up_s": 2046
   },
   {
    "variant": "V1 passive flap relief (closed below 600 Pa)",
    "leakage_to_plant_fraction": 0.333862,
    "max_event_kg": 1187.009409,
    "events_over_1t": 11,
    "false_dp_raises": 0,
    "deploy_time_s": 453,
    "seismic_all_up_s": 2046
   },
   {
    "variant": "V2 naive sensing: 1 transmitter, no filter/persistence",
    "leakage_to_plant_fraction": 0.461931,
    "max_event_kg": 988.114799,
    "events_over_1t": 0,
    "false_dp_raises": 1,
    "deploy_time_s": 453,
    "seismic_all_up_s": 1895
   },
   {
    "variant": "V3 hard-wired trip on single transmitter (1oo1)",
    "leakage_to_plant_fraction": 0.461445,
    "max_event_kg": 988.115303,
    "events_over_1t": 0,
    "false_dp_raises": 1,
    "deploy_time_s": 453,
    "seismic_all_up_s": 1895
   },
   {
    "variant": "V4 comms-loss rule without busy line (TDMA only)",
    "leakage_to_plant_fraction": 0.378196,
    "max_event_kg": 1108.146594,
    "events_over_1t": 8,
    "false_dp_raises": 0,
    "deploy_time_s": 453,
    "seismic_all_up_s": 2046
   },
   {
    "variant": "V5 audit residence tau=300 s",
    "leakage_to_plant_fraction": 0.599155,
    "max_event_kg": 1614.850082,
    "events_over_1t": 151,
    "false_dp_raises": 0,
    "deploy_time_s": 453,
    "seismic_all_up_s": 2046
   },
   {
    "variant": "V6 drum speed 0.2 m/s",
    "leakage_to_plant_fraction": 0.381565,
    "max_event_kg": 1148.487159,
    "events_over_1t": 9,
    "false_dp_raises": 0,
    "deploy_time_s": 228,
    "seismic_all_up_s": 1063
   },
   {
    "variant": "V7 sticking s0=10 %",
    "leakage_to_plant_fraction": 0.542223,
    "max_event_kg": 1723.500337,
    "events_over_1t": 146,
    "false_dp_raises": 0,
    "deploy_time_s": 453,
    "seismic_all_up_s": 2046
   },
   {
    "variant": "V8 redesign: endless-belt clean-in-place + flap relief",
    "leakage_to_plant_fraction": 0.094652,
    "max_event_kg": 372.153971,
    "events_over_1t": 0,
    "false_dp_raises": 0,
    "deploy_time_s": 453,
    "seismic_all_up_s": 2129
   },
   {
    "variant": "V9 redesign V8 at 1.0 ind/m3 whole bloom",
    "leakage_to_plant_fraction": 0.119517,
    "max_event_kg": 1639.364216,
    "events_over_1t": 7,
    "false_dp_raises": 0,
    "deploy_time_s": 453,
    "seismic_all_up_s": 2129
   }
  ]
 },
 "cyber": {
  "source": "TESTS/08_controls_extremes_FEA/D_controls/out/cyber_checklist.md",
  "rows": [
   {
    "n": "1",
    "item": "Zones & conduits",
    "standard": "IEC 62443-3-2",
    "requirement": "JAZR OT (PLC + per-bay LBCs) is its own zone, separate from plant I&C and from the IT/twin zone",
    "status": "RISK",
    "note": "v3 silent; Nawah must also decide whether JAZR is 'important to safety' (it is in the CW/UHS path) -> sets the security level"
   },
   {
    "n": "2",
    "item": "No remote control of safety-relevant actions",
    "standard": "NSS 17-T / RG 5.71",
    "requirement": "No internet/vendor remote path; every bay or OS command originates at the control-room HMI or in hard-wired local logic",
    "status": "PASS",
    "note": "controller has no network command input; D5 shows forecast/twin data cannot alter bay commands or OS state (159,798 checks)"
   },
   {
    "n": "3",
    "item": "One-way data flow OT -> IT",
    "standard": "FR5 restricted data flow / RG 5.71 level 4->3",
    "requirement": "Data diode exports load cells, counts and video to the twin; the forecast reaches OT only as an advisory outlet score",
    "status": "PASS",
    "note": "design rule; outlet choice is the only OT output the forecast can move, and stale/unsafe -> RECOVER (D4)"
   },
   {
    "n": "4",
    "item": "Local protection independent of network",
    "standard": "FR7 resource availability",
    "requirement": "Hard dP trip, seismic trip, TDMA + busy-loop staging and screw-stop are hard-wired / local",
    "status": "PASS",
    "note": "D3c model check under comms loss: 0 pulse-rule violations; D14 same-scan responses"
   },
   {
    "n": "5",
    "item": "Identification & authentication",
    "standard": "FR1",
    "requirement": "Named operator log-in; approvals bound to user; 2-person rule for SAFE reset",
    "status": "RISK",
    "note": "v3 says 'human approval at every step' but not who or how authenticated"
   },
   {
    "n": "6",
    "item": "Use control",
    "standard": "FR2",
    "requirement": "Role-based permissions (operator, shift supervisor, maintenance); maintenance mode locks out motion",
    "status": "RISK",
    "note": "not specified"
   },
   {
    "n": "7",
    "item": "System integrity",
    "standard": "FR3",
    "requirement": "Signed PLC/LBC logic, version control, change only through Nawah modification process; camera-AI model frozen & validated",
    "status": "RISK",
    "note": "not specified; AI model updates are a supply-chain vector"
   },
   {
    "n": "8",
    "item": "Data confidentiality",
    "standard": "FR4",
    "requirement": "Video of a nuclear marine security zone and protected species handled as restricted",
    "status": "RISK",
    "note": "CICPA/coast-guard sensitivities (site security zone)"
   },
   {
    "n": "9",
    "item": "Timely response to events",
    "standard": "FR6",
    "requirement": "OT event logging, time-synced, reviewed; alarm on config change",
    "status": "RISK",
    "note": "not specified"
   },
   {
    "n": "10",
    "item": "Time source integrity",
    "standard": "FR3/FR7",
    "requirement": "TDMA staging needs synchronised clocks; GNSS spoofing/drift could align two bays' slots",
    "status": "RISK",
    "note": "busy loop alone races (D3b); use local holdover oscillators, slot guard bands > 2x max skew, plausibility checks"
   },
   {
    "n": "11",
    "item": "Wireless links",
    "standard": "FR5",
    "requirement": "No radio for control; outlet valves 5 km offshore controlled via cable in the pipe bundle",
    "status": "RISK",
    "note": "v3 silent on offshore outlet-valve telemetry"
   },
   {
    "n": "12",
    "item": "Common-mode across units",
    "standard": "defence in depth",
    "requirement": "Separate PLC, LBCs and power per unit; no shared controller",
    "status": "PASS",
    "note": "v3: 'each unit has its own lane and controls'"
   },
   {
    "n": "13",
    "item": "Physical security",
    "standard": "NSS 17-T",
    "requirement": "Gantry cabinets locked, inside the maritime security zone; tamper switches",
    "status": "RISK",
    "note": "coordination with site security needed"
   }
  ],
  "totals": {
   "RISK": 9,
   "PASS": 4
  }
 },
 "permits": {
  "source": "TESTS/05_economics_risk/data/regulatory_checklist.csv",
  "rows": [
   {
    "id": "R1",
    "requirement": "Modification in the cooling-water flow path must go through operator modification control and regulator safety screening",
    "authority": "FANR / Nawah",
    "status": "RISK",
    "why": "v3 acknowledges it (PASS on framing) but schedule/cost unknown; whether ESW shares the approach channel is not public",
    "ref": "16_FLAW_AUDIT row 3; IAEA SSG-71 (2022) Modifications to NPPs; FANR regs stated to be IAEA-based (ARPANSA 2016 FANR keynote)"
   },
   {
    "id": "R2",
    "requirement": "Structures near safety SSCs designed Seismic II/I + storm/tsunami/debris loads",
    "authority": "FANR",
    "status": "RISK",
    "why": "Raises civil cost (inside 30-40% engineering markup here, unverified); no site seismic/hydro data public",
    "ref": "16_ row 3 [ENG]"
   },
   {
    "id": "R3",
    "requirement": "Never block the UHS/cooling flow: permanent open path, passive tested relief",
    "authority": "FANR / Nawah",
    "status": "PASS",
    "why": "v3: always-open relief bay, per-unit lanes, staged per-bay roll-up (<1 t pulses). Needs analysis + test to evidence",
    "ref": "JAZR_GATE_v3.md §2; 16_ rows 3,8"
   },
   {
    "id": "R4",
    "requirement": "Cyber security of remotely actuated control-room system (OS, cameras, drums)",
    "authority": "FANR (FANR-REG-08 v2, physical protection & cyber security, approved May 2024)",
    "status": "RISK",
    "why": "Network connection to a nuclear site control room; v3 is silent on cyber",
    "ref": "WAM, FANR Board May 2024"
   },
   {
    "id": "R5",
    "requirement": "Brief: no redesign of plant systems or new nuclear safety systems",
    "authority": "ENEC brief",
    "status": "RISK",
    "why": "JAZR is outside plant screens but in the flow path; judges may read it as plant redesign",
    "ref": "02_enec_statement_close_reading.md"
   },
   {
    "id": "R6",
    "requirement": "Environmental permit / EIA before marine construction (piling, training wall, 5 km seabed pipe)",
    "authority": "EAD (Federal Law 24/1999)",
    "status": "RISK",
    "why": "EIA likely required; the site's own EIA took >4 years",
    "ref": "WAM 2023 (EAD SEA programme); Khaleej Times 2012; enec.ae environment-permit page"
   },
   {
    "id": "R7",
    "requirement": "Amend the plant's Operational Environmental Permit (renewed annually) for new outlets releasing live biomass",
    "authority": "EAD",
    "status": "RISK",
    "why": "New discharge/release points 5 km offshore = new permitted activity; release fate (decay, strandings, other intakes) must be shown",
    "ref": "enec.ae environment-permit page; 16_ row 14"
   },
   {
    "id": "R8",
    "requirement": "Handling/relocating marine life incl. protected turtles",
    "authority": "MOCCAE / EAD (Federal Law 23/1999; MR 302/2001 protected species incl. marine turtles)",
    "status": "RISK",
    "why": "Camera diverter + auto-stop untested; need zero-harm evidence and consent",
    "ref": "FAOLEX summaries of FL 23/1999 and MR 302/2001"
   },
   {
    "id": "R9",
    "requirement": "Marine works permit, notices to mariners, nav aids for piles/outlets",
    "authority": "Abu Dhabi Maritime (Administrative Decision 69/2025 maritime safety bylaw; AED 30,000 fine for marine works without permit)",
    "status": "RISK",
    "why": "Routine but mandatory; outlets 5 km offshore in navigable water",
    "ref": "admaritime.ae Decision 69/2025 PDF; Gulf News 2025"
   },
   {
    "id": "R10",
    "requirement": "Nuclear site maritime security zone",
    "authority": "CICPA / Coast Guard",
    "status": "RISK",
    "why": "Seabed pipe + outlets cross the zone; sign-off needed (heightened security noted in 16_ audit; not independently verified)",
    "ref": "16_ row 4"
   },
   {
    "id": "R11",
    "requirement": "Decision 17/2026: permits for testing autonomous/remotely operated small marine craft",
    "authority": "Abu Dhabi DMT",
    "status": "N/A",
    "why": "JAZR uses no vessels; APPLIES if the team uses USVs/drones to deploy drifters or survey the outlet",
    "ref": "LexisNexis ME summary 27 Jun 2026 (primary text not read)"
   },
   {
    "id": "R12",
    "requirement": "Disposal of recovered biomass ('recover, not release' mode)",
    "authority": "Abu Dhabi waste regulator / EAD",
    "status": "RISK",
    "why": "Composting/dewatering route not specified; authority not verified",
    "ref": "v3 §2 (unverified)"
   },
   {
    "id": "R13",
    "requirement": "No chemicals / no change to monitored discharge parameters",
    "authority": "ENEC brief / EAD",
    "status": "PASS",
    "why": "JAZR adds no chemicals; brush + low-pressure spray only",
    "ref": "JAZR_GATE_v3.md §2; 02_ file"
   },
   {
    "id": "R14",
    "requirement": "Construction inside operating nuclear site (work control, outage windows)",
    "authority": "Nawah",
    "status": "RISK",
    "why": "Training wall/gantry in an operating intake may need reduced flow (derate) during works",
    "ref": "16_ rows 1,11"
   }
  ],
  "totals": {
   "RISK": 11,
   "PASS": 2,
   "N/A": 1
  },
  "n_items": 14,
  "summary": "14 permit items: 2 PASS, 11 RISK, 1 N/A (matches 00_TEST_REPORT '14 permit items, 2 PASS, 11 RISK')"
 },
 "economics": {
  "source": "TESTS/05_economics_risk/out/results.json",
  "breakeven_unit_days": 0.93,
  "breakeven_note": "Case A (JAZR Core/MC capex), 6% discount: outage unit-days per unit-year avoided needed to break even. Break-even uses mode inputs and the twin's mode reach (12%) and 95% availability; unit-days are outage days on the protected unit WITHOUT JAZR.",
  "breakeven_table": [
   {
    "case": "A_r0.03",
    "capex_unit_musd": 13.6,
    "opex_unit_musd": 0.58,
    "unit_days_per_unit_yr": 0.75,
    "unit_days_over_life_per_unit": 22.4,
    "site_events_per_yr_needed": 0.38,
    "years_between_events_needed": 2.7
   },
   {
    "case": "A_r0.06",
    "capex_unit_musd": 13.6,
    "opex_unit_musd": 0.58,
    "unit_days_per_unit_yr": 0.93,
    "unit_days_over_life_per_unit": 27.9,
    "site_events_per_yr_needed": 0.47,
    "years_between_events_needed": 2.1
   },
   {
    "case": "A_r0.08",
    "capex_unit_musd": 13.6,
    "opex_unit_musd": 0.58,
    "unit_days_per_unit_yr": 1.07,
    "unit_days_over_life_per_unit": 32.0,
    "site_events_per_yr_needed": 0.54,
    "years_between_events_needed": 1.9
   },
   {
    "case": "A_r0.1",
    "capex_unit_musd": 13.6,
    "opex_unit_musd": 0.58,
    "unit_days_per_unit_yr": 1.21,
    "unit_days_over_life_per_unit": 36.4,
    "site_events_per_yr_needed": 0.61,
    "years_between_events_needed": 1.6
   },
   {
    "case": "B_r0.03",
    "capex_unit_musd": 51.0,
    "opex_unit_musd": 1.2,
    "unit_days_per_unit_yr": 2.33,
    "unit_days_over_life_per_unit": 69.8,
    "site_events_per_yr_needed": 1.17,
    "years_between_events_needed": 0.9
   },
   {
    "case": "B_r0.06",
    "capex_unit_musd": 51.0,
    "opex_unit_musd": 1.2,
    "unit_days_per_unit_yr": 3.02,
    "unit_days_over_life_per_unit": 90.5,
    "site_events_per_yr_needed": 1.52,
    "years_between_events_needed": 0.7
   },
   {
    "case": "B_r0.08",
    "capex_unit_musd": 51.0,
    "opex_unit_musd": 1.2,
    "unit_days_per_unit_yr": 3.53,
    "unit_days_over_life_per_unit": 106.0,
    "site_events_per_yr_needed": 1.78,
    "years_between_events_needed": 0.6
   },
   {
    "case": "B_r0.1",
    "capex_unit_musd": 51.0,
    "opex_unit_musd": 1.2,
    "unit_days_per_unit_yr": 4.08,
    "unit_days_over_life_per_unit": 122.5,
    "site_events_per_yr_needed": 2.06,
    "years_between_events_needed": 0.5
   }
  ],
  "cost_bounds_musd": {
   "low": 23.8,
   "mode": 51.0,
   "high": 124.5,
   "direct": {
    "low": 16.5,
    "mode": 29.1,
    "high": 59.3
   },
   "total_AED_M": {
    "low": 87,
    "mode": 187,
    "high": 457
   },
   "note": "Full-system (case B) per-unit cost bounds, MUSD"
  },
  "cost_table_mode_musd_per_unit": {
   "training_wall_150-200m": 4.0,
   "piled_gantry_150-200m": 6.0,
   "mesh_bays_drums_rails_motors": 4.0,
   "bypass_camera_screw_headtank_pump": 4.0,
   "seabed_HDPE_pipe_5km_1.2mID": 10.0,
   "outlets_x2_diffusers": 1.0,
   "controls_OS_sensors_share": 0.07,
   "SUBTOTAL direct": 29.07,
   "engineering/nuclear QA/licensing/seismic": 8.72,
   "contingency": 13.23,
   "TOTAL per unit": 51.02
  },
  "capex_mc_p10_p50_p90_musd": {
   "A": [
    10.9,
    14.3,
    18.4
   ],
   "B": [
    51.6,
    61.0,
    71.6
   ]
  },
  "payback": [
   {
    "label": "A-S0",
    "case": "A",
    "scenario": "S0 base (global Gamma-Poisson + the site 0 events/5.5 yr)",
    "rate_events_per_site_yr": 0.0147,
    "p_payback": 0.001,
    "npv_p50_musd": -80.3
   },
   {
    "label": "A-S1",
    "case": "A",
    "scenario": "S1 jellyfish-prone site (pooled rate of sites with >=1 event)",
    "rate_events_per_site_yr": 0.0565,
    "p_payback": 0.003,
    "npv_p50_musd": -73.9
   },
   {
    "label": "A-S2",
    "case": "A",
    "scenario": "S2 Hanul-like (9 shutdowns 1996-2006)",
    "rate_events_per_site_yr": 0.8182,
    "p_payback": 0.872,
    "npv_p50_musd": 53.9
   },
   {
    "label": "A-S3",
    "case": "A",
    "scenario": "S3 Gravelines-like (3 events 2025-26)",
    "rate_events_per_site_yr": 1.5,
    "p_payback": 0.999,
    "npv_p50_musd": 171.5
   },
   {
    "label": "B-S0",
    "case": "B",
    "scenario": "S0 base (global Gamma-Poisson + the site 0 events/5.5 yr)",
    "rate_events_per_site_yr": 0.0147,
    "p_payback": 0.0,
    "npv_p50_musd": -300.1
   },
   {
    "label": "B-S1",
    "case": "B",
    "scenario": "S1 jellyfish-prone site (pooled rate of sites with >=1 event)",
    "rate_events_per_site_yr": 0.0565,
    "p_payback": 0.0,
    "npv_p50_musd": -292.9
   },
   {
    "label": "B-S2",
    "case": "B",
    "scenario": "S2 Hanul-like (9 shutdowns 1996-2006)",
    "rate_events_per_site_yr": 0.8182,
    "p_payback": 0.019,
    "npv_p50_musd": -164.2
   },
   {
    "label": "B-S3",
    "case": "B",
    "scenario": "S3 Gravelines-like (3 events 2025-26)",
    "rate_events_per_site_yr": 1.5,
    "p_payback": 0.299,
    "npv_p50_musd": -48.2
   }
  ],
  "payback_rate_unit": "site jellyfish outage events per year (lambda); NPV at 6%, full build",
  "payback_curve": [
   [
    0.005,
    0.0
   ],
   [
    0.0062,
    0.0
   ],
   [
    0.0078,
    0.000333
   ],
   [
    0.0097,
    0.000667
   ],
   [
    0.0121,
    0.000333
   ],
   [
    0.0151,
    0.000333
   ],
   [
    0.0188,
    0.000333
   ],
   [
    0.0234,
    0.001
   ],
   [
    0.0292,
    0.001333
   ],
   [
    0.0364,
    0.000333
   ],
   [
    0.0454,
    0.001333
   ],
   [
    0.0566,
    0.002333
   ],
   [
    0.0706,
    0.004667
   ],
   [
    0.088,
    0.010333
   ],
   [
    0.1097,
    0.015
   ],
   [
    0.1368,
    0.024333
   ],
   [
    0.1705,
    0.043
   ],
   [
    0.2126,
    0.077667
   ],
   [
    0.2651,
    0.134
   ],
   [
    0.3305,
    0.211667
   ],
   [
    0.412,
    0.347667
   ],
   [
    0.5137,
    0.519667
   ],
   [
    0.6405,
    0.694667
   ],
   [
    0.7986,
    0.856
   ],
   [
    0.9957,
    0.953667
   ],
   [
    1.2414,
    0.99
   ],
   [
    1.5478,
    0.999333
   ],
   [
    1.9299,
    1.0
   ],
   [
    2.4062,
    1.0
   ],
   [
    3.0,
    1.0
   ]
  ],
  "payback_curve_caseB": [
   [
    0.005,
    0.0
   ],
   [
    0.0062,
    0.0
   ],
   [
    0.0078,
    0.0
   ],
   [
    0.0097,
    0.0
   ],
   [
    0.0121,
    0.0
   ],
   [
    0.0151,
    0.0
   ],
   [
    0.0188,
    0.0
   ],
   [
    0.0234,
    0.0
   ],
   [
    0.0292,
    0.0
   ],
   [
    0.0364,
    0.0
   ],
   [
    0.0454,
    0.0
   ],
   [
    0.0566,
    0.0
   ],
   [
    0.0706,
    0.0
   ],
   [
    0.088,
    0.0
   ],
   [
    0.1097,
    0.0
   ],
   [
    0.1368,
    0.0
   ],
   [
    0.1705,
    0.0
   ],
   [
    0.2126,
    0.0
   ],
   [
    0.2651,
    0.0
   ],
   [
    0.3305,
    0.0
   ],
   [
    0.412,
    0.0
   ],
   [
    0.5137,
    0.001333
   ],
   [
    0.6405,
    0.004333
   ],
   [
    0.7986,
    0.013
   ],
   [
    0.9957,
    0.049
   ],
   [
    1.2414,
    0.145333
   ],
   [
    1.5478,
    0.323333
   ],
   [
    1.9299,
    0.598667
   ],
   [
    2.4062,
    0.843667
   ],
   [
    3.0,
    0.97
   ]
  ],
  "payback_curve_note": "[lambda events/site-yr, P(payback)] for case A (and case B)",
  "frequency": {
   "sites": 51,
   "events": 41,
   "site_years": 2222,
   "pooled_rate_all": 0.0184,
   "site_posterior_mean": 0.0147,
   "site_posterior_p10_p50_p90": [
    0.0,
    0.003,
    0.044
   ],
   "P(lambda>0.1/yr)": 0.024,
   "severity_unit_days_mean": 7.67,
   "unit_day_GWh": 32.1
  },
  "expected_annual_loss_site_musd_no_jazr": {
   "S0 base (global Gamma-Poisson + the site 0 events/5.5 yr)": 0.22,
   "S1 jellyfish-prone site (pooled rate of sites with >=1 event)": 0.86,
   "S2 Hanul-like (9 shutdowns 1996-2006)": 12.49,
   "S3 Gravelines-like (3 events 2025-26)": 22.9
  },
  "co2": {
   "per_unit_rows_tco2_yr": {
    "JAZR operation (electricity, displaced gas), per unit": 158.2,
    "JAZR embodied (steel+HDPE+concrete+install)/30 yr, per unit": 208.8,
    "JAZR TOTAL per unit-yr": 367.0
   },
   "embodied_tco2_per_unit": 6265,
   "site_compare_tco2_yr": {
    "JAZR (4 lines, op+embodied)": 1468.2,
    "Status quo boats (diesel)": 205.8,
    "Bubble-curtain alternative 440 kW": 25.2
   },
   "avoided_tco2_per_unit_day_outage": 12964,
   "carbon_payback_years": {
    "S0": 47.9,
    "S1": 6.7,
    "S2": 0.4
   }
  },
  "rubric": {
   "v3_self_score": 85.0,
   "redteam_score_with_tank": 67.0,
   "redteam_score_no_tank": 59.5,
   "benchmark_estimate": 70.5
  },
  "real_option_A_S1_observed": {
   "E[NPV] full now": -73.0,
   "E[NPV] pilot only": -18.2,
   "E[NPV] pilot + option to expand": -19.9,
   "P(expand)": 0.045,
   "option value vs full now": 53.1,
   "option value vs pilot only": -1.6
  }
 },
 "crew_hours": {
  "source": "TESTS/04_biology_wildlife_ops/results/t6_ops_des.json; summary.json T6d_crew_hours",
  "jazr": 423.2,
  "today_low": 1096.6,
  "today_high": 3458.6,
  "units": "person-hours per bloom",
  "leakage_case": 0.13,
  "reduction_vs_low": 0.614083,
  "reduction_vs_high": 0.877636,
  "by_leakage": [
   {
    "leak": 0.055,
    "jazr": 372.6,
    "today_low": 1096.6,
    "today_high": 3458.6,
    "reduction_vs_low": 0.660237,
    "reduction_vs_high": 0.89227
   },
   {
    "leak": 0.13,
    "jazr": 423.2,
    "today_low": 1096.6,
    "today_high": 3458.6,
    "reduction_vs_low": 0.614083,
    "reduction_vs_high": 0.877636
   },
   {
    "leak": 0.28,
    "jazr": 676.3,
    "today_low": 1096.6,
    "today_high": 3458.6,
    "reduction_vs_low": 0.383314,
    "reduction_vs_high": 0.804465
   }
  ],
  "preseason_fixed_person_h_per_unit": 160,
  "verdict": "PASS",
  "note": "JAZR 423 person-h per bloom vs today 1097-3459 (reduction 61-88% at 13% leakage); still not zero: residual screen crew + repairs"
 },
 "survival_budget": {
  "source": "TESTS/10_mechanisms/survival_budget.csv",
  "rows": [
   {
    "stage": "1",
    "description": "Screen face (conveyor belt, smooth polymer mesh)",
    "target": 0.998,
    "lo": 0.99,
    "hi": 0.999,
    "basis": "ESTIMATE; no relative shear on belt; static mesh would be 0.97-0.995"
   },
   {
    "stage": "2",
    "description": "Entrance + flared transition (accel <=0.2 ft/s/ft)",
    "target": 0.999,
    "lo": 0.995,
    "hi": 1.0,
    "basis": "ESTIMATE; NMFS 8.6.2.8"
   },
   {
    "stage": "3",
    "description": "Dewatering (horizontal flat plate, >=0.3 m depth)",
    "target": 0.997,
    "lo": 0.985,
    "hi": 0.999,
    "basis": "ESTIMATE; USGS fish >98% 24 h (REPORTED)"
   },
   {
    "stage": "4",
    "description": "Turtle excluder (round bars 30-55 deg)",
    "target": 0.998,
    "lo": 0.99,
    "hi": 0.999,
    "basis": "ESTIMATE"
   },
   {
    "stage": "5",
    "description": "Lift: water-only HydroLift",
    "target": 0.998,
    "lo": 0.99,
    "hi": 0.999,
    "basis": "ESTIMATE; alternative screw x2 0.96 (0.85-0.99)"
   },
   {
    "stage": "6",
    "description": "Head tank + down-leg (no free fall, no air)",
    "target": 0.999,
    "lo": 0.995,
    "hi": 1.0,
    "basis": "ESTIMATE; NMFS 8.6.3.9-10"
   },
   {
    "stage": "7",
    "description": "Gravity pipe 10.5 km, 2.9 h, O2 held",
    "target": 0.995,
    "lo": 0.97,
    "hi": 0.998,
    "basis": "ESTIMATE; largest unknown; no gelatinous data"
   },
   {
    "stage": "8",
    "description": "Submerged diffuser outlet (<=1 m/s)",
    "target": 0.999,
    "lo": 0.995,
    "hi": 1.0,
    "basis": "ESTIMATE"
   },
   {
    "stage": "9",
    "description": "Post-release 24-96 h (delayed mortality)",
    "target": 0.995,
    "lo": 0.95,
    "hi": 0.998,
    "basis": "ESTIMATE; Hudson fish 90% -> 35% at 96 h is the cautionary case"
   },
   {
    "stage": "ALL",
    "description": "End-to-end (product), HydroLift chain",
    "target": 0.9782,
    "lo": 0.8676,
    "hi": 0.992,
    "basis": "CALC from the ESTIMATES above"
   },
   {
    "stage": "ALL-screw",
    "description": "End-to-end with two-stage screw instead of lock",
    "target": 0.941,
    "lo": 0.7449,
    "hi": 0.9831,
    "basis": "CALC"
   }
  ]
 },
 "bio_rules": {
  "source": "TESTS/09_biology_behaviour/biology_design_rules.csv",
  "rows": [
   {
    "rule_id": "R01",
    "goal": "both",
    "rule": "No air contact and no free bubbles anywhere in the animal path (submerged inlets/outlets; pipe runs full-bore; screw buckets never drain above water; no free-fall drops; no hydraulic jumps; no spray on animals)",
    "quantity": "free gas in animal water",
    "threshold": "ZERO free bubbles; any air exposure triggers a bell inspection",
    "evidence_type": "aquarium practice (expert manual)",
    "confidence": "HIGH (qualitative); threshold for harm UNKNOWN",
    "tank_test": "T09-style: camera count of bells with trapped gas after each stage"
   },
   {
    "rule_id": "R02",
    "goal": "survival",
    "rule": "Dissolved gas never supersaturated; O2 added only as fully dissolved O2 (side-stream saturator or downflow contactor) with no free bubbles reaching animals",
    "quantity": "DO and total dissolved gas (TDG)",
    "threshold": "DO 75-99 % air saturation; TDG <=100 % at the lowest-pressure point of the path (incl. outlet depth)",
    "evidence_type": "aquarium practice",
    "confidence": "HIGH that it matters; exact TDG limit for medusae UNKNOWN",
    "tank_test": "DO/TDG probes at head tank, mid-pipe, outlet; inspect bells"
   },
   {
    "rule_id": "R03",
    "goal": "survival",
    "rule": "Keep DO above floor through the whole 3 h transit",
    "quantity": "DO at outlet",
    "threshold": ">=75 % sat (~4.2 mg/L at 34 C, 42 ppt); absolute floor >=2.6 mg/L for fish bycatch",
    "evidence_type": "lab physiology + meta-analysis",
    "confidence": "MEDIUM",
    "tank_test": "Respirometry of Gulf Catostylus at 30-34 C (active and handled)"
   },
   {
    "rule_id": "R04",
    "goal": "survival",
    "rule": "Cap jellyfish biomass loading in the pipe or inject dissolved O2",
    "quantity": "wet biomass per m3 of pipe water over 3 h",
    "threshold": "<=6.6 kg/m3 (e.g. 20 animals/m3 at 0.33 kg) without O2 injection under the conservative respiration rate; above this, inject O2 per R02",
    "evidence_type": "derived from published rates",
    "confidence": "MEDIUM (rates are from other rhizostomes; regression CV 72 %)",
    "tank_test": "Closed-pipe-loop DO decline test with live animals at design density"
   },
   {
    "rule_id": "R05",
    "goal": "survival",
    "rule": "Map intake density to pipe density before sizing O2",
    "quantity": "pipe animals/m3",
    "threshold": "pipe density ~= 86 x eta x intake density for one 172.5 m3/s unit into a 2.0 m3/s pipe (0.1/m3 -> 7.7; 0.3 -> 23; 1 -> 77 /m3 at eta 0.9)",
    "evidence_type": "derived",
    "confidence": "MEDIUM",
    "tank_test": "n/a (arithmetic)"
   },
   {
    "rule_id": "R06",
    "goal": "survival",
    "rule": "Maximum transit time",
    "quantity": "hours in conveyance",
    "threshold": "<=3 h design is within aquarium shipping practice (1 h to >24 h) ONLY if R01-R04 and R08 hold; no published survival vs time for rhizostomes",
    "evidence_type": "aquarium practice",
    "confidence": "LOW-MEDIUM (survival curve UNKNOWN)",
    "tank_test": "24-96 h post-transit survival vs 1/3/6 h simulated transit"
   },
   {
    "rule_id": "R07",
    "goal": "survival",
    "rule": "No mechanical contact: no nets, no hands, no mesh lifting; transfer water-to-water",
    "quantity": "contact events per animal",
    "threshold": "ZERO intended contacts; excluder/wedge-wire contacts brief and sliding only",
    "evidence_type": "aquarium practice",
    "confidence": "HIGH (qualitative); force/abrasion threshold UNKNOWN",
    "tank_test": "T05/T14 bell-mesh friction; video scoring of damage"
   },
   {
    "rule_id": "R08",
    "goal": "survival",
    "rule": "Temperature: no heating above intake ambient; shade head tank; never route through thermal outfall water",
    "quantity": "delta T and absolute T",
    "threshold": "Target dT <=1 C (design inference); AZA: <5 C change per 24 h tolerated; avoid >35 C (top of UAE Catostylus occurrence 20-35 C); Cassiopea medusae lethal >34 C (C. andromeda) and 40 C (C. xamachana)",
    "evidence_type": "field occurrence + lab on other rhizostomes",
    "confidence": "MEDIUM; Catostylus CTmax UNKNOWN",
    "tank_test": "CTmax / pulsation curve 28-38 C for Gulf animals"
   },
   {
    "rule_id": "R09",
    "goal": "survival",
    "rule": "Salinity: same seawater end to end; seawater-only screen wash (no fresh water); release outside brine and freshwater plumes",
    "quantity": "delta S",
    "threshold": "Design target |dS| <= 1-2 ppt (INFERENCE; no tolerance data); medusae are osmoconformers whose buoyancy shifts with salinity; C. mosaicus vanished after every major freshwater flow (16 events in 20 y)",
    "evidence_type": "field + aquarium",
    "confidence": "MEDIUM qualitative; threshold UNKNOWN",
    "tank_test": "Salinity step test 42 -> 38/46 ppt; buoyancy and pulsation"
   },
   {
    "rule_id": "R10",
    "goal": "both",
    "rule": "Velocities: keep sweep and entrance velocities well above swimming speed and accelerating monotonically into the entrance",
    "quantity": "velocity ratio and acceleration",
    "threshold": "Entrance/sweep >= 3x max sustained swim speed of the size class (~4-9 cm/s for 6.5-20 cm bells; up to 15 cm/s large Stomolophus) i.e. >=0.3-0.45 m/s (INFERENCE); no deceleration zones; acceleration <= fish-screen bypass…",
    "evidence_type": "lab swim data + fish-screen analogue",
    "confidence": "MEDIUM (ratio is a design inference)",
    "tank_test": "Flume: % of live animals that hold station vs entrance velocity"
   },
   {
    "rule_id": "R11",
    "goal": "both",
    "rule": "No low-velocity eddies or shear layers where animals can hold station (dead zones behind baffles; entrance lips)",
    "quantity": "local velocity and shear",
    "threshold": "Avoid zones with velocity < swim speed; avoid persistent shear layers ~0.1-0.34 s-1 where medusae actively hold position",
    "evidence_type": "lab + field (Aurelia)",
    "confidence": "MEDIUM",
    "tank_test": "CFD + live-animal residence-time map in the tank"
   },
   {
    "rule_id": "R12",
    "goal": "survival",
    "rule": "Fluid shear / strain in screws pipe and fittings",
    "quantity": "strain rate",
    "threshold": "UNKNOWN for medusae; use larval/juvenile fish analogue <400-600 s-1 and injury rise >495 s-1 as a provisional ceiling",
    "evidence_type": "fish analogue only",
    "confidence": "LOW",
    "tank_test": "Shear-jet exposure of bells; score damage/pulsation 0-96 h"
   },
   {
    "rule_id": "R13",
    "goal": "both",
    "rule": "Noise: keep machinery noise at the bell well below levels that damaged rhizostome statocysts; no acoustic deterrents",
    "quantity": "received sound level 50-400 Hz",
    "threshold": "Damage observed at RL 157 +/-5 dB re 1 uPa (peaks 175) for 2 h in Rhizostoma pulmo and Cotylorhiza; no-effect level UNKNOWN; measure and keep far below",
    "evidence_type": "lab (SEM histology)",
    "confidence": "MEDIUM for harm; threshold UNKNOWN",
    "tank_test": "Hydrophone survey of screw/pipe; statocyst histology if needed"
   },
   {
    "rule_id": "R14",
    "goal": "both",
    "rule": "No electric or magnetic fields as guidance",
    "quantity": "field strength",
    "threshold": "Do not use (no scyphozoan behavioural evidence; harm to turtles/fish unassessed)",
    "evidence_type": "absence of evidence",
    "confidence": "MEDIUM (decision)",
    "tank_test": "none"
   },
   {
    "rule_id": "R15",
    "goal": "both",
    "rule": "Lighting: no artificial light at screens/entrances by default",
    "quantity": "light at night",
    "threshold": "Default dark at night; any light guidance only after a tank test. C. mosaicus is non-zooxanthellate so no sun-tracking expected; Aurelia pulse rate rises with light (Horstmann 1934)",
    "evidence_type": "lab (other species)",
    "confidence": "LOW",
    "tank_test": "Light-choice tank (dark vs dim LED; red vs white)"
   },
   {
    "rule_id": "R16",
    "goal": "both",
    "rule": "Handle the size range: oversize bells must not pin on the 15 cm excluder grid",
    "quantity": "bell diameter vs bar gap",
    "threshold": "Oct-Nov mean bells 6.5-11.8 cm pass; tail to 1.7 kg / 40 cm total length will not: grid must be self-clearing to the open escape chute (alive)",
    "evidence_type": "field size data",
    "confidence": "HIGH (geometry)",
    "tank_test": "Tank: large bell on excluder at design velocity"
   },
   {
    "rule_id": "R17",
    "goal": "survival",
    "rule": "Release conditions",
    "quantity": "outlet",
    "threshold": "Release at ambient T and S; gentle submerged outlet (no free fall, no jet impact); over soft sediment, away from breakwaters, marinas, reefs, thermal and brine plumes; release in darkness or matched light to avoid dark-…",
    "evidence_type": "aquarium + polyp ecology",
    "confidence": "MEDIUM",
    "tank_test": "Post-release pulsation and drift tracking (pilot P02)"
   },
   {
    "rule_id": "R18",
    "goal": "both",
    "rule": "Stress spawning: assume gametes/planulae will be released in the system",
    "quantity": "planulae export",
    "threshold": "Treat the whole wetted path as a planula source; no shaded hard overhangs in the path; flush; outlet over soft sediment",
    "evidence_type": "aquarium practice + fecundity evidence",
    "confidence": "MEDIUM",
    "tank_test": "Plankton net at outlet during tank/pilot runs"
   },
   {
    "rule_id": "R19",
    "goal": "ecology",
    "rule": "Do not create polyp habitat on fixed submerged structures",
    "quantity": "overhanging shaded hard area",
    "threshold": "Minimise overhangs/undersides; keep cassettes stored raised and dry; non-biocidal fouling-release surfaces; inspect for polyps each spring; prefer vertical, lit surfaces",
    "evidence_type": "field case + experiments",
    "confidence": "MEDIUM",
    "tank_test": "Settlement plates on JAZR materials at the site (6-12 months)"
   },
   {
    "rule_id": "R20",
    "goal": "survival",
    "rule": "Post-handling survival must be measured not assumed",
    "quantity": "survival at 96 h",
    "threshold": "UNKNOWN (no published survival for any scyphomedusa after pumping/lifting/piping); report initial AND 96 h delayed survival",
    "evidence_type": "evidence gap",
    "confidence": "HIGH that it is unknown",
    "tank_test": "T09 + pilot P02 with pulsation-rate recovery score"
   }
  ]
 },
 "o2_budget": {
  "source": "TESTS/09_biology_behaviour/o2_budget.csv",
  "note": "DO drop over 3 h transit; DO_sat 34 C / 42 ppt; end values if start at 100% sat",
  "rows": [
   {
    "mass_case": "mean 0.33 kg (Hashemi 2025, n=503)",
    "resp_case": "SRR low (C=0.34%WW)",
    "density": 1.0,
    "drop": 0.02,
    "end_mg_L": 5.64,
    "end_pct": 99.7,
    "mgO2_per_h_per_animal": 5.5
   },
   {
    "mass_case": "mean 0.33 kg (Hashemi 2025, n=503)",
    "resp_case": "SRR low (C=0.34%WW)",
    "density": 5.0,
    "drop": 0.08,
    "end_mg_L": 5.57,
    "end_pct": 98.5,
    "mgO2_per_h_per_animal": 5.5
   },
   {
    "mass_case": "mean 0.33 kg (Hashemi 2025, n=503)",
    "resp_case": "SRR low (C=0.34%WW)",
    "density": 10.0,
    "drop": 0.16,
    "end_mg_L": 5.49,
    "end_pct": 97.1,
    "mgO2_per_h_per_animal": 5.5
   },
   {
    "mass_case": "mean 0.33 kg (Hashemi 2025, n=503)",
    "resp_case": "SRR low (C=0.34%WW)",
    "density": 20.0,
    "drop": 0.33,
    "end_mg_L": 5.33,
    "end_pct": 94.2,
    "mgO2_per_h_per_animal": 5.5
   },
   {
    "mass_case": "mean 0.33 kg (Hashemi 2025, n=503)",
    "resp_case": "SRR low (C=0.34%WW)",
    "density": 50.0,
    "drop": 0.82,
    "end_mg_L": 4.83,
    "end_pct": 85.4,
    "mgO2_per_h_per_animal": 5.5
   },
   {
    "mass_case": "mean 0.33 kg (Hashemi 2025, n=503)",
    "resp_case": "SRR low (C=0.34%WW)",
    "density": 100.0,
    "drop": 1.65,
    "end_mg_L": 4.01,
    "end_pct": 70.8,
    "mgO2_per_h_per_animal": 5.5
   },
   {
    "mass_case": "mean 0.33 kg (Hashemi 2025, n=503)",
    "resp_case": "SRR high (C=0.60%WW)",
    "density": 1.0,
    "drop": 0.03,
    "end_mg_L": 5.63,
    "end_pct": 99.5,
    "mgO2_per_h_per_animal": 9.37
   },
   {
    "mass_case": "mean 0.33 kg (Hashemi 2025, n=503)",
    "resp_case": "SRR high (C=0.60%WW)",
    "density": 5.0,
    "drop": 0.14,
    "end_mg_L": 5.51,
    "end_pct": 97.5,
    "mgO2_per_h_per_animal": 9.37
   },
   {
    "mass_case": "mean 0.33 kg (Hashemi 2025, n=503)",
    "resp_case": "SRR high (C=0.60%WW)",
    "density": 10.0,
    "drop": 0.28,
    "end_mg_L": 5.37,
    "end_pct": 95.0,
    "mgO2_per_h_per_animal": 9.37
   },
   {
    "mass_case": "mean 0.33 kg (Hashemi 2025, n=503)",
    "resp_case": "SRR high (C=0.60%WW)",
    "density": 20.0,
    "drop": 0.56,
    "end_mg_L": 5.09,
    "end_pct": 90.1,
    "mgO2_per_h_per_animal": 9.37
   },
   {
    "mass_case": "mean 0.33 kg (Hashemi 2025, n=503)",
    "resp_case": "SRR high (C=0.60%WW)",
    "density": 50.0,
    "drop": 1.41,
    "end_mg_L": 4.25,
    "end_pct": 75.1,
    "mgO2_per_h_per_animal": 9.37
   },
   {
    "mass_case": "mean 0.33 kg (Hashemi 2025, n=503)",
    "resp_case": "SRR high (C=0.60%WW)",
    "density": 100.0,
    "drop": 2.81,
    "end_mg_L": 2.84,
    "end_pct": 50.3,
    "mgO2_per_h_per_animal": 9.37
   },
   {
    "mass_case": "mean 0.33 kg (Hashemi 2025, n=503)",
    "resp_case": "Stomolophus active (Larson 1987)",
    "density": 1.0,
    "drop": 0.07,
    "end_mg_L": 5.58,
    "end_pct": 98.8,
    "mgO2_per_h_per_animal": 23.43
   },
   {
    "mass_case": "mean 0.33 kg (Hashemi 2025, n=503)",
    "resp_case": "Stomolophus active (Larson 1987)",
    "density": 5.0,
    "drop": 0.35,
    "end_mg_L": 5.3,
    "end_pct": 93.8,
    "mgO2_per_h_per_animal": 23.43
   },
   {
    "mass_case": "mean 0.33 kg (Hashemi 2025, n=503)",
    "resp_case": "Stomolophus active (Larson 1987)",
    "density": 10.0,
    "drop": 0.7,
    "end_mg_L": 4.95,
    "end_pct": 87.6,
    "mgO2_per_h_per_animal": 23.43
   },
   {
    "mass_case": "mean 0.33 kg (Hashemi 2025, n=503)",
    "resp_case": "Stomolophus active (Larson 1987)",
    "density": 20.0,
    "drop": 1.41,
    "end_mg_L": 4.25,
    "end_pct": 75.1,
    "mgO2_per_h_per_animal": 23.43
   },
   {
    "mass_case": "mean 0.33 kg (Hashemi 2025, n=503)",
    "resp_case": "Stomolophus active (Larson 1987)",
    "density": 50.0,
    "drop": 3.51,
    "end_mg_L": 2.14,
    "end_pct": 37.9,
    "mgO2_per_h_per_animal": 23.43
   },
   {
    "mass_case": "mean 0.33 kg (Hashemi 2025, n=503)",
    "resp_case": "Stomolophus active (Larson 1987)",
    "density": 100.0,
    "drop": 7.03,
    "end_mg_L": -1.37,
    "end_pct": -24.3,
    "mgO2_per_h_per_animal": 23.43
   },
   {
    "mass_case": "mean 0.33 kg (Hashemi 2025, n=503)",
    "resp_case": "Stomolophus active x2 (handling-stress margin, ASSUMED)",
    "density": 1.0,
    "drop": 0.14,
    "end_mg_L": 5.51,
    "end_pct": 97.5,
    "mgO2_per_h_per_animal": 46.86
   },
   {
    "mass_case": "mean 0.33 kg (Hashemi 2025, n=503)",
    "resp_case": "Stomolophus active x2 (handling-stress margin, ASSUMED)",
    "density": 5.0,
    "drop": 0.7,
    "end_mg_L": 4.95,
    "end_pct": 87.6,
    "mgO2_per_h_per_animal": 46.86
   },
   {
    "mass_case": "mean 0.33 kg (Hashemi 2025, n=503)",
    "resp_case": "Stomolophus active x2 (handling-stress margin, ASSUMED)",
    "density": 10.0,
    "drop": 1.41,
    "end_mg_L": 4.25,
    "end_pct": 75.1,
    "mgO2_per_h_per_animal": 46.86
   },
   {
    "mass_case": "mean 0.33 kg (Hashemi 2025, n=503)",
    "resp_case": "Stomolophus active x2 (handling-stress margin, ASSUMED)",
    "density": 20.0,
    "drop": 2.81,
    "end_mg_L": 2.84,
    "end_pct": 50.3,
    "mgO2_per_h_per_animal": 46.86
   },
   {
    "mass_case": "mean 0.33 kg (Hashemi 2025, n=503)",
    "resp_case": "Stomolophus active x2 (handling-stress margin, ASSUMED)",
    "density": 50.0,
    "drop": 7.03,
    "end_mg_L": -1.37,
    "end_pct": -24.3,
    "mgO2_per_h_per_animal": 46.86
   },
   {
    "mass_case": "mean 0.33 kg (Hashemi 2025, n=503)",
    "resp_case": "Stomolophus active x2 (handling-stress margin, ASSUMED)",
    "density": 100.0,
    "drop": 14.06,
    "end_mg_L": -8.4,
    "end_pct": -148.6,
    "mgO2_per_h_per_animal": 46.86
   },
   {
    "mass_case": "Nov UAE bell 11.8 cm ~0.13 kg (00_data)",
    "resp_case": "SRR low (C=0.34%WW)",
    "density": 1.0,
    "drop": 0.01,
    "end_mg_L": 5.65,
    "end_pct": 99.9,
    "mgO2_per_h_per_animal": 2.29
   },
   {
    "mass_case": "Nov UAE bell 11.8 cm ~0.13 kg (00_data)",
    "resp_case": "SRR low (C=0.34%WW)",
    "density": 5.0,
    "drop": 0.03,
    "end_mg_L": 5.62,
    "end_pct": 99.4,
    "mgO2_per_h_per_animal": 2.29
   },
   {
    "mass_case": "Nov UAE bell 11.8 cm ~0.13 kg (00_data)",
    "resp_case": "SRR low (C=0.34%WW)",
    "density": 10.0,
    "drop": 0.07,
    "end_mg_L": 5.59,
    "end_pct": 98.8,
    "mgO2_per_h_per_animal": 2.29
   },
   {
    "mass_case": "Nov UAE bell 11.8 cm ~0.13 kg (00_data)",
    "resp_case": "SRR low (C=0.34%WW)",
    "density": 20.0,
    "drop": 0.14,
    "end_mg_L": 5.52,
    "end_pct": 97.6,
    "mgO2_per_h_per_animal": 2.29
   },
   {
    "mass_case": "Nov UAE bell 11.8 cm ~0.13 kg (00_data)",
    "resp_case": "SRR low (C=0.34%WW)",
    "density": 50.0,
    "drop": 0.34,
    "end_mg_L": 5.31,
    "end_pct": 93.9,
    "mgO2_per_h_per_animal": 2.29
   },
   {
    "mass_case": "Nov UAE bell 11.8 cm ~0.13 kg (00_data)",
    "resp_case": "SRR low (C=0.34%WW)",
    "density": 100.0,
    "drop": 0.69,
    "end_mg_L": 4.97,
    "end_pct": 87.9,
    "mgO2_per_h_per_animal": 2.29
   },
   {
    "mass_case": "Nov UAE bell 11.8 cm ~0.13 kg (00_data)",
    "resp_case": "SRR high (C=0.60%WW)",
    "density": 1.0,
    "drop": 0.01,
    "end_mg_L": 5.64,
    "end_pct": 99.8,
    "mgO2_per_h_per_animal": 3.91
   },
   {
    "mass_case": "Nov UAE bell 11.8 cm ~0.13 kg (00_data)",
    "resp_case": "SRR high (C=0.60%WW)",
    "density": 5.0,
    "drop": 0.06,
    "end_mg_L": 5.6,
    "end_pct": 99.0,
    "mgO2_per_h_per_animal": 3.91
   },
   {
    "mass_case": "Nov UAE bell 11.8 cm ~0.13 kg (00_data)",
    "resp_case": "SRR high (C=0.60%WW)",
    "density": 10.0,
    "drop": 0.12,
    "end_mg_L": 5.54,
    "end_pct": 97.9,
    "mgO2_per_h_per_animal": 3.91
   },
   {
    "mass_case": "Nov UAE bell 11.8 cm ~0.13 kg (00_data)",
    "resp_case": "SRR high (C=0.60%WW)",
    "density": 20.0,
    "drop": 0.23,
    "end_mg_L": 5.42,
    "end_pct": 95.9,
    "mgO2_per_h_per_animal": 3.91
   },
   {
    "mass_case": "Nov UAE bell 11.8 cm ~0.13 kg (00_data)",
    "resp_case": "SRR high (C=0.60%WW)",
    "density": 50.0,
    "drop": 0.59,
    "end_mg_L": 5.07,
    "end_pct": 89.6,
    "mgO2_per_h_per_animal": 3.91
   },
   {
    "mass_case": "Nov UAE bell 11.8 cm ~0.13 kg (00_data)",
    "resp_case": "SRR high (C=0.60%WW)",
    "density": 100.0,
    "drop": 1.17,
    "end_mg_L": 4.48,
    "end_pct": 79.3,
    "mgO2_per_h_per_animal": 3.91
   },
   {
    "mass_case": "Nov UAE bell 11.8 cm ~0.13 kg (00_data)",
    "resp_case": "Stomolophus active (Larson 1987)",
    "density": 1.0,
    "drop": 0.03,
    "end_mg_L": 5.63,
    "end_pct": 99.5,
    "mgO2_per_h_per_animal": 9.23
   },
   {
    "mass_case": "Nov UAE bell 11.8 cm ~0.13 kg (00_data)",
    "resp_case": "Stomolophus active (Larson 1987)",
    "density": 5.0,
    "drop": 0.14,
    "end_mg_L": 5.52,
    "end_pct": 97.6,
    "mgO2_per_h_per_animal": 9.23
   },
   {
    "mass_case": "Nov UAE bell 11.8 cm ~0.13 kg (00_data)",
    "resp_case": "Stomolophus active (Larson 1987)",
    "density": 10.0,
    "drop": 0.28,
    "end_mg_L": 5.38,
    "end_pct": 95.1,
    "mgO2_per_h_per_animal": 9.23
   },
   {
    "mass_case": "Nov UAE bell 11.8 cm ~0.13 kg (00_data)",
    "resp_case": "Stomolophus active (Larson 1987)",
    "density": 20.0,
    "drop": 0.55,
    "end_mg_L": 5.1,
    "end_pct": 90.2,
    "mgO2_per_h_per_animal": 9.23
   },
   {
    "mass_case": "Nov UAE bell 11.8 cm ~0.13 kg (00_data)",
    "resp_case": "Stomolophus active (Larson 1987)",
    "density": 50.0,
    "drop": 1.38,
    "end_mg_L": 4.27,
    "end_pct": 75.5,
    "mgO2_per_h_per_animal": 9.23
   },
   {
    "mass_case": "Nov UAE bell 11.8 cm ~0.13 kg (00_data)",
    "resp_case": "Stomolophus active (Larson 1987)",
    "density": 100.0,
    "drop": 2.77,
    "end_mg_L": 2.89,
    "end_pct": 51.0,
    "mgO2_per_h_per_animal": 9.23
   },
   {
    "mass_case": "Nov UAE bell 11.8 cm ~0.13 kg (00_data)",
    "resp_case": "Stomolophus active x2 (handling-stress margin, ASSUMED)",
    "density": 1.0,
    "drop": 0.06,
    "end_mg_L": 5.6,
    "end_pct": 99.0,
    "mgO2_per_h_per_animal": 18.46
   },
   {
    "mass_case": "Nov UAE bell 11.8 cm ~0.13 kg (00_data)",
    "resp_case": "Stomolophus active x2 (handling-stress margin, ASSUMED)",
    "density": 5.0,
    "drop": 0.28,
    "end_mg_L": 5.38,
    "end_pct": 95.1,
    "mgO2_per_h_per_animal": 18.46
   },
   {
    "mass_case": "Nov UAE bell 11.8 cm ~0.13 kg (00_data)",
    "resp_case": "Stomolophus active x2 (handling-stress margin, ASSUMED)",
    "density": 10.0,
    "drop": 0.55,
    "end_mg_L": 5.1,
    "end_pct": 90.2,
    "mgO2_per_h_per_animal": 18.46
   },
   {
    "mass_case": "Nov UAE bell 11.8 cm ~0.13 kg (00_data)",
    "resp_case": "Stomolophus active x2 (handling-stress margin, ASSUMED)",
    "density": 20.0,
    "drop": 1.11,
    "end_mg_L": 4.55,
    "end_pct": 80.4,
    "mgO2_per_h_per_animal": 18.46
   },
   {
    "mass_case": "Nov UAE bell 11.8 cm ~0.13 kg (00_data)",
    "resp_case": "Stomolophus active x2 (handling-stress margin, ASSUMED)",
    "density": 50.0,
    "drop": 2.77,
    "end_mg_L": 2.89,
    "end_pct": 51.0,
    "mgO2_per_h_per_animal": 18.46
   },
   {
    "mass_case": "Nov UAE bell 11.8 cm ~0.13 kg (00_data)",
    "resp_case": "Stomolophus active x2 (handling-stress margin, ASSUMED)",
    "density": 100.0,
    "drop": 5.54,
    "end_mg_L": 0.12,
    "end_pct": 2.1,
    "mgO2_per_h_per_animal": 18.46
   },
   {
    "mass_case": "max 1.7 kg (Hashemi 2025)",
    "resp_case": "SRR low (C=0.34%WW)",
    "density": 1.0,
    "drop": 0.08,
    "end_mg_L": 5.58,
    "end_pct": 98.6,
    "mgO2_per_h_per_animal": 25.66
   },
   {
    "mass_case": "max 1.7 kg (Hashemi 2025)",
    "resp_case": "SRR low (C=0.34%WW)",
    "density": 5.0,
    "drop": 0.38,
    "end_mg_L": 5.27,
    "end_pct": 93.2,
    "mgO2_per_h_per_animal": 25.66
   },
   {
    "mass_case": "max 1.7 kg (Hashemi 2025)",
    "resp_case": "SRR low (C=0.34%WW)",
    "density": 10.0,
    "drop": 0.77,
    "end_mg_L": 4.89,
    "end_pct": 86.4,
    "mgO2_per_h_per_animal": 25.66
   },
   {
    "mass_case": "max 1.7 kg (Hashemi 2025)",
    "resp_case": "SRR low (C=0.34%WW)",
    "density": 20.0,
    "drop": 1.54,
    "end_mg_L": 4.12,
    "end_pct": 72.8,
    "mgO2_per_h_per_animal": 25.66
   },
   {
    "mass_case": "max 1.7 kg (Hashemi 2025)",
    "resp_case": "SRR low (C=0.34%WW)",
    "density": 50.0,
    "drop": 3.85,
    "end_mg_L": 1.81,
    "end_pct": 31.9,
    "mgO2_per_h_per_animal": 25.66
   },
   {
    "mass_case": "max 1.7 kg (Hashemi 2025)",
    "resp_case": "SRR low (C=0.34%WW)",
    "density": 100.0,
    "drop": 7.7,
    "end_mg_L": -2.04,
    "end_pct": -36.1,
    "mgO2_per_h_per_animal": 25.66
   },
   {
    "mass_case": "max 1.7 kg (Hashemi 2025)",
    "resp_case": "SRR high (C=0.60%WW)",
    "density": 1.0,
    "drop": 0.13,
    "end_mg_L": 5.52,
    "end_pct": 97.7,
    "mgO2_per_h_per_animal": 43.77
   },
   {
    "mass_case": "max 1.7 kg (Hashemi 2025)",
    "resp_case": "SRR high (C=0.60%WW)",
    "density": 5.0,
    "drop": 0.66,
    "end_mg_L": 5.0,
    "end_pct": 88.4,
    "mgO2_per_h_per_animal": 43.77
   },
   {
    "mass_case": "max 1.7 kg (Hashemi 2025)",
    "resp_case": "SRR high (C=0.60%WW)",
    "density": 10.0,
    "drop": 1.31,
    "end_mg_L": 4.34,
    "end_pct": 76.8,
    "mgO2_per_h_per_animal": 43.77
   },
   {
    "mass_case": "max 1.7 kg (Hashemi 2025)",
    "resp_case": "SRR high (C=0.60%WW)",
    "density": 20.0,
    "drop": 2.63,
    "end_mg_L": 3.03,
    "end_pct": 53.6,
    "mgO2_per_h_per_animal": 43.77
   },
   {
    "mass_case": "max 1.7 kg (Hashemi 2025)",
    "resp_case": "SRR high (C=0.60%WW)",
    "density": 50.0,
    "drop": 6.57,
    "end_mg_L": -0.91,
    "end_pct": -16.1,
    "mgO2_per_h_per_animal": 43.77
   },
   {
    "mass_case": "max 1.7 kg (Hashemi 2025)",
    "resp_case": "SRR high (C=0.60%WW)",
    "density": 100.0,
    "drop": 13.13,
    "end_mg_L": -7.48,
    "end_pct": -132.2,
    "mgO2_per_h_per_animal": 43.77
   },
   {
    "mass_case": "max 1.7 kg (Hashemi 2025)",
    "resp_case": "Stomolophus active (Larson 1987)",
    "density": 1.0,
    "drop": 0.36,
    "end_mg_L": 5.29,
    "end_pct": 93.6,
    "mgO2_per_h_per_animal": 120.7
   },
   {
    "mass_case": "max 1.7 kg (Hashemi 2025)",
    "resp_case": "Stomolophus active (Larson 1987)",
    "density": 5.0,
    "drop": 1.81,
    "end_mg_L": 3.84,
    "end_pct": 68.0,
    "mgO2_per_h_per_animal": 120.7
   },
   {
    "mass_case": "max 1.7 kg (Hashemi 2025)",
    "resp_case": "Stomolophus active (Larson 1987)",
    "density": 10.0,
    "drop": 3.62,
    "end_mg_L": 2.03,
    "end_pct": 36.0,
    "mgO2_per_h_per_animal": 120.7
   },
   {
    "mass_case": "max 1.7 kg (Hashemi 2025)",
    "resp_case": "Stomolophus active (Larson 1987)",
    "density": 20.0,
    "drop": 7.24,
    "end_mg_L": -1.59,
    "end_pct": -28.1,
    "mgO2_per_h_per_animal": 120.7
   },
   {
    "mass_case": "max 1.7 kg (Hashemi 2025)",
    "resp_case": "Stomolophus active (Larson 1987)",
    "density": 50.0,
    "drop": 18.1,
    "end_mg_L": -12.45,
    "end_pct": -220.1,
    "mgO2_per_h_per_animal": 120.7
   },
   {
    "mass_case": "max 1.7 kg (Hashemi 2025)",
    "resp_case": "Stomolophus active (Larson 1987)",
    "density": 100.0,
    "drop": 36.21,
    "end_mg_L": -30.55,
    "end_pct": -540.3,
    "mgO2_per_h_per_animal": 120.7
   },
   {
    "mass_case": "max 1.7 kg (Hashemi 2025)",
    "resp_case": "Stomolophus active x2 (handling-stress margin, ASSUMED)",
    "density": 1.0,
    "drop": 0.72,
    "end_mg_L": 4.93,
    "end_pct": 87.2,
    "mgO2_per_h_per_animal": 241.4
   },
   {
    "mass_case": "max 1.7 kg (Hashemi 2025)",
    "resp_case": "Stomolophus active x2 (handling-stress margin, ASSUMED)",
    "density": 5.0,
    "drop": 3.62,
    "end_mg_L": 2.03,
    "end_pct": 36.0,
    "mgO2_per_h_per_animal": 241.4
   },
   {
    "mass_case": "max 1.7 kg (Hashemi 2025)",
    "resp_case": "Stomolophus active x2 (handling-stress margin, ASSUMED)",
    "density": 10.0,
    "drop": 7.24,
    "end_mg_L": -1.59,
    "end_pct": -28.1,
    "mgO2_per_h_per_animal": 241.4
   },
   {
    "mass_case": "max 1.7 kg (Hashemi 2025)",
    "resp_case": "Stomolophus active x2 (handling-stress margin, ASSUMED)",
    "density": 20.0,
    "drop": 14.48,
    "end_mg_L": -8.83,
    "end_pct": -156.1,
    "mgO2_per_h_per_animal": 241.4
   },
   {
    "mass_case": "max 1.7 kg (Hashemi 2025)",
    "resp_case": "Stomolophus active x2 (handling-stress margin, ASSUMED)",
    "density": 50.0,
    "drop": 36.21,
    "end_mg_L": -30.55,
    "end_pct": -540.3,
    "mgO2_per_h_per_animal": 241.4
   },
   {
    "mass_case": "max 1.7 kg (Hashemi 2025)",
    "resp_case": "Stomolophus active x2 (handling-stress margin, ASSUMED)",
    "density": 100.0,
    "drop": 72.42,
    "end_mg_L": -66.76,
    "end_pct": -1180.6,
    "mgO2_per_h_per_animal": 241.4
   }
  ]
 },
 "virtual_tank": {
  "source": "TESTS/07_virtual_tank/results/sim_results.json; result text from TESTS/07_virtual_tank/README.md",
  "label": "SIMULATED virtual tank - not physical evidence",
  "rows": [
   {
    "test": "T01",
    "name": "surrogates",
    "metric": "hover fraction (mean)",
    "value": 0.2,
    "verdict": "FAIL (nominal) / SENSITIVE",
    "criterion": ">=80% hover",
    "result": "20% hover (13–23%). Hovering means \\|settling velocity\\| ≤ 5 mm/s, which requires density control to σ ≈ 0.03 kg/m³ (30 ppm). Kitchen-scale scatter (air bubbles, gel %) is about 0.2 kg/m³"
   },
   {
    "test": "T02",
    "name": "baseline",
    "metric": "intake fraction, no screen, bypass off",
    "value": 0.957778,
    "verdict": "REFERENCE (no criterion)",
    "criterion": "eta_r >= 0.7 at 11 deg; kill if <0.4 at every angle",
    "result": "Bypass off: 95.8% reached the intake (93–100%), 4% lost in corners. Bypass on as a control: 17% entered the bypass by chance, 78% reached the intake"
   },
   {
    "test": "T03",
    "name": "guidance η_r",
    "metric": "eta_r at 11 deg (protocol mean)",
    "value": 0.5,
    "verdict": "FAIL",
    "criterion": "eta_r >= 0.7 at 11 deg; kill if <0.4 at every angle",
    "result": "8° 0.47 · 11° 0.50 · 15° 0.56 · 20° 0.69 (3 protocol runs; 15-seed means 0.50 / 0.51 / 0.57 / 0.62). 0% reached the intake in every screen run. The loss is bells jammed at the face and the bypass mouth (~40%)"
   },
   {
    "test": "T04",
    "name": "entrance spacing",
    "metric": "eta_r with 4 entrances (15-seed mean)",
    "value": 0.713333,
    "verdict": "PASS",
    "criterion": "more entrances -> fewer stuck",
    "result": "2 → 4 entrances: η_r 0.51 → 0.71, stuck bells 12.5 → 8.5 per 30"
   },
   {
    "test": "T05",
    "name": "clogging",
    "metric": "design rate, bells/min",
    "value": 37.209792,
    "verdict": "FAIL",
    "criterion": "cycling keeps dP stable at design rate (operationalised: dP(5min) <= 1.5 x dP(t0)); kill: >50% face covered in <1 min at design rate",
    "result": "Design rate ≈37 bells/min (prototype 0.3 /m³ face loading, Froude time-scaled). Head over 5 min: 0.28 → 4.6 mm without cycling, 0.28 → 2.3 mm with cycling. Face cover 33% vs 25%. Never >50% within 1 min. At 74/min, 50% …"
   },
   {
    "test": "T06",
    "name": "roll-down seal",
    "metric": "fraction of runs with bells under",
    "value": 0.0,
    "verdict": "PASS",
    "criterion": "gap ~0 and 0 bells under (seated); kill if bells pass under in >10% of runs",
    "result": "Deploy time 8.6 s (6.5–11.3). Seated gap 1.0–2.5 mm. 0 bells under the seated bar in 10/10 runs; no bell was pinned. However, 4–12 bells slipped under while the bar was being lowered"
   },
   {
    "test": "T07",
    "name": "relief pulse",
    "metric": "single-bay pulse fraction (mean)",
    "value": 0.339355,
    "verdict": "PASS on average / FAIL for the downstream bay",
    "criterion": "pulse is a small fraction of bells on the face (operationalised: <=35%, ~one bay of four + margin)",
    "result": "Lifting one bay releases 34% of the bells on the face on average (0–91%). By bay: bay 1 (upstream) 0%, bay 2 2%, bay 3 54%, bay 4 (downstream) 80%. Lifting all bays releases more than were on the face, because bells ups…"
   },
   {
    "test": "T08",
    "name": "outer guide line",
    "metric": "min eta_g over angles/directions",
    "value": 0.944444,
    "verdict": "PASS at 15 deg,20 deg,25 deg",
    "criterion": "eta_g >= 0.4 in both directions",
    "result": "η_g 0.94–1.00 at 15/20/25°, flood and ebb alike"
   },
   {
    "test": "T09",
    "name": "passage damage",
    "metric": "gelatin intact fraction via screw",
    "value": 1.0,
    "verdict": "PASS (SENSITIVE to gel recipe)",
    "criterion": ">=90% intact via screw/siphon; kill <50%",
    "result": "Gelatin bells: screw 100% intact, siphon 100%, pump 0% (shredded). Agar bells (brittle): siphon 67%, 1–5 m tube 63–68%"
   },
   {
    "test": "T10",
    "name": "turtle",
    "metric": "max turtles reaching screw path (of 30)",
    "value": 10.0,
    "verdict": "KILL (some configurations) / SENSITIVE to detection probability",
    "criterion": "100% diverted or exit; kill: any turtle reaching screw path",
    "result": "Camera only: 1–2 per 30 reach the screw path. Person mock: 10/30 swimmers reach it. Camera + door: 0 swimmers reach it, because the door threshold of 6 mN separates a swimmer from a bell pile. Passive turtles exert abou…"
   },
   {
    "test": "T11",
    "name": "fish return",
    "metric": "returned via bypass (mean)",
    "value": 1.0,
    "verdict": "REPORTED",
    "criterion": "report (no target)",
    "result": "1 cm rigid beads: 100% returned via bypass, 0 stuck"
   },
   {
    "test": "T12",
    "name": "drift-back",
    "metric": "return after 3 cycles at 1.0 m",
    "value": 0.261111,
    "verdict": "PASS",
    "criterion": "returns fall with distance",
    "result": "Returned to the intake after 3 cycles: 79% (30 cm), 56% (60 cm), 26% (100 cm)"
   },
   {
    "test": "T13",
    "name": "waves",
    "metric": "worst relative eta_r change",
    "value": 0.04878,
    "verdict": "PASS",
    "criterion": "eta_r drops <20%",
    "result": "Waves 1–4 cm at 1.0–1.5 s raise η_r by 5–84% because shaking unjams bells. 0 leaks; overtopping needs a crest above roughly freeboard + bell radius"
   },
   {
    "test": "T14",
    "name": "extrusion",
    "metric": "fragments extruded (tank)",
    "value": 0.0,
    "verdict": "REPORTED / SENSITIVE (tank cannot reproduce prototype Cauchy number)",
    "criterion": "report; sets the mesh opening",
    "result": "0 of 540 fragments (1–2 cm; 3/5/8 mm mesh) extruded in the tank. At tank scale ΔP/E ≈ 1e-4. At prototype scale with 75% blinding and an assumed mesoglea E of 50–300 Pa, extrusion is predicted (`SIM_T14_cauchy_scaling.cs…"
   },
   {
    "test": "T15",
    "name": "bay load",
    "metric": "strip force N at 11 cm/s, 75% blinded",
    "value": 6.881584,
    "verdict": "PASS (scales with blinding)",
    "criterion": "force scales with blinding; compare with calc",
    "result": "Strip force 0.16 N clean → 0.37 / 1.5 / 6.9 N at 25 / 50 / 75% blinding (11 cm/s). That is 1.6–2.3× the uniform hand calculation, because blinding concentrates flow. Prototype equivalent is about ×8000"
   },
   {
    "test": "T16",
    "name": "repeatability",
    "metric": "counter discrepancy (mean)",
    "value": 0.020833,
    "verdict": "FAIL / SENSITIVE (one miss in ~15 counts = 6.7%)",
    "criterion": "<=5% discrepancy",
    "result": "Counter discrepancy 0 / 0 / 6.25% (mean 2.1%). With ~15 counts per run, a single miss is 6.7%, so P(run ≤5%) is only 36–69%"
   }
  ]
 },
 "data_checks": {
  "source": "TESTS/00_data/README.md (Assumption check); machine-readable TESTS/00_data/out/assumption_check.csv",
  "rows": [
   {
    "assumption": "Tidal amplitude U0 (alongshore)",
    "jazr": "0.117 m/s",
    "real": "M2 0.073 m/s alongshore (~080°); spring M2+S2 ≈ 0.108; equivalent U0 from total-current median = 0.118",
    "verdict": "OK. It matches total current and spring tide. Tide alone is weaker, so the twin is slightly conservative"
   },
   {
    "assumption": "Median current",
    "jazr": "0.083 m/s",
    "real": "median 0.083 (quantised value), mean 0.086; p99 0.19; max 0.39 m/s",
    "verdict": "OK. Add the quantisation caveat: quote the mean, 0.086"
   },
   {
    "assumption": "Onshore residual drift",
    "jazr": "1–3 cm/s, with 3 cm/s as the \"worst case\"",
    "real": "Oct–Nov mean 2.5 cm/s (CMEMS), 2.3 cm/s (HYCOM); 3-day mean p90 6.2, p99 9.5 cm/s; 10-day p90 4.7 cm/s; onshore on 76% of days",
    "verdict": "CHANGE. 3 cm/s is the typical case. Run the stress case at 5–6 cm/s (the flaw audit's 5 cm/s run gave 33%)"
   },
   {
    "assumption": "Wind drift",
    "jazr": "not modelled",
    "real": "Oct–Nov onshore wind 1.9–2.2 m/s mean, p99 8–8.7 m/s",
    "verdict": "CHANGE. Add a windage term, or state the exclusion"
   },
   {
    "assumption": "SST (survival, welfare, fouling)",
    "jazr": "31 → 23 °C Oct → Dec; 35 °C summer",
    "real": "Oct 31.4, Nov 27.9 °C; Oct–Nov max 35.1; all-time 17.3–36.7 °C; +0.15 °C/decade",
    "verdict": "OK"
   },
   {
    "assumption": "Wave height (ops/structures)",
    "jazr": "Hs max 1.4 m nearshore; <0.6 m 90% Oct–Nov",
    "real": "Hs p90 Oct–Nov 0.52 m, max 1.02; all-year max 1.42 nearshore, 2.20 offshore",
    "verdict": "OK for operations. For structural design, 4 years is not an extreme-value basis: get 50/100-year Hs"
   },
   {
    "assumption": "Wet mass per animal",
    "jazr": "3 kg typical, 5 kg upper",
    "real": "C. perezi (Oman Sea, n = 503) mean 0.33 kg, max 1.7 kg; UAE Oct–Nov mean bells 6.5–11.8 cm → 0.04–0.13 kg",
    "verdict": "CHANGE. Use about 0.3 kg typical and 1.7 kg upper (or 1–2 kg for the brief's 30–45 cm animals). At 0.1/m³ the stress load falls from 108 to about 12 t/h per unit at 0.33 kg, or about 61 t/h at 1.7 kg"
   },
   {
    "assumption": "Bloom density for sizing",
    "jazr": "0.3 ind/m³ design (0.1–1)",
    "real": "No Gulf density data exist (presence-only records). Shin Hanul's 202 t/day at plant-scale flow implies only ~0.002–0.02 ind/m³",
    "verdict": "OK as conservative. It cannot be validated"
   },
   {
    "assumption": "Species",
    "jazr": "C. mosaicus",
    "real": "33 of 35 Gulf records are C. perezi",
    "verdict": "CHANGE. Say \"Catostylus sp. (likely C. perezi)\""
   },
   {
    "assumption": "Jellyfish swim speed",
    "jazr": "3.6 / 10 cm/s",
    "real": "no new data",
    "verdict": "Unchanged (no data)"
   },
   {
    "assumption": "Turtles near the intake",
    "jazr": "camera diverter; turtles bell-sized",
    "real": "39 green turtles tracked; fixes within 6.5 km of the site; displacement p90 0.33 m/s, p99 0.87 m/s",
    "verdict": "OK. Turtles are present, and many move faster than the 0.10 m/s approach velocity. No sizes are in the open data"
   },
   {
    "assumption": "Bloom-load distribution",
    "jazr": "Shin Hanul 200 t/day pilot load",
    "real": "no public daily series",
    "verdict": "NOT AVAILABLE"
   }
  ]
 },
 "_notes": [
  "twin_results: no eta_r 0.95-0.99 leak values exist in twin/out (v5 runs fixed eta_r=0.9); v5_rows omitted.",
  "vt_guidance: guidance CSV has no entrance-flow column; bypass/entrance-flow % vs eta comes from SIM_sensitivity.json 'bypass' block (bypass_scan)."
 ],
 "_generated": "extracted by build_evidence.py from JAZR result files; all numbers model-based/simulated"
};
