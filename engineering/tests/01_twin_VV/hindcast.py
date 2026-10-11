"""Real-forcing loader for the hindcast tests. Uses whatever the data agent left in ../00_data/raw:
  openmeteo_marine/marine_near.json : hourly ocean_current_velocity (km/h) + ocean_current_direction
                                      (deg, direction the current flows TOWARD) at 24.04N 52.21E (2022-2025)
  openmeteo_era5/era5_wind.json      : hourly wind_speed_10m (m/s) + wind_direction_10m (deg, FROM), optional
Rotation into twin axes (same assumption as 00_data/scripts/analyse_metocean.py): coast trends 070/250 deg, so
twin +x (alongshore) = toward 070 deg and twin +y (offshore) = toward 340 deg (onshore normal = 160 deg).
Returns None if the files are missing, so the pytest hindcast test can skip with a clear message."""
import os, json
import numpy as np
from common import HERE
DATA = os.path.abspath(os.path.join(HERE, "..", "00_data", "raw"))
COAST_DEG = 70.0

def _arr(lst): return np.array([np.nan if v is None else v for v in lst], float)

def load(coast_deg=COAST_DEG):
    fm = os.path.join(DATA, "openmeteo_marine", "marine_near.json")
    if not os.path.exists(fm): return None
    h = json.load(open(fm))["hourly"]
    unit = json.load(open(fm)).get("hourly_units", {}).get("ocean_current_velocity", "km/h")
    spd = _arr(h["ocean_current_velocity"]) / (3.6 if unit == "km/h" else 1.0)
    dr = np.deg2rad(_arr(h["ocean_current_direction"]))
    east, north = spd*np.sin(dr), spd*np.cos(dr)
    a = np.deg2rad(coast_deg); ax_ = (np.sin(a), np.cos(a)); ay = (np.sin(a-np.pi/2), np.cos(a-np.pi/2))  # 070 and 340
    u = east*ax_[0] + north*ax_[1]; v = east*ay[0] + north*ay[1]
    t = np.array(h["time"], dtype="datetime64[h]")
    ok = ~np.isnan(u)
    u = np.interp(np.arange(len(u)), np.where(ok)[0], u[ok]); v = np.interp(np.arange(len(v)), np.where(ok)[0], v[ok])
    out = dict(time=t, u=u, v=v, n_missing=int((~ok).sum()), wind=None)
    fw = os.path.join(DATA, "openmeteo_era5", "era5_wind.json")
    if os.path.exists(fw):
        w = json.load(open(fw)); hw = w["hourly"]; un = w.get("hourly_units", {}).get("wind_speed_10m", "m/s")
        ws = _arr(hw["wind_speed_10m"]) / (3.6 if un == "km/h" else 1.0)
        wd = np.deg2rad(_arr(hw["wind_direction_10m"]) + 180.0)          # FROM -> TOWARD
        we, wn = ws*np.sin(wd), ws*np.cos(wd)
        tw = np.array(hw["time"], dtype="datetime64[h]")
        wu = we*ax_[0] + wn*ax_[1]; wv = we*ay[0] + wn*ay[1]
        # align to the marine time axis
        idx = np.searchsorted(tw, t); good = (idx < len(tw)) & (tw[np.minimum(idx, len(tw)-1)] == t)
        wu_a = np.full(len(t), np.nan); wv_a = np.full(len(t), np.nan)
        wu_a[good] = wu[idx[good]]; wv_a[good] = wv[idx[good]]
        okw = ~np.isnan(wu_a)
        if okw.sum() > 10:
            wu_a = np.interp(np.arange(len(t)), np.where(okw)[0], wu_a[okw]); wv_a = np.interp(np.arange(len(t)), np.where(okw)[0], wv_a[okw])
            out["wind"] = (wu_a, wv_a)
    return out

class Series:
    """Picklable f(t_seconds) -> (u, v), linear interpolation of an hourly series starting at index i0."""
    def __init__(self, u, v, i0, hours):
        n = int(np.ceil(hours)) + 2
        self.u = np.asarray(u[i0:i0+n], float); self.v = np.asarray(v[i0:i0+n], float)
    def __call__(self, t):
        h = t/3600.0; k = int(h); f = h-k; k = min(k, len(self.u)-2)
        return (self.u[k]*(1-f) + self.u[k+1]*f, self.v[k]*(1-f) + self.v[k+1]*f)
