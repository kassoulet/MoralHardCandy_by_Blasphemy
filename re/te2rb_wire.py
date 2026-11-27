"""te2rb wire pass end to end: t -> list of 0x2ff80 line calls. Camera/matrices/vertex transform/projection are float32 and bit-exact (te2rb_f32.py),
face + edge selection from the 3DS, line setup te2rb_line.setup.  Check: python3 -I te2rb_wire.py (needs golden/ from probe_cam.py / probe_faces.py)"""
import numpy as np,sys,pickle,collections,os,struct
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import m3ds,te2rb_f32 as F,te2rb_line
f32=np.float32
BASE=0x402ffb8
START=26.5      # part start (music row 4:9)
_KEYS=None
def keys():
    global _KEYS
    if _KEYS is None:
        r=pickle.load(open('golden/cam/c_cam.pkl','rb'))[0]; _KEYS=(r['pk'],r['tk'],r['rk'])
    return _KEYS
def frame(t): return f32(f32(f32(t)-f32(START))*f32(35)) if False else f32(f32(np.float64(t)-START)*f32(35))
def screen(t,path='golden/dat/te2rb.3ds'):
    o,_=m3ds.load(path); tt=o['Tube03']['m'][3]; V3=o['Tube03']['v']
    pk,tk,rk=keys(); f=frame(t)
    pos=F.hermite(pk[1],pk[0],f,3); tg=F.hermite(tk[1],tk[0],f,3); rl=F.hermite(rk[1],rk[0],f,1)
    V=F.view_matrix(pos,tg,rl[0]); M=F.tube_matrix_p((tt[0],f32(0),tt[1]),V)   # node pos = (t.x, 0, t.y)
    C=F.xform(F.engine_vertices(V3,tt),M); sx,sy=F.project(C)
    return o,C,sx,sy
def calls(t):
    o,C,sx,sy=screen(t); F_=o['Tube03']['f']; ff=o['Tube03']['ff']
    z=C[:,2]; ok=z>0; zz=np.where(ok,z,1)
    inside=ok&(sx>=0)&(sx<512)&(sy>=0)&(sy<256)
    out=[]
    for (a,b,cc),fl in zip(F_,ff):
        if not(inside[a] and inside[b] and inside[cc]): continue
        cr=f32(f32(f32(sx[b]-sx[a])*f32(sy[cc]-sy[a]))-f32(f32(sx[cc]-sx[a])*f32(sy[b]-sy[a])))
        if not cr<0: continue
        v=(a,b,cc)
        for i in range(3):
            if fl>>i&1:
                r=te2rb_line.setup(sx[v[i]],sy[v[i]],sx[v[(i+1)%3]],sy[v[(i+1)%3]])
                if r: out.append((BASE+r[0],r[1],r[2],r[3]&0xffffffff,r[4]&0xffffffff,r[5]))
    return out
if __name__=='__main__':
    for T in sys.argv[1:] or ['27.0','27.2','27.4','27.6','27.8','28.0']:
        d=pickle.load(open(f'golden/pf2/LNOUT_{T}.pkl','rb'))   # dump labelled with the next step: frame = T-0.2
        cap=collections.Counter((x[0],x[1],x[2],x[4]&0xffffffff,x[5]&0xffffffff,x[6]) for x in d)
        pr=collections.Counter(calls(float(T)-0.2))
        print(T,'captured',len(d),'predicted',sum(pr.values()),'exact',sum((cap&pr).values()))
