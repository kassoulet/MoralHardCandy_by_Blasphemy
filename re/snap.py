#!/usr/bin/env python3
"""snap.py OUT - boot CANDYD.EXE (unpacked image, emucore) through all asset loading to the main loop (0x1dca7)
and save a RAM snapshot + CPU/DOS state so harness.py can restart in seconds.
Run WITHOUT -I (unicorn). Slow: the whole PNG/JPEG/3DS decode runs under Unicorn (~12M insn/s)."""
import sys,time,pickle,zlib
sys.path.insert(0,__file__.rsplit('/',1)[0])
import emucore as E
from unicorn import *
OUT=sys.argv[1]; t0=time.time()
E.keybytes[:]=[0,0x50]*12+[13]     # MIDAS config menu: 12 x Down + Enter = 'No Sound'
LOOP=0x1dca7
def at_loop(uc,a,sz,_):
    print('main loop reached, t=%.0fs'%(time.time()-t0),flush=True)
    st=dict(regs={r:E.ireg(r) for r in ('EAX','EBX','ECX','EDX','ESI','EDI','EBP','ESP','EIP','EFLAGS','CS','DS','ES','SS','FS','GS')},
      files={k:list(v) for k,v in E.files.items()},nextfd=E.nextfd[0],vectors=dict(E.vectors),keybytes=list(E.keybytes),clk=E.clk[0],
      arena=E.arena_ptr[0],dosptr=E.dosptr[0],nextsel=E.nextsel[0],curmode=E.curmode[0],
      gdt=bytes(E.mu.mem_read(E.GDT,0x880)),ldt=bytes(E.mu.mem_read(E.LDT,512*8)),ports=dict(E.ports))
    open(OUT+'.mem','wb').write(zlib.compress(bytes(E.mu.mem_read(0,0x6000000)),1))
    pickle.dump(st,open(OUT+'.st','wb')); uc.emu_stop()
E.mu.hook_add(UC_HOOK_CODE,at_loop,begin=LOOP,end=LOOP)
pc=0x554ec
while True:
    E.mu.emu_start(pc,0,count=300_000_000); pc=E.ireg('EIP')
    print('t=%.0f'%(time.time()-t0),hex(pc),[(k,v[1]) for k,v in E.files.items()],flush=True)
    if pc==LOOP or time.time()-t0>7000: break
