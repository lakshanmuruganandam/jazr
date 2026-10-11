"""T2 - Turtle, dugong and dolphin safety.

(a) swim speed vs every JAZR velocity; (b) enclosed-path breath-hold exposure;
(c) camera detection probability required; (d) required camera-to-screw stop distance.
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from params import *

# ---- swim speeds (m/s). low/high of SUSTAINED/cruising; burst separately ----
species = {
    "juvenile hawksbill (net, tracked)": dict(cruise=(0.125, 0.16), burst=None, src="SRC 5 (net displacement, underestimates instantaneous speed)"),
    "juvenile green (net, tracked)":     dict(cruise=(0.168, 0.168), burst=None, src="Current Biology, Gulf of Mexico (via search; net)"),
    "loggerhead+green cruising (logger)": dict(cruise=(0.27, 0.50), burst=None, src="SRC 4 Kinoshita et al. (measured)"),
    "dugong":                             dict(cruise=(0.6, 1.1), burst=8.3, src="SRC 6 sirenian review"),
    "humpback dolphin":                   dict(cruise=None, burst=None, src="no verified speed found; dives mean 20 s [SRC 19]"),
}
device = {"screen approach": 0.10, "EPA 316(b) 0.5 ft/s": 0.152, "lane / sweep": V_SWEEP,
          "bypass mouth low": V_BYPASS[0], "bypass mouth high": V_BYPASS[1], "pipe": 1.77}

res = {"species": species, "device_velocities": device}
# exceedance table: can the animal sustain swimming away (cruise_low > velocity)?
tab = {}
for s, d in species.items():
    if d["cruise"] is None:
        continue
    tab[s] = {k: ("escapes" if d["cruise"][0] > vel else ("marginal" if d["cruise"][1] > vel else "carried")) for k, vel in device.items()}
res["escape_table"] = tab

# ---- (b) breath-hold exposure in enclosed path ----
pipe_min = PIPE_L[1] / 1.768 / 60
res["breath_hold"] = dict(enclosed_pipe_minutes=pipe_min,
    turtle_reference="NMFS trawl tow-time limit 55/75 min; green turtles failed 2 h forced submergence; delayed death from aspiration [SRC 18]",
    dolphin_reference="Sousa mean dive 20 s [SRC 19]",
    verdict="pipe is an absolute no-entry zone for air-breathers: 47 min full-bore + screw/pump strike")

# ---- (c) required detection probability ----
# Expected turtle arrivals at the bypass per unit-season N is UNKNOWN (no intake-caught data at the plant; ENEC's 70/yr
# are stranded/distressed). Scenario range 1-50 per unit-season [ASSUME]; St Lucie (velocity cap, Florida) 497/yr [SRC 21].
target = 0.01   # target expected turtles reaching screw per site-year (4 units) [ASSUME criterion: 1 in 100 years]
N = np.array([1, 5, 10, 20, 50])
req_miss = target / (UNITS * N)
res["detection_requirement"] = {int(n): dict(required_P_detect_system=1 - m) for n, m in zip(N, req_miss)}
# what a single YOLO-class camera achieves (recall 0.83-0.85) [SRC 17] ; layered independent barriers
r_cam = 0.85
p_div_fail = 0.01     # diverter gate fails to move on demand [ASSUME]
p_door_fail = 0.3     # passive push door fails (exhausted turtle / bell pile) [ASSUME, SRC 15_ file: untested]
p_stop_fail = 0.01    # screw does not stop in time [ASSUME given T2d geometry]
layers = {}
for ncam in (1, 2, 3):
    miss_cam = (1 - r_cam) ** ncam   # assumes independence (optimistic: turbidity/night are common-mode)
    p_reach = (miss_cam + (1 - miss_cam) * p_div_fail) * p_door_fail * p_stop_fail if False else None
    # sequence: camera detect -> (diverter OR stop). If camera misses: only push-door protects.
    p_harm = miss_cam * p_door_fail + (1 - miss_cam) * p_div_fail * p_stop_fail
    layers[f"{ncam}_camera(s)"] = dict(P_miss_cameras=miss_cam, P_harm_per_passage=p_harm, P_protect=1 - p_harm)
# with a physical deformable-pass grid (bells squeeze through, rigid shells do not) in front of the screw [UNTESTED]
p_grid_fail = 0.05  # [ASSUME]
layers["2_cameras+grid"] = dict(P_harm_per_passage=layers["2_camera(s)"]["P_harm_per_passage"] * p_grid_fail)
for k in layers:
    layers[k]["P_protect"] = 1 - layers[k]["P_harm_per_passage"]
res["layers"] = layers

# ---- (d) stop distance ----
# distance needed between the camera and the screw entry so that the animal cannot reach the screw before it is stopped
v_flow = np.array([0.4, 0.55, 0.7])     # bypass/collector velocity
v_swim_down = 0.5                        # turtle swimming WITH the flow (cruise upper) [SRC 4]
lat = dict(frames=3/25, inference=0.2, plc_network=0.1, operator=0.0)   # s, automatic (no human in loop) [ASSUME]
t_detect = sum(lat.values())
t_diverter = (2.0, 5.0)                 # s actuation [ASSUME]
t_screw_stop = (5.0, 20.0)              # s spin-down incl. VFD braking of a ~3 m screw [ASSUME; vendor data needed]
stop = {}
for vf in v_flow:
    vt = vf + v_swim_down
    stop[f"{vf:.2f}"] = dict(v_total=vt,
        d_diverter_m=[vt*(t_detect+t) * 1.5 for t in t_diverter],
        d_screw_stop_m=[vt*(t_detect+t) * 1.5 for t in t_screw_stop])   # 1.5 safety factor
res["stop_distance"] = dict(latency_s=lat, t_detect=t_detect, t_diverter=t_diverter, t_screw_stop=t_screw_stop, table=stop)

# ---- verdicts ----
V = {}
V["T2a_approach_0.10"] = ("PASS", "0.10 m/s < EPA 316(b) 0.15 m/s impingement BTA and below every measured turtle cruising speed; BUT local velocity rises under partial blinding (St Lucie pinning) -> needs per-bay DP limit")
V["T2b_lane_sweep_0.5"] = ("MARGINAL", "0.5 m/s equals the top of measured turtle cruising (0.27-0.50); juveniles (net 0.13-0.17) will be conveyed to the bypass -> the bypass protection is safety-critical, not a backup")
V["T2c_bypass_mouth_0.4-0.7"] = ("FAIL", "exceeds juvenile turtle sustained speed: once at the mouth a juvenile cannot swim out; protection relies entirely on diverter/stop")
V["T2d_dugong_dolphin_lane"] = ("MARGINAL", "dugong cruising 0.6-1.1 m/s can leave the lane; no verified humpback-dolphin speed; both are larger than bells -> add a large-animal bar rack at lane entrance (clear spacing ~0.5 m, sized to pass 45 cm bells) and stop-work on sighting")
V["T2e_breath_hold"] = ("FAIL (if entry possible)", "pipe residence %.0f min full-bore approaches the 55 min tow-time limit and adds pump strike; no air-breather may enter: design must make entry physically impossible, not just unlikely" % pipe_min)
best = layers["3_camera(s)"]["P_protect"]
for k in layers:
    layers[k]["max_turtles_per_unit_season_for_target"] = target / (UNITS * layers[k]["P_harm_per_passage"])
V["T2f_camera_requirement"] = ("FAIL", "required system protection >= %.5f (10 turtles/unit-season, target 0.01/site-yr); 1 camera at recall 0.85 gives %.3f; 3 independent cameras %.4f; 2 cameras+physical grid %.5f -> tolerates only ~%.0f turtle passages/unit-season (grid untested)" %
                               (res['detection_requirement'][10]['required_P_detect_system'], layers['1_camera(s)']['P_protect'], best, layers['2_cameras+grid']['P_protect'], target/(UNITS*layers['2_cameras+grid']['P_harm_per_passage'])))
dmax = stop["0.70"]["d_screw_stop_m"][1]; dmin = stop["0.40"]["d_diverter_m"][0]
V["T2g_stop_distance"] = ("REQUIREMENT", "camera must sit >= %.0f m (diverter) and >= %.0f m (screw stop) upstream of the screw entry at 0.7 m/s; collector entrances closer than that need their own final gate" %
                          (stop["0.70"]["d_diverter_m"][1], dmax))
res["verdicts"] = V
save("t2_wildlife.json", res)

# chart
fig, ax = plt.subplots(figsize=(9, 4.2))
names = list(species.keys())
for y, s_ in enumerate(names):
    d = species[s_]
    if d["cruise"]:
        lo, hi = d["cruise"]; hi = max(hi, lo + 0.01)
        ax.plot([lo, hi], [y, y], lw=10, solid_capstyle="butt", color="tab:green")
    else:
        ax.text(0.75, y, "no verified speed found", fontsize=7, va="center", color="gray")
ax.set_yticks(range(len(names))); ax.set_yticklabels(names, fontsize=7)
for k, vel in device.items():
    ax.axvline(vel, ls="--", lw=1, color="tab:red")
    ax.text(vel + 0.01, len(names) - 0.45, k, rotation=90, fontsize=6.5, va="top", color="tab:red")
ax.set_xlim(0, 1.9); ax.set_ylim(-0.6, len(names) - 0.4); ax.set_xlabel("speed (m/s)")
ax.set_title("T2 sustained swim speeds (green, literature) vs JAZR velocities (red dashed)", fontsize=9)
fig.tight_layout(); fig.savefig(os.path.join(CH, "t2_swim_vs_device.png"), dpi=130)

if __name__ == "__main__":
    for k, (vv, why) in V.items():
        print(f"{k:28s} {vv:10s} {why}")
    for k, d in layers.items():
        print(k, d)
