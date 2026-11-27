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
def code(c):
    x,y,z=c; nz=-z; b=0
    if nz>x: b|=1
    if x>z: b|=2
    if nz>y: b|=4
    if y>z: b|=8
    return b
def lerp(A,B,t):
    """0x329a0 camera part: t*B + (1-t)*A, float32 per op"""
    t=f32(t); o=f32(f32(1)-t)
    return tuple(f32(f32(t*B[k])+f32(o*A[k])) for k in range(3))
def clip(poly,fl):
    """0x32db0 polygon clipper: 4 Sutherland-Hodgman passes (x<-z, x>z, y<-z, y>z) over camera-space vertices; fl = edge flag bits.
    -> (poly, flags) or None if < 3 vertices left"""
    for m,ax,sg in ((1,0,-1),(2,0,1),(4,1,-1),(8,1,1)):
        out=[]; nf=0; n=len(poly)
        for i in range(n):
            a=poly[i]; b=poly[(i+1)%n]; ia=not code(a)&m; ib=not code(b)&m
            if ia:
                out.append(a); nf|=(fl>>i&1)<<(len(out)-1)
            if ia!=ib:
                if sg<0:
                    num=f32(-a[2]-a[ax]); den=f32(f32(b[ax]-a[ax])+f32(b[2]-a[2]))
                else:
                    num=f32(a[2]-a[ax]); den=f32(f32(b[ax]-a[ax])-f32(b[2]-a[2]))
                v=lerp(a,b,f32(num/den)); out.append(v); nf|=(fl>>i&1)<<(len(out)-1)
        poly=out; fl=nf
    return (poly,fl) if len(poly)>=3 else None
def calls(t,mode=1,info=None):
    """line calls in draw order: faces queued in list order into 4096 depth buckets (head insertion), buckets drawn 0..4095"""
    o,C,sx,sy=screen(t); F_=o['Tube03']['f']; ff=o['Tube03']['ff']
    q=[]
    for (a,b,cc),fl in zip(F_,ff):
        P=[tuple(f32(x) for x in C[k]) for k in (a,b,cc)]
        # 3D facing cull
        e=[f32(P[1][k]-P[0][k]) for k in range(3)]; d=[f32(P[2][k]-P[0][k]) for k in range(3)]
        n=(f32(f32(e[1]*d[2])-f32(d[1]*e[2])),f32(f32(e[2]*d[0])-f32(d[2]*e[0])),f32(f32(e[0]*d[1])-f32(d[0]*e[1])))
        dot=f32(f32(f32(n[1]*P[0][1])+f32(n[0]*P[0][0]))+f32(n[2]*P[0][2]))
        if dot<0: continue
        cs=[code(p) for p in P]
        if cs[0]&cs[1]&cs[2]: continue
        if cs[0]|cs[1]|cs[2]:
            r=clip(P,int(fl))
            if r is None: continue
            P,fl=r
        Cn=np.array(P,f32); X,Y=F.project(Cn); n=len(P)
        dep=f32(f32(f32(f32(P[0][2]+P[1][2])+P[2][2])*f32(1/3)))     # 0x340a0: (z0+z1+z2)*0.33333334
        v=f32(dep*f32(f32(4096)/f32(88000))); idx=int(np.rint(f32(f32(4095)-v) if mode==1 else v))
        out=[]
        for i in range(n):
            if fl>>i&1:
                r=te2rb_line.setup(X[i],Y[i],X[(i+1)%n],Y[(i+1)%n])
                if r: out.append((BASE+r[0],r[1],r[2],r[3]&0xffffffff,r[4]&0xffffffff,r[5]))
        q.append((idx,len(q),out))
        if info is not None: info.extend((c,idx,dep) for c in out)
    return [c for idx,i,out in sorted(q,key=lambda e:(e[0],-e[1])) for c in out if 0<=idx<4096]
if __name__=='__main__':
    for T in sys.argv[1:] or ['27.0','27.2','27.4','27.6','27.8','28.0']:
        d=pickle.load(open(f'golden/pf2/LNOUT_{T}.pkl','rb'))   # dump labelled with the next step: frame = T-0.2
        cap=collections.Counter((x[0],x[1],x[2],x[4]&0xffffffff,x[5]&0xffffffff,x[6]) for x in d)
        pr=collections.Counter(calls(float(T)-0.2))
        print(T,'captured',len(d),'predicted',sum(pr.values()),'exact',sum((cap&pr).values()))
