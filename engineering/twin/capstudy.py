import numpy as np, json, os
from ablation import avg, STACK
import jazr_twin as J
if __name__ == '__main__':
  R={}
  for name in ("S5","S7"):
      kw=[k for n,k in STACK if n.startswith(name)][0]
      for cap in (None, 1000, 300, 100, 30):
          a=avg(dict(kw, cap_t=cap)); R[f"{name}|cap={cap}"]=a
          print(f"{name} cap {str(cap):5s} t/pocket: intake {a['captured']*100:5.1f}%  handled {a['handlings']:.2f}x  peak held {a['peak_held_t']:6.0f} t  >2km {a['far']*100:.0f}%",flush=True)
  json.dump(R,open(os.path.join(J.OUT,"capstudy.json"),"w"),indent=1)
