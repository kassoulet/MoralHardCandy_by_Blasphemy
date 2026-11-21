"""m3ds.py - minimal 3DS reader (meshes + camera keyframes) used to fit/port the keyframe player."""
import struct,numpy as np
C=(0x4D4D,0x3D3D,0x4000,0x4100,0xB000,0xB002,0xB003,0xB004)
def load(path):
    d=open(path,'rb').read(); objs={}; cam=None; tracks={}
    def walk(o,e):
        while o<e:
            cid,ln=struct.unpack_from('<HI',d,o)
            if ln<6: break
            yield cid,o,ln
            if cid==0x4000: yield from walk(d.index(b'\0',o+6)+1,o+ln)
            elif cid in C: yield from walk(o+6,o+ln)
            o+=ln
    cur=None; node=None
    for cid,o,ln in walk(0,len(d)):
        if cid==0x4000: cur=d[o+6:d.index(b'\0',o+6)].decode(); objs[cur]={}
        elif cid==0x4110:
            n,=struct.unpack_from('<H',d,o+6); objs[cur]['v']=np.frombuffer(d,'<f4',n*3,o+8).reshape(n,3).copy()
        elif cid==0x4120:
            n,=struct.unpack_from('<H',d,o+6); objs[cur]['f']=np.frombuffer(d,'<u2',n*4,o+8).reshape(n,4)[:,:3].copy()
        elif cid==0x4140:
            n,=struct.unpack_from('<H',d,o+6); objs[cur]['uv']=np.frombuffer(d,'<f4',n*2,o+8).reshape(n,2).copy()
        elif cid==0x4160: objs[cur]['m']=np.frombuffer(d,'<f4',12,o+6).reshape(4,3).copy()
        elif cid==0x4700: objs[cur]['cam']=struct.unpack_from('<8f',d,o+6)
        elif cid in (0xB003,0xB004,0xB002): node=(cid,None)
        elif cid==0xB010: node=(node[0],d[o+6:d.index(b'\0',o+6)].decode())
        elif cid in (0xB020,0xB021,0xB023,0xB024) and ln>=20:
            n,=struct.unpack_from('<I',d,o+16); q=o+20; keys=[]
            nv={0xB020:3,0xB021:4,0xB023:1,0xB024:1}[cid]
            for k in range(n):
                fr,kf=struct.unpack_from('<Ii',d,q) if False else (struct.unpack_from('<i',d,q)[0],struct.unpack_from('<H',d,q+4)[0]); q+=6
                nf=bin(kf&0x1f).count('1'); q+=4*nf
                keys.append((fr,struct.unpack_from('<%df'%nv,d,q))); q+=4*nv
            tracks[(node[0],node[1],cid)]=keys
    return objs,tracks
