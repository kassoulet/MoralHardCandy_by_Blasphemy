#!/usr/bin/env python3
"""partmap.py SNAP.mem DATDIR OUT.json - which CANDY.DAT files each of the 14 parts references (string-literal refs inside the part's own
init/render functions; the shared base-class code 0x1dd90..0x1e100 is excluded)."""
import zlib,struct,os,sys,json
m=zlib.decompress(open(sys.argv[1],'rb').read()); u=lambda a:struct.unpack('<I',m[a:a+4])[0]
names={n.lower() for n in os.listdir(sys.argv[2])}
def cstr(a): return m[a:m.index(b'\0',a)].decode('latin1')
refs={}
for i in range(0x1000,0x56000-4):
    v=u(i)
    if 0x100000<=v<0x120000:
        try: s=cstr(v)
        except Exception: continue
        if s.lower() in names: refs[i]=s
parts=[u(0x10c790+4*i) for i in range(14)]
vts=[u(u(p)+4) for p in parts]
ents=sorted({u(v+4*j) for v in vts for j in range(10) if 0x1000<u(v+4*j)<0x56000})
out=[]
for i,v in enumerate(vts):
    fs=[]
    for j in (2,3,4,6,7):
        e=u(v+4*j); nxt=min([x for x in ents if x>e]+[0x56000])
        if 0x1de00<=e<0x1e200 and j!=3: continue
        for a,s in refs.items():
            if e<=a<nxt and s not in fs: fs.append(s)
    out.append(dict(i=i,vtable=hex(v),files=fs))
json.dump(out,open(sys.argv[3],'w'),indent=1)
for o in out: print(o['i'],o['files'])
