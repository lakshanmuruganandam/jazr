"""Minimal Bloom Incident OS state machine (one unit) for the T9 operations smoke test.

States: IDLE -> READY -> DEPLOYING -> OPERATING -> STANDDOWN -> IDLE
Rules encoded (from JAZR_GATE_v3 + fixes recommended by tests T2/T6/T7):
  * human approval for Deploy and Stand-down, EXCEPT a pre-authorised close alert (lead < 1 h, RED) auto-deploys (T6b)
  * one relief bay never deploys (never block the lane, FATAL 3)
  * staged roll-up: at most one bay rolling at a time; per-bay dP must persist >= filter time (wave/tide transients)
  * camera turtle detection -> diverter to escape chute + screw stop; restart only after clear time
  * outlet chosen from forecast; none safe -> RECOVER mode (no release)
Time unit: seconds of simulated time, advanced with tick().
"""
import json

IDLE, READY, DEPLOYING, OPERATING, STANDDOWN = "IDLE", "READY", "DEPLOYING", "OPERATING", "STANDDOWN"


class TransitionError(Exception):
    pass


class BloomOS:
    def __init__(self, n_bays=18, relief_bays=(17,), deploy_s=600, rollup_s=90, dp_trip_pa=400.0,
                 dp_filter_s=30, turtle_clear_s=60, close_alert_h=1.0, preauthorised=True):
        self.n_bays = n_bays
        self.relief = set(relief_bays)
        self.deploy_s = deploy_s
        self.rollup_s = rollup_s
        self.dp_trip = dp_trip_pa
        self.dp_filter_s = dp_filter_s
        self.turtle_clear_s = turtle_clear_s
        self.close_alert_h = close_alert_h
        self.preauth = preauthorised
        self.t = 0.0
        self.state = IDLE
        self.bays = {i: "UP" for i in range(n_bays)}       # UP / DOWN / ROLLING_UP / ROLLING_DOWN
        self.dp = {i: 0.0 for i in range(n_bays)}
        self.dp_since = {i: None for i in range(n_bays)}
        self.rolling = None
        self.roll_until = 0.0
        self.roll_queue = []
        self.deploy_until = None
        self.screw_running = False
        self.diverter = "BYPASS"
        self.turtle_last = None
        self.outlet = None
        self.mode = "RELEASE"
        self.alert = None
        self.approvals = {}
        self.log = []
        self.max_simultaneous_rolling = 0

    # ---------- helpers ----------
    def _go(self, new, why, by="auto"):
        self.log.append(dict(t=self.t, frm=self.state, to=new, why=why, by=by))
        self.state = new

    def _require(self, *states):
        if self.state not in states:
            raise TransitionError(f"not allowed in {self.state}")

    def deployable_bays(self):
        return [i for i in range(self.n_bays) if i not in self.relief]

    # ---------- operator / external inputs ----------
    def receive_alert(self, lead_h, level="RED"):
        self._require(IDLE, READY)
        self.alert = dict(t=self.t, lead_h=lead_h, level=level, close=lead_h < self.close_alert_h)
        if self.state == IDLE:
            self._go(READY, f"alert lead {lead_h} h {level}")
        if self.alert["close"] and level == "RED" and self.preauth:
            self._start_deploy(by="pre-authorised")

    def approve(self, step, by):
        self.approvals[step] = dict(t=self.t, by=by)
        if step == "deploy":
            self._require(READY)
            self._start_deploy(by=by)
        elif step == "standdown":
            self._require(OPERATING)
            self._go(STANDDOWN, "stand-down approved", by)
            self.screw_running = False
            for i in self.bays:
                if self.bays[i] == "DOWN":
                    self.roll_queue.append(i)
        else:
            raise TransitionError(f"unknown step {step}")

    def _start_deploy(self, by):
        self._go(DEPLOYING, "deploy", by)
        self.deploy_until = self.t + self.deploy_s
        for i in self.deployable_bays():
            self.bays[i] = "ROLLING_DOWN"
        self.screw_running = True

    def set_forecast(self, safe_outlets):
        """safe_outlets: dict name -> bool (72 h drift forecast clear of exclusion zones)."""
        ok = [k for k, v in safe_outlets.items() if v]
        if ok:
            self.outlet, self.mode = ok[0], "RELEASE"
        else:
            self.outlet, self.mode = None, "RECOVER"

    def bay_dp(self, bay, pa):
        self.dp[bay] = pa
        if pa >= self.dp_trip:
            if self.dp_since[bay] is None:
                self.dp_since[bay] = self.t
        else:
            self.dp_since[bay] = None

    def turtle_detected(self, entrance):
        self.diverter = "ESCAPE"
        self.screw_running = False
        self.turtle_last = self.t
        self.log.append(dict(t=self.t, event="turtle", entrance=entrance))

    # ---------- time ----------
    def tick(self, dt=1.0):
        steps = int(round(dt))
        for _ in range(steps):
            self.t += 1.0
            self._step()

    def _step(self):
        if self.state == DEPLOYING and self.t >= self.deploy_until:
            for i in self.deployable_bays():
                self.bays[i] = "DOWN"
            self._go(OPERATING, "all bays down (relief bay open)")
        if self.state == OPERATING:
            for i, since in self.dp_since.items():
                if since is not None and self.t - since >= self.dp_filter_s and self.bays[i] == "DOWN" and i not in self.roll_queue:
                    self.roll_queue.append(i)
        # staged roll-up: one bay at a time
        if self.rolling is not None and self.t >= self.roll_until:
            b = self.rolling
            self.bays[b] = "UP"
            self.rolling = None
            self.dp[b] = 0.0; self.dp_since[b] = None
            if self.state == OPERATING:      # self-clean cycle: bay re-deploys after clearing
                self.bays[b] = "DOWN"
        if self.rolling is None and self.roll_queue:
            b = self.roll_queue.pop(0)
            self.rolling = b
            self.bays[b] = "ROLLING_UP"
            self.roll_until = self.t + self.rollup_s
        self.max_simultaneous_rolling = max(self.max_simultaneous_rolling,
                                            sum(1 for s in self.bays.values() if s == "ROLLING_UP"))
        # turtle clear -> restart screw (only while operating)
        if self.turtle_last is not None and self.t - self.turtle_last >= self.turtle_clear_s:
            self.turtle_last = None
            self.diverter = "BYPASS"
            if self.state == OPERATING:
                self.screw_running = True
        if self.state == STANDDOWN and self.rolling is None and not self.roll_queue:
            if all(s == "UP" for s in self.bays.values()):
                self._go(IDLE, "all bays stowed")
                self.alert = None

    # ---------- invariants & dashboard ----------
    def invariants(self):
        assert any(self.bays[i] == "UP" for i in self.relief), "relief bay must stay open"
        assert self.max_simultaneous_rolling <= 1, "staged roll-up violated"
        if self.diverter == "ESCAPE":
            assert not self.screw_running, "screw must be stopped while a turtle is diverted"
        if self.mode == "RECOVER":
            assert self.outlet is None
        return True

    def dashboard(self):
        d = dict(t=self.t, state=self.state, mode=self.mode, outlet=self.outlet,
                 bays_down=sum(1 for s in self.bays.values() if s == "DOWN"),
                 bays_rolling=sum(1 for s in self.bays.values() if s.startswith("ROLLING")),
                 relief_open=all(self.bays[i] == "UP" for i in self.relief),
                 screw_running=self.screw_running, diverter=self.diverter,
                 alert=self.alert, last_events=self.log[-5:])
        json.dumps(d)     # must be serialisable for the web dashboard
        return d
