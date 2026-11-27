#!/usr/bin/env python3
"""export_poly.py PKL OUTDIR - probe_poly.py capture -> OUTDIR/polys.json + tex.bin (256x256x32 texture read from the boot snapshot) for tools/polytest.mjs"""
import sys,pickle,json,base64,zlib,struct,os
SNAP='/tmp/claude-1000/-home-gautier-SynologyDrive-code-current-demoports/32c9b7ad-cb1e-451b-a282-9c45f32c7e6e/scratchpad/mhc/boot.mem'
PI=pickle.load(open(sys.argv[1],'rb')); out=sys.argv[2]; os.makedirs(out,exist_ok=True)
mem=zlib.decompress(open(SNAP,'rb').read())
b64=lambda x:base64.b64encode(x).decode()
texbuf=struct.unpack('<I',PI[0]['tex'][0x10:0x14])[0]
open(out+'/tex.bin','wb').write(mem[texbuf:texbuf+256*1024])
L=[]
for d in PI:
    nv=struct.unpack('<I',d['item'][12:16])[0]
    L.append(dict(t=d['t'],item=b64(d['item']),nv=nv,verts=[b64(v) for v in d['verts'][:nv]],mat=b64(d['mat']),
      spans=[s[2][1:9] for s in d['spans']],chg=[d['chg'][0].tolist(),d['chg'][1].tolist(),d['chg'][2].tolist()]))
json.dump(dict(texbuf=texbuf,surf=0x402ffb8,polys=L),open(out+'/polys.json','w'))
print(len(L),'polys',texbuf)
