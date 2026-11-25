"""te2rb wire-line setup: model of CANDYD.EXE 0x300a0 (no-clip path) -> args of the AA line inner loop 0x2ff80. Checked vs captured calls (probe_lines.py): 1974/2001 exact at t=27.8, using the engine's own screen vertices.
3DS face flags (0x4120 4th word) bits 0,1,2 = edges AB,BC,CA are drawn (exact match on 983 faces); only faces that are front-facing and fully inside the 512x256 view are queued.
"""
import numpy as np,math
f32=np.float32
PITCH=2048
def setup(x0,y0,x1,y1,w=512,h=256):
    """model of 0x300a0 (no-clip path). returns (addr_offset,count,frac,major,minor,slope) or None"""
    A,B,C,D=f32(x0),f32(y0),f32(x1),f32(y1)
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
