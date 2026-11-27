"""te2rb_polyexport.py PKL OUT.json: our own polygon items (te2rb_poly.items) next to the captured per-item changed pixels, for tools/polytest2.mjs"""
import sys,os,pickle,json,struct,numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import te2rb_poly as P
PI=pickle.load(open(sys.argv[1],'rb')); L=[]
for T in sorted(set(p['t'] for p in PI)):
    cap=[p for p in PI if p['t']==T]; mine=P.items(T)
    for p,(idx,vs) in zip(cap,mine):
        L.append(dict(t=T,v=[[float(v['sx']),float(v['sy']),float(v['uz']),float(v['vz']),float(v['iz'])] for v in vs],
          chg=[p['chg'][0].tolist(),p['chg'][2].tolist()]))
json.dump(L,open(sys.argv[2],'w')); print(len(L))
