import json, os
from v4study import avg
import jazr_twin as J
if __name__=="__main__":
    R={}
    base=dict(system=True,ring=False,eta_r=0.9,vr=-0.025,hours=240,policy="immediate")
    for gx,gy in ((1200,5000),(1200,10000),(5000,3000),(10000,3000),(15000,3000)):
        for ur in (0.0,0.01):
            m=avg(dict(base,gate_x=gx,gate_y=gy,ur=ur)); R[f"outlet x={gx} y={gy} ur={ur}"]=m
            print(f"outlet alongshore {gx/1000:4.1f} km, offshore {gy/1000:4.1f} km, residual {ur}: {m[0]*100:5.1f}% [{m[1]*100:.0f}-{m[2]*100:.0f}]",flush=True)
    json.dump(R,open(os.path.join(J.OUT,"v5_far.json"),"w"),indent=1)
