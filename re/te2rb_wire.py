"""te2rb wire pass end to end: t -> list of 0x2ff80 line calls, from the raw 3DS only (camera + projection + face/edge selection + 0x300a0 setup).
Check: python3 -I te2rb_wire.py (needs golden/dat/te2rb.3ds and golden/pf/LNOUT_<t>.pkl from probe_lines.py)"""
import numpy as np,sys,pickle,collections,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import m3ds,te2rb_cam,te2rb_line
f32=np.float32
BASE=0x402ffb8
def calls(t,path='golden/dat/te2rb.3ds'):
    o,_=m3ds.load(path); tt=o['Tube03']['m'][3].astype(float); V=o['Tube03']['v'].astype(float)
    F=o['Tube03']['f']; ff=o['Tube03']['ff']
    p,R=te2rb_cam.camera(t,path)
    E=np.stack([tt[1]-V[:,1],V[:,2],V[:,0]-tt[0]],1)       # 3DS -> engine model
    c=((E-p)@R*[0.25,0.5,1]).astype(f32)
    z=c[:,2]; ok=z>0; zz=np.where(ok,z,1)
    sx=(f32(255.5)+f32(256)*c[:,0]/zz).astype(f32); sy=(f32(127.5)-f32(128)*c[:,1]/zz).astype(f32)
    inside=ok&(sx>=0)&(sx<512)&(sy>=0)&(sy<256)
    out=[]
    for (a,b,cc),fl in zip(F,ff):
        if not(inside[a] and inside[b] and inside[cc]): continue
        cr=(sx[b]-sx[a])*(sy[cc]-sy[a])-(sx[cc]-sx[a])*(sy[b]-sy[a])
        if not cr<0: continue
        v=(a,b,cc)
        for i in range(3):
            if fl>>i&1:
                r=te2rb_line.setup(sx[v[i]],sy[v[i]],sx[v[(i+1)%3]],sy[v[(i+1)%3]])
                if r: out.append((BASE+r[0],r[1],r[2],r[3]&0xffffffff,r[4]&0xffffffff,r[5]))
    return out
if __name__=='__main__':
    for T in sys.argv[1:] or ['27.0','27.2','27.4','27.6','27.8','28.0']:
        d=pickle.load(open(f'golden/pf/LNOUT_{T}.pkl','rb'))
        cap=collections.Counter((x[0],x[1],x[2],x[4]&0xffffffff,x[5]&0xffffffff,x[6]) for x in d)
        pr=collections.Counter(calls(float(T)))
        print(T,'captured',len(d),'predicted',sum(pr.values()),'exact',sum((cap&pr).values()))
