"""te2rb camera build exactly as the engine does it (0x36810 and callees).
KEY FINDING: the program runs with the x87 precision control at 24 bits (single), so every x87 result is rounded to float32
(+ - * / sqrt, fsin/fcos/fpatan too): plain float32 arithmetic op by op, in the order of the x87 stack code. Only the tbyte pi/2 at 0x10948c is wider.
Keys = engine key structs (stride 0x98: +0 frame, +8 pos xyz / value, +0x18 in-tangent xyz, +0x28 out-tangent xyz)."""
import numpy as np,struct
f32=np.float32
PIH=f32(1.5707963267948966)       # only used as pi/2 - asin(c) rounded to float32 below (the tbyte constant 0xc90fdaa22168c000/2^63)
PIH_EXT=float(int('c90fdaa22168c000',16))/2**63
def key_f(b,i): return struct.unpack_from('<f',b,i*0x98)[0]
def key_v(b,i,off,n=3): return struct.unpack_from('<%df'%n,b,i*0x98+off)
def hermite(b,n,f,comp):
    """0x379d0 (comp=3: pos/target) / 0x37ef0 (comp=1: roll) for a non-looping track, zero ease. f = float32 frame. -> tuple of float32"""
    fr=[key_f(b,i) for i in range(n)]; f=f32(f)
    if f<fr[0]: return key_v(b,0,8,comp)
    if f>=fr[-1]: return key_v(b,n-1,8,comp)
    i=0
    while i<n-2 and not (fr[i+1]>=f): i+=1
    u=f32(f32(f-f32(fr[i]))/f32(f32(fr[i+1])-f32(fr[i])))
    A=f32(u*u); B=f32(A*u); A2=f32(2*A); A3=f32(3*A); B2=f32(2*B)
    h2=f32(f32(-B2)+A3); h1=f32(f32(B2-A3)+f32(1)); h3=f32(f32(B-A2)+u); h4=f32(B-A)
    P0=key_v(b,i,8,comp); P1=key_v(b,i+1,8,comp); T0=key_v(b,i,0x28,comp); T1=key_v(b,i+1,0x18,comp)
    out=[]
    for c in range(comp):
        s=f32(f32(h2*f32(P1[c]))+f32(h1*f32(P0[c])))
        s=f32(s+f32(h3*f32(T0[c])))
        out.append(f32(s+f32(h4*f32(T1[c]))))
    return tuple(out)
def mat_id(): return np.eye(4,dtype=f32)
def mm(A,B):
    """0x3aa50: out[i][j] = ((A[i][0]B[0][j]+A[i][1]B[1][j])+A[i][2]B[2][j])+A[i][3]B[3][j]"""
    o=np.zeros((4,4),f32)
    for i in range(4):
        for j in range(4):
            p=[f32(A[i,k]*B[k,j]) for k in range(4)]
            o[i,j]=f32(f32(f32(p[0]+p[1])+p[2])+p[3])
    return o
def sincos(a): a=float(f32(a)); return f32(np.sin(a)),f32(np.cos(a))
def rz(a):
    s,c=sincos(a); m=mat_id(); m[0,0]=c;m[0,1]=s;m[1,0]=-s;m[1,1]=c; return m
def rx(a):
    s,c=sincos(a); m=mat_id(); m[1,1]=c;m[1,2]=s;m[2,1]=-s;m[2,2]=c; return m
def ry(a):
    s,c=sincos(a); m=mat_id(); m[0,0]=c;m[0,2]=-s;m[2,0]=s;m[2,2]=c; return m
def trans(x,y,z):
    m=mat_id(); m[3,0]=x;m[3,1]=y;m[3,2]=z; return m
def _asin(s):   # fpatan is not subject to the precision control: extended result (rounded by the caller's fstp / the following fsub)
    q=f32(np.sqrt(f32(f32(1)-f32(s*s)))); return np.arctan2(np.longdouble(s),np.longdouble(q))
