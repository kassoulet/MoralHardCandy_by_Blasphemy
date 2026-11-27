"""te2rb wire-line setup: model of CANDYD.EXE 0x300a0 (no-clip path) -> args of the AA line inner loop 0x2ff80. Checked vs captured calls (probe_lines.py): 1974/2001 exact at t=27.8, using the engine's own screen vertices.
3DS face flags (0x4120 4th word) bits 0,1,2 = edges AB,BC,CA are drawn (exact match on 983 faces); only faces that are front-facing and fully inside the 512x256 view are queued.
"""
import numpy as np,math
f32=np.float32
PITCH=2048
def _cl(v,hi):
    v=f32(1) if v<=1 else v          # cmp bits,1.0 / jle
    return hi if v>=hi else v
def clip_line(A,B,C,D,w,h):
    """0x300a0 screen-rect clip (all float32): x endpoints outside [1,w-2] -> both x clamped, y re-derived from the line y=m*x+b;
    then the same for y with x=minv*y+b2 (x re-clamped). -> (x0,y0,x1,y1) or None (trivially rejected)"""
    hx,hy=f32(w-2),f32(h-2)
    f0=(4 if A<1 else 0)|(8 if A>hx else 0); f1=(4 if C<1 else 0)|(8 if C>hx else 0)
    if f0&f1: return None
    if (f0|f1)&12:
        m=f32(f32(D-B)/f32(C-A)); b=f32(B-f32(A*m))
        A1=_cl(A,hx); B1=f32(f32(A1*m)+b); C1=_cl(C,hx); D1=f32(f32(C1*m)+b)
        A,B,C,D=A1,B1,C1,D1
    f0=(1 if B<1 else 0)|(2 if B>hy else 0); f1=(1 if D<1 else 0)|(2 if D>hy else 0)
    if f0&f1: return None
    if (f0|f1)&3:
        mi=f32(f32(C-A)/f32(D-B)); b=f32(A-f32(B*mi))
        B1=_cl(B,hy); A1=_cl(f32(f32(mi*B1)+b),hx); D1=_cl(D,hy); C1=_cl(f32(f32(mi*D1)+b),hx)
        A,B,C,D=A1,B1,C1,D1
    return A,B,C,D
def setup(x0,y0,x1,y1,w=512,h=256):
    """model of 0x300a0: screen clip then DDA setup. returns (addr_offset,count,frac,major,minor,slope) or None"""
    A,B,C,D=f32(x0),f32(y0),f32(x1),f32(y1)
    r=clip_line(A,B,C,D,w,h)
    if r is None: return None
    A,B,C,D=r
    dx=f32(C-A); dy=f32(D-B)
    if 0>=dx: xs=-4; A=-A; C=-C
    else: xs=4
    if 0>=dy: ys=-PITCH; B=-B; D=-D
    else: ys=PITCH
    adx=abs(dx); ady=abs(dy)
    bound=h-2
    if ady>adx:
        adx,ady=ady,adx; xs,ys=ys,xs; A,B=B,A; C=D; bound=w-2
    if adx==0: return None
    sl=f32(ady/adx); s=float(sl)*4294967296.0
    slope=int(min(s,4294967295.0))
    ai=int(A); ci=int(C); cnt=ci-ai
    out=None
    while cnt>=0:
        v=f32(f32(f32(ai)-A)*sl+B); mi=int(v)
        if mi<0: mi-=1
        if 1<=abs(mi)<=bound: break
        ai+=1; cnt-=1
    if cnt<0: return None
    frac=int((float(v)-mi)*4294967296.0)&0xffffffff
    return (mi*ys+ai*xs,cnt,frac,xs,ys,slope)
