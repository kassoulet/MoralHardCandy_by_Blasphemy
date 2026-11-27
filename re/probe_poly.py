#!/usr/bin/env python3
"""probe_flow.py SNAP T0 T1 STEP OUT.pkl - trace the te2rb render 0x29da0: at every call site pre/post record regs + surface hashes/raw.
Run WITHOUT -I (unicorn). Same stepping as harness.py (pause flag, events fed, one main-loop iteration per step)."""
import sys,os,pickle,zlib,struct,time,hashlib,re
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import emucore as E
from unicorn import *
SNAP,T0,T1,STEP,OUT=sys.argv[1],float(sys.argv[2]),float(sys.argv[3]),float(sys.argv[4]),sys.argv[5]
st=pickle.load(open(SNAP+'.st','rb'))
mem=zlib.decompress(open(SNAP+'.mem','rb').read()); E.mu.mem_write(0,mem); del mem
E.mu.mem_write(E.GDT,st['gdt']); E.mu.mem_write(E.LDT,st['ldt'])
E.files.clear(); E.files.update({k:list(v) for k,v in st['files'].items()}); E.nextfd[0]=st['nextfd']; E.vectors.update(st['vectors'])
E.arena_ptr[0]=st['arena']; E.dosptr[0]=st['dosptr']; E.nextsel[0]=st['nextsel']; E.curmode[0]=st['curmode']; E.clk[0]=st['clk']; E.ports.update(st['ports'])
for r,v in st['regs'].items(): E.mu.reg_write(E.R(r),v)
LOOP=0x1dca7; TIME=0x10c7e8; PAUSE=0x10c7f0
def u32(a): return struct.unpack('<I',bytes(E.mu.mem_read(a,4)))[0]
hit=[0]; skip=[0]
def at_loop(uc,a,sz,_):
    if skip[0]: skip[0]=0; return
    uc.emu_stop()
E.mu.hook_add(UC_HOOK_CODE,at_loop,begin=LOOP,end=LOOP)
import json
ROWS=json.load(open(os.environ.get('ROWS',SNAP.rsplit('/',1)[0]+'/rows.json')))['rows']
SENT=0x1dcb1; fed=[0]; mode=['loop']
def at_sent(uc,a,sz,_):
    if mode[0]=='ev': uc.emu_stop()
E.mu.hook_add(UC_HOOK_CODE,at_sent,begin=SENT,end=SENT)
def feed(t):
    todo=[r for r in ROWS[fed[0]:] if r[2]<=t]
    for i in range(0,len(todo),128):
        for od,row,rt,_,_ in todo[i:i+128]:
            idx=u32(0x10d0ac); a=0x10c8ac+8*(idx&0xff)
            E.mu.mem_write(a,struct.pack('<II',(od<<8)|row,int(rt*1000)+u32(0x10d0b4))); E.mu.mem_write(0x10d0ac,struct.pack('<I',idx+1))
        E.mu.mem_write(0x112a60,struct.pack('<I',500)); E.mu.mem_write(0x112a68,struct.pack('<I',1193181))
        esp=E.ireg('ESP')-4; E.mu.mem_write(esp,struct.pack('<I',SENT)); E.mu.reg_write(E.R('ESP'),esp)
        mode[0]='ev'; E.mu.emu_start(0x1d800,0,count=100_000_000); mode[0]='loop'
        E.mu.reg_write(E.R('ESP'),esp+4); E.mu.reg_write(E.R('EIP'),LOOP)
    fed[0]+=len(todo)
def at_wait(uc,a,sz,_): uc.mem_write(0x10c7f8,struct.pack('<I',(u32(0x10c7f4)+1)&0xffffffff))
E.mu.hook_add(UC_HOOK_CODE,at_wait,begin=0x1d490,end=0x1d490)
# call sites of 0x29da0 (disassembly)
SITES=[int(m.group(1),16) for l in open(os.environ.get('DIS','/tmp/d.txt')) if (m:=re.match(r'\s*([0-9a-f]+):\tcall\s+0x',l))]
RES=[]; cur=[None]; LASTH={}
def surfs():
    """all surface objects we know: (name,ptr) -> raw bytes of w*h*4 (pitch applied)"""
    out={}
    for name,p in (('main',u32(0x10c7d4)),('p18',u32(u32(0x10c800 if False else 0x10c7d4)+0) if False else 0)):
        pass
    return out
