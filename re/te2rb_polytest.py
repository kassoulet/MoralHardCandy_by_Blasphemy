"""python3 -I te2rb_polytest.py [golden/poly/pall.pkl]: Sphere01 polygon items vs the emulator's items (screen xy, +0x40/+0x44/+0x50, order)"""
import sys,os,pickle,struct,numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import te2rb_poly as P
f32=np.float32
PI=pickle.load(open(sys.argv[1] if len(sys.argv)>1 else 'golden/poly/pall.pkl','rb'))
for T in sorted(set(p['t'] for p in PI)):
    cap=[]
    for p in [p for p in PI if p['t']==T]:
        nv=struct.unpack('<I',p['item'][12:16])[0]
        cap.append([tuple(np.frombuffer(v[:0x58],f32)[i] for i in (6,7,0x40//4,0x44//4,0x50//4)) for v in p['verts'][:nv]])
    mine=[[(v['sx'],v['sy'],v['uz'],v['vz'],v['iz']) for v in vs] for idx,vs in P.items(T)]
    same=sum(1 for a,b in zip(cap,mine) if a==b); n=len(cap)
    print('t=%.1f captured %d mine %d identical in order %d'%(T,n,len(mine),same))
