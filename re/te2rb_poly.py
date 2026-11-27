"""te2rb textured polygon items (Sphere01 dome, the 0x40660 items) from the raw 3DS, float32 like the engine.
Same pipeline as the wire pass (te2rb_wire.py): 0x31690 transform, 3D facing cull, outcodes, 4-plane clipper (0x329a0 also interpolates uv at +0x38),
0x33f70 projection, 0x34010 (iz=f32(0.01/z) at +0x50, u*iz, v*iz at +0x40/+0x44), depth bucket (0x340a0/0x36530).
Engine model coords of Sphere01: f32((V-t)@R^T) computed in DOUBLE (verified bit-exact), axes (x,z,y); node matrix W (0xd0 in the engine object) = quaternion rotation, constant bits below.
Check: python3 -I te2rb_polytest.py (needs golden/poly/pall.pkl from probe_poly.py)"""
import numpy as np,sys,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import m3ds,te2rb_f32 as F,te2rb_wire as W
f32=np.float32
K=f32(0.01)      # [model+0x30]
WSPH=np.array([[1065353216,859553069,3007036721,0],[859553071,3212836864,867941678,0],[3007036719,3015425326,3212836864,0],[0,0,0,1065353216]],np.uint32).view(f32)
_S=None
def sphere(path='golden/dat/te2rb.3ds'):
    global _S
    if _S is None:
        o,_=m3ds.load(path); s=o['Sphere01']; R=s['m'][:3].astype(float); t=s['m'][3].astype(float)
        L=(s['v'].astype(float)-t)@R.T
        uv=np.stack([s['uv'][:,0],f32(1)-s['uv'][:,1]],1).astype(f32)    # v flipped (1-v)
        _S=(np.stack([L[:,0],L[:,2],L[:,1]],1).astype(f32),uv,s['f'])
    return _S
def view(t):
    pk,tk,rk=W.keys(); f=W.frame(t)
    pos=F.hermite(pk[1],pk[0],f,3); tg=F.hermite(tk[1],tk[0],f,3); rl=F.hermite(rk[1],rk[0],f,1)
    return F.view_matrix(pos,tg,rl[0])
def lerpv(A,B,t):
    """0x329a0: cam and uv = f32(t*B)+f32((1-t)*A)"""
    t=f32(t); o=f32(f32(1)-t)
    return (tuple(f32(f32(t*B[0][k])+f32(o*A[0][k])) for k in range(3)),tuple(f32(f32(t*B[1][k])+f32(o*A[1][k])) for k in range(2)))
def clip(poly):
    for m,ax,sg in ((1,0,-1),(2,0,1),(4,1,-1),(8,1,1)):
        out=[]; n=len(poly)
        for i in range(n):
            a=poly[i]; b=poly[(i+1)%n]; ia=not W.code(a[0])&m; ib=not W.code(b[0])&m
            if ia: out.append(a)
            if ia!=ib:
                A,B=a[0],b[0]
                if sg<0: num=f32(-A[2]-A[ax]); den=f32(f32(B[ax]-A[ax])+f32(B[2]-A[2]))
                else: num=f32(A[2]-A[ax]); den=f32(f32(B[ax]-A[ax])-f32(B[2]-A[2]))
                out.append(lerpv(a,b,f32(num/den)))
        poly=out
    return poly if len(poly)>=3 else None
def items(t):
    """polygon items in draw order: list of (bucket idx, [vertex dict: sx sy iz uz vz cam uv])"""
    E,UV,FA=sphere(); V=view(t); M=F.mm(WSPH,F.mm(V,F.proj_matrix())); C=F.xform(E,M)
    q=[]
    for a,b,c in FA:
        P=[(tuple(f32(x) for x in C[k]),tuple(UV[k])) for k in (a,b,c)]
        e=[f32(P[1][0][k]-P[0][0][k]) for k in range(3)]; d=[f32(P[2][0][k]-P[0][0][k]) for k in range(3)]
        n=(f32(f32(e[1]*d[2])-f32(d[1]*e[2])),f32(f32(e[2]*d[0])-f32(d[2]*e[0])),f32(f32(e[0]*d[1])-f32(d[0]*e[1])))
        p0=P[0][0]; dot=f32(f32(f32(n[1]*p0[1])+f32(n[0]*p0[0]))+f32(n[2]*p0[2]))
        if dot<0: continue
        cs=[W.code(p[0]) for p in P]
        if cs[0]&cs[1]&cs[2]: continue
        if cs[0]|cs[1]|cs[2]:
            P=clip(P)
            if P is None: continue
        Cn=np.array([p[0] for p in P],f32); X,Y=F.project(Cn)
        dep=f32(f32(f32(f32(P[0][0][2]+P[1][0][2])+P[2][0][2])*f32(1/3)))
        idx=int(np.rint(f32(f32(4095)-f32(dep*f32(f32(4096)/f32(88000))))))
        vs=[]
        for i,p in enumerate(P):
            iz=f32(K/p[0][2]); vs.append(dict(sx=X[i],sy=Y[i],iz=iz,uz=f32(iz*p[1][0]),vz=f32(iz*p[1][1]),cam=p[0],uv=p[1]))
        q.append((idx,len(q),vs))
    return [(idx,vs) for idx,i,vs in sorted(q,key=lambda e:(e[0],-e[1])) if 0<=idx<4096]
