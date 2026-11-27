"""Draw the predicted (te2rb_wire.calls) and the captured line calls into empty 512x256 buffers; report pixel differences.
python3 -I te2rb_wiretest.py   (needs golden/ from probe_lines.py)"""
import sys,os,pickle,numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import te2rb_wire as W,te2rb_draw as D
ramp=[min(255,int(.25*i))*0x010101&0xfefeff for i in range(256)]
def render(cl):
    px=np.zeros(512*256,np.uint32)
    for a,n,fr,xs,ys,sl in cl:
        s=lambda v:v-(1<<32) if v>>31 else v
        D.draw(px,W.BASE,ramp,a,n,fr,s(xs),s(ys),sl)
    return px
for T in sys.argv[1:] or ['27.0','27.2','27.4','27.6','27.8','28.0']:
    d=pickle.load(open(f'golden/pf2/LNOUT_{T}.pkl','rb'))
    cap=[(x[0],x[1],x[2],x[4],x[5],x[6]) for x in d]
    a=render(W.calls(float(T)-0.2)); b=render(cap)
    df=a!=b
    ch=lambda p,s:(p>>s)&255
    mx=max(int(np.abs(ch(a,s).astype(int)-ch(b,s).astype(int)).max()) for s in (0,8,16))
    print(T,'px lit',int((b!=0).sum()),'differing px',int(df.sum()),'max channel diff',mx)
