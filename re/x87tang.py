#!/usr/bin/env python3
"""x87tang.py - run the engine's keyframe tangent code (0x37040 interior / 0x37230 first / 0x37300 last, listing in tang_x87.dis) as a tiny x87 interpreter
(every arithmetic result rounded to float32: x87 precision control = 24 bits). Used by te2rb_tang.py to derive the Camera02 tangents from the 3DS keys."""
import re,struct,numpy as np
f32=np.float32
CONST={0x102e5e:2.0,0x102e66:0.25,0x102e6e:0.5,0x102e72:3.0,0x102e76:2.0,0x102e7e:0.25,0x102e86:0.5,0x102e8a:3.0}   # read from the unpacked image
EXT=True   # x87 precision control at table build: extended (64-bit mantissa); only the dword stores round
SEC={}
for l in open(__file__.rsplit('/',1)[0]+'/tang_x87.dis'):
    if l.startswith(';'): cur=l.split()[1]; SEC[cur]=[]; continue
    m=re.match(r'\s*([0-9a-f]+):\s+(\w+)\s*(.*)',l)
    if m: SEC[cur].append((m.group(2),m.group(3).strip()))
def run(sec,keys,loc):
    """keys: dict reg->dict offset->float (frame at 0, xyz at 8/0xc/0x10, tcb at 0x84..0x8c); loc: initial locals"""
    st=[]; L=dict(loc)
    def addr(o):
        m=re.search(r'(?:DWORD|QWORD) PTR (?:ds:(0x[0-9a-f]+)|\[(\w+)(?:\+(0x[0-9a-f]+))?\])',o)
        if m.group(1): return ('c',int(m.group(1),16))
        return (m.group(2),int(m.group(3) or '0',16))
    def rd(o):
        r,off=addr(o)
        if r=='c': return np.longdouble(CONST[off])
        if r=='esp': return L[off]
        return np.longdouble(keys[r][off])
    def wr(o,v,sz):
        r,off=addr(o); v=float(f32(v)) if sz=='DWORD' else v
        (L if r=='esp' else keys[r])[off]=v
    R=lambda x: x if EXT else float(f32(x))
    sti=lambda s:int(re.search(r'st\((\d)\)',s).group(1)) if 'st(' in s else 0
    for op,args in SEC[sec]:
        a=[x.strip() for x in args.split(',')] if args else []
        if op=='fld1': st.insert(0,1.0)
        elif op=='fld':
            st.insert(0,st[sti(a[0])] if a[0].startswith('st') else rd(a[0]))
        elif op in('fst','fstp'):
            if a[0].startswith('st'):
                i=sti(a[0]); st[i]=st[0]
            else: wr(a[0],st[0],a[0].split()[0])
            if op=='fstp': st.pop(0)
        elif op=='fxch': i=sti(a[0]); st[0],st[i]=st[i],st[0]
        elif op in('fadd','fsub','fsubr','fmul','fdiv','fdivr'):
            if a[0].startswith('st'):
                if a[0]=='st': d=0;s=sti(a[1])           # st, st(i)
                else: d=sti(a[0]);s=0                    # st(i), st
                x,y=st[d],st[s]
            else: d=0; x=st[0]; y=rd(a[0])
            if op in('fsubr','fdivr'): x,y=y,x
            st[d]=R({'fadd':lambda:x+y,'fsub':lambda:x-y,'fsubr':lambda:x-y,'fmul':lambda:x*y,'fdiv':lambda:x/y,'fdivr':lambda:x/y}[op]())
        elif op in('faddp','fsubp','fsubrp','fmulp','fdivp','fdivrp'):
            d=sti(a[0]); x,y=st[d],st[0]                  # st(d) op= st0 (Intel SDM: fsubp x=st(d)-st0, fsubrp st0-st(d))
            if op.endswith('rp'): x,y=y,x
            v=(x+y if op=='faddp' else x*y if op=='fmulp' else x-y if 'sub' in op else x/y)
            st[d]=R(v); st.pop(0)
        elif op in('sub','add','ret','nop','lea','mov','pop','push'): pass
        else: raise Exception(op+' '+args)
    return st,L
def key(fr,p,tcb=(0.,0.,0.)):
    k={0:fr,8:p[0],0xc:p[1],0x10:p[2]}; k.update({0x84:tcb[0],0x88:tcb[1],0x8c:tcb[2]}); return k
def tangents(fr,P):
    """fr: frames, P: (n,3) float32 values -> (ti,to) arrays float32 (non-looping track, n>=3, tcb=0). Order as the driver 0x37490: first, interior, last."""
    n=len(fr);ti=np.zeros((n,3),f32);to=np.zeros((n,3),f32); K=[key(float(fr[i]),[float(x) for x in P[i]]) for i in range(n)]
    def take(k,o0): return [k[o0+4*c] for c in range(3)]
    run('first',{'edx':K[0],'ebx':K[1],'ecx':K[2]},{})
    to[0]=take(K[0],0x28)
    for i in range(1,n-1):
        run('interior',{'edx':K[i-1],'ebx':K[i],'ecx':K[i+1]},{0x44:K[i-1][0],0x48:K[i][0],0x4c:K[i+1][0]})
        ti[i]=take(K[i],0x18);to[i]=take(K[i],0x28)
    run('last',{'ecx':K[n-1],'ebx':K[n-2],'edx':K[n-3]},{})
    ti[n-1]=take(K[n-1],0x18)
    return ti,to
