#!/usr/bin/env python3
"""probe_light.py SNAP T0 T1 STEP OUTDIR - harness.py, then re-run the load-time lighting 0x366d0 (-> 0x347e0 per Tube/Sphere face, light vector (1,0,0), see 0x291df) on the loaded scene and dump per call: the 4x4 matrix at 0x31690 (EBX), face normal in, vector out, face +0x58 -> re/golden/light.pkl.\nprobe_meshes.py SNAP T0 T1 STEP OUTDIR - harness.py plus: dump all faces of the three te2rb meshes (light index +0x58, normal, vertices) and the material colour table to /tmp/claude-1000/meshes.pkl (copy to re/golden/meshes.pkl).\nharness.py SNAP T0 T1 STEP OUTDIR - golden frames of the ORIGINAL CANDYD.EXE.

SNAP = file prefix made by snap.py (OUT.mem + OUT.st: state at the main loop 0x1dca7 after all assets are loaded).
The demo clock is the double at [0x10c7e8] (seconds). The program recomputes it from the PIT clock every iteration unless the pause flag
[0x10c7f0] ('p' key in the original) is set; we set the pause flag and write t ourselves, so frame(t) is exactly what the original draws at demo time t.
One main-loop iteration (0x1dc97 -> back) = one render. The 640x480 truecolor LFB (0x30000000) is dumped as PNG for t = T0, T0+STEP, ... (seconds).
Run WITHOUT -I (unicorn).  env: BPP (default 32: bytes per pixel 4, B G R X)"""
import sys,os,pickle,zlib,struct,time
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import emucore as E
from unicorn import *
import numpy as np
from PIL import Image
SNAP,T0,T1,STEP,OUT=sys.argv[1],float(sys.argv[2]),float(sys.argv[3]),float(sys.argv[4]),sys.argv[5]
os.makedirs(OUT,exist_ok=True)
st=pickle.load(open(SNAP+'.st','rb'))
mem=zlib.decompress(open(SNAP+'.mem','rb').read()); E.mu.mem_write(0,mem); del mem
E.mu.mem_write(E.GDT,st['gdt']); E.mu.mem_write(E.LDT,st['ldt'])
E.files.clear(); E.files.update({k:list(v) for k,v in st['files'].items()}); E.nextfd[0]=st['nextfd']; E.vectors.update(st['vectors'])
E.arena_ptr[0]=st['arena']; E.dosptr[0]=st['dosptr']; E.nextsel[0]=st['nextsel']; E.curmode[0]=st['curmode']; E.clk[0]=st['clk']; E.ports.update(st['ports'])
for r,v in st['regs'].items(): E.mu.reg_write(E.R(r),v)
LOOP=0x1dca7; TIME=0x10c7e8; PAUSE=0x10c7f0
iters=[0]
surf=[None]
def frame_png(t,name):
    # the demo renders into a 32bpp surface object (w,h,pitch,buf at +0,+4,+8,+0x10; 512x256) that 0x54d33 converts to the 24bpp LFB
    # (that final blit is broken in our emulation: its destination is garbage), so grab the source surface and letterbox it into 640x480
    w,h,p,buf=surf[0]; raw=bytes(E.mu.mem_read(buf,p*h)); a=np.frombuffer(raw,np.uint8).reshape(h,p)[:, :w*4].reshape(h,w,4)
    img=np.zeros((480,640,3),np.uint8); y0=(480-h)//2; x0=(640-w)//2; img[y0:y0+h,x0:x0+w]=a[:,:,2::-1]
    Image.fromarray(img).save(name)
def run_to_loop(maxn=2_000_000_000):
    # run until the next arrival at LOOP (hook stops the CPU)
    E.mu.emu_start(E.ireg('EIP'),0,count=maxn)
hit=[0]; skip=[0]
def at_loop(uc,a,sz,_):
    if skip[0]: skip[0]=0; return
    hit[0]+=1; uc.emu_stop()
E.mu.hook_add(UC_HOOK_CODE,at_loop,begin=LOOP,end=LOOP)
E.mu.mem_write(PAUSE,b'\x01')
import json
ROWS=json.load(open(os.environ.get('ROWS',SNAP.rsplit('/',1)[0]+'/rows.json')))['rows']
SENT=0x1dcb1; fed=[0]; mode=['loop']
def at_sent(uc,a,sz,_):
    if mode[0]=='ev': uc.emu_stop()
E.mu.hook_add(UC_HOOK_CODE,at_sent,begin=SENT,end=SENT)
def u32(a): return struct.unpack('<I',bytes(E.mu.mem_read(a,4)))[0]
def feed(t):
    """queue the music rows up to demo time t into the ring (what the MIDAS sync callback does), then let 0x1d800 consume them (no render)"""
    todo=[r for r in ROWS[fed[0]:] if r[2]<=t]
    for i in range(0,len(todo),128):
        for od,row,rt,_,_ in todo[i:i+128]:
            idx=u32(0x10d0ac); a=0x10c8ac+8*(idx&0xff)
            E.mu.mem_write(a,struct.pack('<II',(od<<8)|row,int(rt*1000)+u32(0x10d0b4))); E.mu.mem_write(0x10d0ac,struct.pack('<I',idx+1))
        E.mu.mem_write(0x112a60,struct.pack('<I',500)); E.mu.mem_write(0x112a68,struct.pack('<I',1193181))   # clock = 500 s: every event is due
        esp=E.ireg('ESP')-4; E.mu.mem_write(esp,struct.pack('<I',SENT)); E.mu.reg_write(E.R('ESP'),esp)
        mode[0]='ev'; E.mu.emu_start(0x1d800,0,count=100_000_000); mode[0]='loop'
        E.mu.reg_write(E.R('ESP'),esp+4); E.mu.reg_write(E.R('EIP'),LOOP)
    fed[0]+=len(todo); print('fed',fed[0],flush=True)
