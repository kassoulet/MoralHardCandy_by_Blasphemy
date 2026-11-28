#!/usr/bin/env python3
"""te2rb_tang.py DAT/te2rb.3ds ../web/assets/te2rb.json [--write] - derive the Camera02 key tangents (pos, target, roll) from the 3DS keys by running the
engine's own tangent code (x87tang.py, listing tang_x87.dis: 0x37230 first / 0x37040 interior / 0x37300 last key, TCB all 0) and compare with the engine dump in
the json (bit-identical except the two unused slots per track: first in-tangent, last out-tangent, which the engine leaves uninitialised). --write stores the derived values."""
import sys,json,numpy as np
sys.path.insert(0,__file__.rsplit('/',1)[0]); import m3ds,x87tang
f=np.float32
def derive(path):
    o,tr=m3ds.load(path); out={}
    for name,key,sw in (('pos',(45059,'Camera02',45088),1),('tgt',(45060,'Camera02',45088),1),('roll',(45059,'Camera02',45092),0)):
        s=sorted(tr[key]); fr=np.array([a for a,_ in s],float); P=np.array([b for _,b in s],f)
        if sw: P=P[:,[0,2,1]]          # 3DS (x,y,z) -> engine (x,z,y)
        ti,to=x87tang.tangents(fr,P if sw else np.pad(P,((0,0),(0,2)))); n=P.shape[1]
        out[name]=(fr,P,ti[:,:n],to[:,:n])
    return out
if __name__=='__main__':
    j=json.load(open(sys.argv[2])); D=derive(sys.argv[1]); bad=tot=0
    for n,(fr,P,ti,to) in D.items():
        for i,k in enumerate(j['cam'][n]):
            assert k['f']==fr[i] and np.array_equal(f(k['v']),P[i])
            for nm,a in (('ti',ti[i]),('to',to[i])):
                if (nm=='ti' and i==0) or (nm=='to' and i==len(fr)-1): continue
                tot+=len(a); bad+=int(np.sum(f(k[nm])!=a))
            if '--write' in sys.argv:
                if i: k['ti']=[float(x) for x in ti[i]]
                if i<len(fr)-1: k['to']=[float(x) for x in to[i]]
    print('tangent components differing from the engine dump: %d of %d'%(bad,tot))
    if '--write' in sys.argv: json.dump(j,open(sys.argv[2],'w'),separators=(',',':'))
