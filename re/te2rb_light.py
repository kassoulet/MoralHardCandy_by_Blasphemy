#!/usr/bin/env python3
"""te2rb_light.py ../web/assets/te2rb.json [--write] - per-face light index of Tube03 (face +0x58), derived (lighting 0x347e0 as run by 0x366d0 at part init, light vector (1,0,0)):
  n = normalize((v2-v0) x (v1-v0))  (x87 extended; the engine's stored normal differs from this in the last float32 bit for ~1/3 of the faces, the index does not)
  d = ((nx*m0 + ny*m4) + nz*m8)  with the load-time Tube03 matrix column (m0,m4,m8) = (-4.371139e-8, 0, 1)  (Ry(-pi/2) built from float32 sin/cos; at 27 s the matrix is exact 0/+-1, and a re-run then gives
      128 instead of 127 on the 10 faces with nz == 0, which is how the matrix at load time was identified)
  idx = trunc(128 - 126*(pi/2 - acos(d))*(2/pi)) & 255, acos(d) = PIH - atan2(d, sqrt(1-d*d)) in extended precision (0x54ebc), PIH = 0xc90fdaa22168c000/2^63, d clamped to [-1,1].
Checked bit-identical on all 1704 faces against the engine's value (the 'li' key of the json, a dump of face+0x58). The colour ramp (256 dwords at material+0xc) is still a dump:
its builder runs during part init, before the boot snapshot, and was not traced (shape: 0x50 grey falling to 0x2b over idx 0..127, then 0x50 rising to 0xffda0a over 128..255)."""
import sys,json,base64,numpy as np
f=np.float32; Lg=np.longdouble
PIH=(Lg(0xc90fdaa2)*Lg(2)**32+Lg(0x2168c000))/Lg(2)**63
M0=Lg(f(-4.371139183945161e-08))
def idx(n):
    d=Lg(f((n[0]*M0+n[1]*0)+n[2]*1))     # 0x31690 stores the result as a dword, 0x347e0 re-reads it
    ac=Lg(0) if d>=1 else Lg(np.pi) if d<=-1 else PIH-np.arctan2(d,np.sqrt(1-d*d))
    return int(np.trunc(Lg(128)-(Lg(1.5707963267948966)-ac)*Lg(126)*Lg(0.6366197723675814)))&255
def tube_idx(j):
    V=np.frombuffer(base64.b64decode(j['tube']['v']),f).reshape(-1,3).astype(Lg); F=np.frombuffer(base64.b64decode(j['tube']['f']),np.uint16).reshape(-1,3)
    out=[]
    for a,b,c in F:
        e1=V[b]-V[a]; e2=V[c]-V[a]; x,y=e2,e1
        cr=np.array([x[1]*y[2]-x[2]*y[1],x[2]*y[0]-x[0]*y[2],x[0]*y[1]-x[1]*y[0]],Lg)
        n=(cr/np.sqrt((cr**2).sum())).astype(f).astype(Lg); out.append(idx(n))
    return np.array(out,np.uint8)
if __name__=='__main__':
    j=json.load(open(sys.argv[1])); li=tube_idx(j); ref=np.frombuffer(base64.b64decode(j['tube']['li']),np.uint8)
    print('face light indices differing from the engine dump: %d of %d'%(int((li!=ref).sum()),len(ref)))
    if '--write' in sys.argv: j['tube']['li']=base64.b64encode(li.tobytes()).decode(); json.dump(j,open(sys.argv[1],'w'),separators=(',',':'))
