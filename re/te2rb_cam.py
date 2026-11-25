"""te2rb camera, decoded from engine dumps (probe_faces.py) at t=27.0..28.0 (exact to float32 rounding).
frame f = 35*(t-26.7); pos/target/roll = Catmull-Rom (3DS default TCB=0, tangents scaled 2*d1/(d0+d1)) over the Camera02 keys.
Engine model coords = (t.y-V.y, V.z, V.x-t.x) (t = Tube03 0x4160 translation); camera-space = (P-pos_e) . R . diag(.25,.5,1)
  where R columns = camera x,y,z axes in model coords: z = normalize(target-pos), x/y = unrolled right/up rotated by -(roll mod 360) deg.
Screen: sx = 255.5+256*x/z, sy = 127.5-128*y/z."""
import numpy as np,m3ds
def cr(fr,v,f):
    i=min(max(np.searchsorted(fr,f)-1,1),len(fr)-3)
    p0,p1,p2,p3=v[i-1],v[i],v[i+1],v[i+2]; d0,d1,d2=fr[i]-fr[i-1],fr[i+1]-fr[i],fr[i+2]-fr[i+1]
    m1=0.5*((p1-p0)+(p2-p1))*2*d1/(d0+d1); m2=0.5*((p2-p1)+(p3-p2))*2*d1/(d1+d2); u=(f-fr[i])/d1
    return (2*u**3-3*u**2+1)*p1+(-2*u**3+3*u**2)*p2+(u**3-2*u**2+u)*m1+(u**3-u**2)*m2
def camera(t,path='dat/te2rb.3ds'):
    o,tr=m3ds.load(path); tt=o['Tube03']['m'][3].astype(float)
    K=lambda k:(lambda s:(np.array([a for a,_ in s],float),np.array([b for _,b in s],float)))(sorted(tr[k]))
    f=35*(t-26.7); p=cr(*K((45059,'Camera02',45088)),f); g=cr(*K((45060,'Camera02',45088)),f); roll=cr(*K((45059,'Camera02',45092)),f)[0]
    e=lambda w:np.array([tt[1]-w[1],w[2],w[0]-tt[0]])   # 3DS world -> engine model
    p,g=e(p),e(g); fw=g-p; fw/=np.linalg.norm(fw); r0=np.cross([0,1.,0],fw); r0/=np.linalg.norm(r0); u0=np.cross(fw,r0)
    a=np.radians(-(roll%360)); x=np.cos(a)*r0+np.sin(a)*u0; y=-np.sin(a)*r0+np.cos(a)*u0   # y = x rotated +90deg
    return p,np.stack([x,y,fw],1)
