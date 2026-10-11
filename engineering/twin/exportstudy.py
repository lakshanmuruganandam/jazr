import json, os
from ablation import avg
import jazr_twin as J
if __name__ == '__main__':
  R={}
  base=dict(system=True, policy="ebb", window=0.25, ratchet=0.07, cap_t=100)
  for lab,kw in [("passive lane end 2 km",dict(gate_x=2000,gate_y=150)),
                 ("passive lane end 3 km",dict(gate_x=3000,gate_y=150)),
                 ("pipe 1 km offshore",dict(gate_x=1200,gate_y=1000)),
                 ("pipe 1.5 km offshore",dict(gate_x=1200,gate_y=1500)),
                 ("pipe 2 km offshore",dict(gate_x=1200,gate_y=2000)),
                 ("pipe 3 km offshore",dict(gate_x=1200,gate_y=3000)),
                 ("pipe 3 km, immediate (no timing)",dict(gate_x=1200,gate_y=3000,policy="immediate")),
                 ("pipe 3 km, eta_g 0.5",dict(gate_x=1200,gate_y=3000,eta_g=0.5)),
                 ("pipe 3 km, eta_g 0.5, eta_r 0.5",dict(gate_x=1200,gate_y=3000,eta_g=0.5,eta_r=0.5)),
                 ("pipe 3 km, swim 0.10",dict(gate_x=1200,gate_y=3000,swim=0.10)),
                 ("pipe 3 km, onshore 1 cm/s",dict(gate_x=1200,gate_y=3000,vr=-0.01))]:
      a=avg(dict(base,**kw)); R[lab]=a
      print(f"{lab:36s}: intake {a['captured']*100:5.1f}% [{a['lo']*100:.0f}-{a['hi']*100:.0f}] handled {a['handlings']:.2f}x  >2km {a['far']*100:.0f}%",flush=True)
  json.dump(R,open(os.path.join(J.OUT,"exportstudy.json"),"w"),indent=1)
