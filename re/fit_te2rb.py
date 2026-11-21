import m3ds,numpy as np,sys,os
from PIL import Image,ImageDraw,ImageFilter
S=os.environ['S']
o,t=m3ds.load(S+'/dat/te2rb.3ds')
V=o['Tube03']['v'].astype(float); F=o['Tube03']['f']
cp=sorted(t[(45059,'Camera02',45088)]); tp=sorted(t[(45060,'Camera02',45088)]); rl=sorted(t[(45059,'Camera02',45092)])
def interp(k,f):
    fr=np.array([a for a,_ in k],float); v=np.array([b for _,b in k],float)
    return np.array([np.interp(f,fr,v[:,i]) for i in range(v.shape[1])])
def view(f,fov,W=512,H=256):
    p=interp(cp,f); tg=interp(tp,f); roll=np.radians(interp(rl,f)[0])
    z=tg-p; z/=np.linalg.norm(z); x=np.cross(z,[0,0,1.]); x/=np.linalg.norm(x); y=np.cross(x,z)
    c,s=np.cos(roll),np.sin(roll); x,y=x*c+y*s,-x*s+y*c
    R=np.stack([x,y,z]); foc=(W/2)/np.tan(np.radians(fov)/2)
    return p,R,foc
def edges(f,fov,W=512,H=256):
    p,R,foc=view(f,fov,W,H); c=(V-p)@R.T
    ok=c[:,2]>1; sx=W/2+foc*c[:,0]/np.where(ok,c[:,2],1); sy=H/2-foc*c[:,1]/np.where(ok,c[:,2],1)
    im=Image.new('L',(W,H),0); d=ImageDraw.Draw(im)
    for a,b,cc in F:
        for i,j in ((a,b),(b,cc),(cc,a)):
            if ok[i] and ok[j]: d.line((sx[i],sy[i],sx[j],sy[j]),fill=255)
    return np.array(im)>0
def lines(path):
    g=Image.open(path).convert('L').crop((64,112,576,368)); a=np.array(g,float); b=np.array(g.filter(ImageFilter.BoxBlur(4)),float)
    return np.clip(a-b,0,None)
if __name__=='__main__':
    for T in [30,34,38,42,46,50]:
        L=lines(S+'/gold5/t%08.3f.png'%T); best=[]
        for fov in (94,122.6):
            for f in range(-480,1214,12):
                e=edges(f,fov); n=e.sum()
                if n<200: continue
                best.append((L[e].mean(),f,fov,n))
        best.sort(reverse=True); print(T,[(round(a,1),f,fv) for a,f,fv,n in best[:4]])