def angles(p,t):
    """pitch, yaw (float32), yaw before the sign test"""
    px,py,pz=[f32(x) for x in p]; tx,ty,tz=[f32(x) for x in t]
    dx=f32(tx-px); dy=f32(ty-py); dz=f32(tz-pz)
    dy2=f32(dy*dy); dx2=f32(dx*dx); dz2=f32(dz*dz)
    Lq=f32(np.sqrt(f32(f32(dy2+dx2)+dz2))); H=f32(np.sqrt(f32(dz2+dx2)))
    pitch=f32(_asin(f32(dy/Lq))); c=f32(dz/H)
    yaw=f32(np.longdouble(PIH_EXT)-_asin(c))
    return pitch,yaw
def view(pos,tgt,roll):
    """0x36810 -> 4x4 float32 view matrix (row vectors, 3DS->engine already applied by the caller's key data)"""
    pitch,yaw=angles(pos,tgt)
    if f32(tgt[0])>f32(pos[0]): yaw=-yaw
    from fractions import Fraction as Fr   # fmul qword operand is a full double; the product is rounded straight to 24 bits
    R=f32(float(Fr(float(f32(f32(roll)*f32(2))))*Fr(3.141592653589793)))
    R=f32(float(Fr(float(R))*Fr(0.0027777777777777775)))
    return R,pitch,yaw
def view_matrix(pos,tgt,roll):
    """full 0x36810: ((T(-pos) * Ry(yaw)) * Rx(pitch)) * Rz(roll), float32"""
    R,pitch,yaw=view(pos,tgt,roll)
    m=mm(trans(-pos[0],-pos[1],-pos[2]),ry(yaw)); m=mm(m,rx(pitch)); return mm(m,rz(R))
def tube_world(t):
    """Tube03 node matrix (rows): rotation permuting the axes + node position t=(x,0,z) (0x4160 translation, float32)"""
    W=np.zeros((4,4),f32); W[0,2]=-1; W[1,1]=1; W[2,0]=1; W[3,0]=t[0]; W[3,1]=t[1]; W[3,2]=t[2]; W[3,3]=1; return W
def tube_matrix(t,V): return mm(tube_world(t),V)   # engine model xyz -> camera (0x32390: world * ctx+0x58)
def xform(P,M):
    """0x31690, vectorised: P (n,3) float32 model xyz, M 4x4 -> camera xyz: ((x*M0+y*M4)+z*M8)+M12, each op float32"""
    x,y,z=P[:,0],P[:,1],P[:,2]
    return np.stack([((((x*M[0,j]).astype(f32)+(y*M[1,j]).astype(f32)).astype(f32)+(z*M[2,j]).astype(f32)).astype(f32)+M[3,j]).astype(f32) for j in range(3)],1)
def project(C,cx=f32(255.5),cy=f32(127.5),kx=f32(256),ky=f32(128)):
    """0x33f70: sx = (kx*x)*(1/z)+cx ; sy = cy-(ky*y)*(1/z), each op float32"""
    iz=(f32(1)/C[:,2]).astype(f32)
    sx=((kx*C[:,0]).astype(f32)*iz).astype(f32)+cx
    sy=cy-((ky*C[:,1]).astype(f32)*iz).astype(f32)
    return sx.astype(f32),sy.astype(f32)
def engine_vertices(V3,t):
    """3DS vertices (n,3 float32) -> engine model coords (t.y-V.y, V.z, V.x-t.x), t = 0x4160 translation"""
    return np.stack([t[1]-V3[:,1],V3[:,2],V3[:,0]-t[0]],1).astype(f32)
def proj_matrix(a=f32(8),b=f32(4)):
    """0x3af80 via 0x36250: diag(2/ctx[0x24], 2/ctx[0x28], 1) = diag(0.25, 0.5, 1) (ctx+0x24=8, +0x28=4)"""
    m=mat_id(); m[0,0]=f32(f32(2)/a); m[1,1]=f32(f32(2)/b); return m
def tube_matrix_p(t,V):
    """Tube03 model -> scaled camera space (0x32390: obj+0x150 = world * (view*proj))"""
    return mm(tube_world(t),mm(V,proj_matrix()))
