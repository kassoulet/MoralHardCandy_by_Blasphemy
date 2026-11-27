"""Checks te2rb_f32 against engine captures (golden/cam/c_cam.pkl from probe_cam.py, golden/pf/LNOUT_f<t>.pkl from probe_faces.py): python3 -I te2rb_f32test.py"""
import sys,os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import pickle,struct,numpy as np,m3ds
import te2rb_f32 as F
f32=F.f32
f=lambda b:struct.unpack('<%df'%(len(b)//4),b)
M4=lambda b:np.array(f(b),f32).reshape(4,4)
R=pickle.load(open('golden/cam/c_cam.pkl','rb'))
o,_=m3ds.load('golden/dat/te2rb.3ds'); tt=o['Tube03']['m'][3]; V3=o['Tube03']['v']
E=F.engine_vertices(V3,tt); bad=0
for r in R:
    fr=f(r['f'])[0]
    pos=F.hermite(r['pk'][1],r['pk'][0],fr,3); tg=F.hermite(r['tk'][1],r['tk'][0],fr,3); rl=F.hermite(r['rk'][1],r['rk'][0],fr,1)
    V=F.view_matrix(pos,tg,rl[0]); assert (V==M4(r['ret'])).all(),('view',r['t'])
    b=r['mesh'][2][1]; assert (F.tube_matrix(f(b[0x23c:0x248]),V)==M4(b[0x110:0x150])).all(),('tube matrix',r['t'])
    T='%.1f'%(round(r['t']*5)/5+0.2); p='golden/pf2/LNOUT_f%s.pkl'%T   # probe_faces labels each dump with the NEXT step time (dump happens at the loop head)
    if not os.path.exists(p): continue
    faces,FV,ctx=pickle.load(open(p,'rb'))
    M=F.tube_matrix_p(f(b[0x23c:0x248]),V); assert (M==M4(b[0x150:0x190])).all(),'0x150'; C=F.xform(E,M); sx,sy=F.project(C)
    idx={tuple(E[i]):i for i in range(len(E))}; n=ok=oks=0
    for a,raw in FV.items():
        v=struct.unpack('<%df'%24,raw[:96]); i=idx.get(tuple(v[0:3]))
        if i is None: continue
        n+=1; ok+=tuple(C[i])==tuple(v[3:6]); oks+=(sx[i],sy[i])==(v[6],v[7])
    print(T,'camera/matrices exact; vertices matched',n,'cam exact',ok,'screen exact',oks)
