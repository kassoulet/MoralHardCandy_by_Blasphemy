"""te2rb: literal model of the AA additive line inner loop 0x2ff80. Verified: 21596/21596 pixel writes of a captured frame (t=27.8) reproduce address and value (probe_px.py). ramp = 256 dwords, entry i = pack(trunc(g*i) per channel, clamp 255) & 0xfefeff (g=0.25 for all frames probed)."""
import numpy as np
M=0xffffffff
def sat(p,t):
    s=((p&0xfefeff)+t)&M; m=s&0x1010100; return (s|((m-(m>>7))&M))&M
def draw(px,base,ramp,eax,cnt,frac,xs,ys,slope):
    """px: np.uint32 array (index=(addr-base)/4). xs,ys: major/minor steps (bytes, signed). inner loop 0x2ff80 literal."""
    a=eax-base; ms=ys; n=cnt; fr=frac
    while True:
        w=fr>>24
        i=(a+ms)//4; px[i]=sat(int(px[i]),int(ramp[w]))
        i=a//4;      px[i]=sat(int(px[i]),int(ramp[~w&255]))
        n-=1
        if n<0: break
        fr+=slope; carry=fr>M; fr&=M
        a+=xs
        if carry: a+=ms
