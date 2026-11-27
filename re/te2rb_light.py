#!/usr/bin/env python3
"""te2rb_light.py golden/meshes.pkl ../web/assets/te2rb.json - add the engine's per-face light index of Tube03 (face +0x58, baked at load by 0x34510, static: identical at 27 s and 52 s)
and the material colour ramp (256 dwords at material+0xc) to the scene data. These two are dumps (not derived): the lighting function 0x34510 is not ported."""
import sys,json,base64,pickle,numpy as np
d=pickle.load(open(sys.argv[1],'rb')); j=json.load(open(sys.argv[2]))
F=d['meshes'][2]['faces']; assert len(F)==1704
b64=lambda a:base64.b64encode(np.ascontiguousarray(a).tobytes()).decode()
j['tube']['li']=b64(np.array([f['idx'] for f in F],np.uint8)); j['ramp']=b64(np.frombuffer(d['ramp'],np.uint32)[:256])
json.dump(j,open(sys.argv[2],'w'),separators=(',',':'))