def at_wait(uc,a,sz,_):   # 0x1d400 spins until the timer ISR bumps [0x10c7f8]: do it for it
    uc.mem_write(0x10c7f8,struct.pack('<I',(u32(0x10c7f4)+1)&0xffffffff))
E.mu.hook_add(UC_HOOK_CODE,at_wait,begin=0x1d490,end=0x1d490)
def hb(uc,a,sz,_):
    d=E.ireg('EBP'); surf[0]=(u32(d),u32(d+4),u32(d+8),u32(d+16))
E.mu.hook_add(UC_HOOK_CODE,hb,begin=0x54d51,end=0x54d51)
OBJ=[0]
MESH=[]
def hm(uc,a,sz,_):
    o=E.ireg('EAX')
    if o not in MESH: MESH.append(o)
E.mu.hook_add(UC_HOOK_CODE,hm,begin=0x32640,end=0x32640)
def h29(uc,a,sz,_): OBJ[0]=E.ireg('EAX')
E.mu.hook_add(UC_HOOK_CODE,h29,begin=0x29da0,end=0x29da0)
t=T0; t0=time.time()
# first call returns immediately (hook fires at the start address): step once
while t<=T1+1e-9:
    feed(t)
    E.mu.mem_write(TIME,struct.pack('<d',t)); E.mu.mem_write(PAUSE,b'\x01')
    hit[0]=0
    # execute one full iteration: leave LOOP, come back
    skip[0]=1
    try: E.mu.emu_start(E.ireg('EIP'),0,count=int(os.environ.get('CNT','400000000')))
    except UcError as e: print('ERR',e,hex(E.ireg('EIP'))); break
    cp=u32(0x10c800); print('cur part',hex(cp),'idx',(cp-0x10c790)//4,'flags',[hex(x) for x in bytes(E.mu.mem_read(u32(cp)+0xc,2))])
    frame_png(t,'%s/t%08.3f.png'%(OUT,t)); print('t=%.3f  eip=%x  (%.0fs host)'%(t,E.ireg('EIP'),time.time()-t0),flush=True)
    t+=STEP

P=OBJ[0]; root=u32(P+0x3c); print('part',hex(P),'root',hex(root))
LOG=[]; cur={}
def h31(uc,a,sz,_):
    cur['m']=struct.unpack('<16f',bytes(E.mu.mem_read(E.ireg('EBX'),64))); cur['in']=struct.unpack('<3f',bytes(E.mu.mem_read(E.ireg('EAX'),12))); cur['out']=E.ireg('EDX'); cur['idx0']=u32(E.ireg('EAX')-0x14+0x58); cur['n0']=struct.unpack('<3f',bytes(E.mu.mem_read(E.ireg('EAX'),12)))
E.mu.hook_add(UC_HOOK_CODE,h31,begin=0x31690,end=0x31690)
def h3b(uc,a,sz,_):   # after 0x31690 returns (0x348b3): the out vector is at [esp+0xd0]
    e=E.ireg('ESP'); cur['v']=struct.unpack('<3f',bytes(E.mu.mem_read(e+0xd0,12))); cur['L']=struct.unpack('<3f',bytes(E.mu.mem_read(E.ireg('EBP')+0x1c,12)))
E.mu.hook_add(UC_HOOK_CODE,h3b,begin=0x348b3,end=0x348b3)
def h4(uc,a,sz,_):   # 0x349cc: face idx store, EDX = face, EAX = idx
    cur['face']=E.ireg('EDX'); cur['idx']=E.ireg('EAX'); LOG.append(dict(cur))
E.mu.hook_add(UC_HOOK_CODE,h4,begin=0x349cc,end=0x349cc)
RET=0x1dca7
esp=E.ireg('ESP')-0x100
for v in (0,0,0,0x3f800000)[::-1]: pass
args=[0x3f800000,0,0,0]   # pushed 0,0,0,1.0: [esp+4..] = 1.0,0,0,0
esp-=4*4
for i,v in enumerate(args): E.mu.mem_write(esp+4+4*i,struct.pack('<I',v))
E.mu.mem_write(esp,struct.pack('<I',RET)); E.mu.reg_write(E.R('ESP'),esp); E.mu.reg_write(E.R('EAX'),root)
skip[0]=0
import emucore
try: E.mu.emu_start(0x366d0,RET,count=200_000_000)
except UcError as e: print('ERR',e,hex(E.ireg('EIP')),{r:hex(E.ireg(r)) for r in ('EAX','EBX','ECX','EDX','ESI','EDI','ESP','EBP')},len(LOG))
print('calls',len(LOG))
pickle.dump(LOG,open('golden/light.pkl','wb'))