OBJ=lambda p:(u32(p),u32(p+4),u32(p+8),u32(p+16))
def snapobj(p):
    try:
        w,h,pi,b=OBJ(p)
        if not(0<w<=1024 and 0<h<=1024 and 0<pi<=8192 and 0x1000000<b<0x6000000): return None
        return (w,h,pi,b,bytes(E.mu.mem_read(b,pi*h)))
    except Exception: return None
def mk(site,kind):
    def f(uc,a,sz,_):
        if cur[0] is None: return
        regs={r:E.ireg(r) for r in ('EAX','EBX','ECX','EDX','ESI','EDI','EBP','ESP')}
        esp=regs['ESP']; stk=[u32(esp+4*i) for i in range(8)]
        ob={}
        for r in ('EAX','EDX','ESI','EBX','EDI'):
            s=snapobj(regs[r]) if 0x1000<regs[r]<0x6000000 else None
            if s: ob[r]=s
        m=snapobj(u32(0x10c7d4))
        if m: ob['main']=m
        RES[-1]['ev'].append((hex(site),kind,regs,stk,ob))
    return f
import numpy as np
TRACE=set(round(float(x),2) for x in os.environ.get('TRACE','27.0').split(','))
T=[0]; PI=[]; PEND=[None]
BUF=0x402ffb8
def rd(a,n): return bytes(E.mu.mem_read(a,n))
def p_in(uc,a,sz,_):
    if round(T[0],2) not in TRACE: return
    it=E.ireg('EAX'); sp=E.ireg('ESP')
    d=dict(item=rd(it,0x80),itemp=it)
    nv=u32(it+12); va=u32(it+16); d['va']=va; d['vptrs']=[u32(va+4*k) for k in range(nv+2)]
    d['verts']=[rd(p,0x80) for p in d['vptrs'][:nv]]
    mat=u32(it+0x38); d['mat']=rd(mat,0x80); d['matp']=mat
    tex=u32(mat+0x18); d['tex']=rd(tex,0x40) if tex else None; d['texp']=tex
    d['pre']=rd(BUF,524288); d['spans']=[]; PEND[0]=d
def p_out(uc,a,sz,_):
    d=PEND[0]
    if d is None: return
    post=rd(BUF,524288); a0=np.frombuffer(d['pre'],np.uint32); a1=np.frombuffer(post,np.uint32)
    ix=np.nonzero(a0!=a1)[0]; d['chg']=(ix,a0[ix],a1[ix]); del d['pre']
    PI.append(dict(t=round(T[0],2),**d)); PEND[0]=None
def p_mid(uc,a,sz,_):
    if PEND[0] is None: return
    d=PEND[0]; d['verts2']=[rd(p,0x80) for p in d['vptrs'][:u32(d['itemp']+12)]]; d['mid']=dict(eax=E.ireg('EAX'),ecx=E.ireg('ECX'),edx=E.ireg('EDX'),st=[u32(E.ireg('ESP')+4*i) for i in range(0,200)])
E.mu.hook_add(UC_HOOK_CODE,p_mid,begin=0x40a63,end=0x40a63)
def span(uc,a,sz,_):
    if PEND[0] is None: return
    sp=E.ireg('ESP'); PEND[0]['spans'].append((a,u32(E.ireg('EAX')),[u32(sp+4*i) for i in range(10)]))
E.mu.hook_add(UC_HOOK_CODE,p_in,begin=0x40660,end=0x40660)
E.mu.hook_add(UC_HOOK_CODE,span,begin=0x83540,end=0x83540)
E.mu.hook_add(UC_HOOK_CODE,p_out,begin=0x365ea,end=0x365ea)
# TIMES=t1,t2,.. (env) overrides T0:T1:STEP; every time is stepped in order (the first must be <=26.2 start of the part)
TL=[float(x) for x in os.environ['TIMES'].split(',')] if 'TIMES' in os.environ else [T0+i*STEP for i in range(int((T1-T0)/STEP+1.0001))]
t0=time.time()
for t in TL:
    T[0]=t; feed(t); RES.append(dict(t=t,ev=[]))
    E.mu.mem_write(TIME,struct.pack('<d',t)); E.mu.mem_write(PAUSE,b'\x01'); skip[0]=1
    try: E.mu.emu_start(E.ireg('EIP'),0,count=400000000)
    except UcError as e: print('ERR',e); break
    cur[0]=None
    cp=u32(0x10c800); print('t=%.2f part idx %d events %d (%.0fs)'%(t,(cp-0x10c790)//4,len(RES[-1]['ev']),time.time()-t0),flush=True)
pickle.dump(PI,open(OUT,'wb'))
