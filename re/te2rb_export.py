#!/usr/bin/env python3
"""te2rb_export.py OUT.json - compact scene data for web/te2rb.js: engine-space meshes (float32, from the 3DS exactly as te2rb_wire/te2rb_poly build them),
faces + edge flags, Sphere01 uv, camera key structs (frame, value, in/out tangent; tangents are the engine's own dump, not yet derived from the 3DS), W of Sphere01."""
import sys,os,json,base64,pickle,struct,numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import m3ds,te2rb_f32 as F,te2rb_poly as P,te2rb_wire as W
f32=np.float32; b64=lambda a:base64.b64encode(np.ascontiguousarray(a).tobytes()).decode()
o,_=m3ds.load('golden/dat/te2rb.3ds'); tt=o['Tube03']['m'][3]
E,UV,FA=P.sphere()
pk,tk,rk=W.keys()
def keys(b,n,comp):
    return [dict(f=F.key_f(b,i),v=list(F.key_v(b,i,8,comp)),ti=list(F.key_v(b,i,0x18,comp)),to=list(F.key_v(b,i,0x28,comp))) for i in range(n)]
d=dict(tube=dict(v=b64(F.engine_vertices(o['Tube03']['v'],tt)),f=b64(o['Tube03']['f'].astype(np.uint16)),ff=b64(o['Tube03']['ff'].astype(np.uint8)),t=[float(x) for x in tt]),
  sphere=dict(v=b64(E),uv=b64(UV),f=b64(FA.astype(np.uint16)),W=b64(P.WSPH)),
  cam=dict(pos=keys(pk[1],pk[0],3),tgt=keys(tk[1],tk[0],3),roll=keys(rk[1],rk[0],1)))
json.dump(d,open(sys.argv[1],'w'),separators=(',',':'))
