"""v5 no-harm: replace Recover (lethal) with HOLD-ALIVE (capped flow-through pocket) + release at 5 km; overflow -> release.
Twin mass is 3 kg/animal; real mass 0.33 kg -> real tonnes = twin tonnes x 0.11."""
import json, os
from v4study import avg
import jazr_twin as J
if __name__=="__main__":
    R={}; k=0.33/3.0
    base=dict(system=True,ring=False,eta_r=0.9,gate_x=1200,gate_y=5000,vr=-0.025,hours=240)
    R["release only"]=avg(dict(base,policy="immediate"))
    R["hold unlimited (=no release during bloom)"]=avg(dict(base,policy="hold",hold_h=1e9))
    for real_t in (25,50,100,200,400):
        R[f"hold-alive cap {real_t} t real"]=avg(dict(base,policy="hold",hold_h=1e9,cap_t=real_t/k))
    for lab,v in R.items(): print(f"{lab:42s}: {v[0]*100:5.1f}% [{v[1]*100:.0f}-{v[2]*100:.0f}]")
    json.dump(R,open(os.path.join(J.OUT,"v5_noharm.json"),"w"),indent=1)
