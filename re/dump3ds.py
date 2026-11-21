#!/usr/bin/env python3
"""dump3ds.py FILE.3ds - chunk tree summary: objects (verts/faces), cameras, lights, materials, keyframer ranges"""
import sys,struct
d=open(sys.argv[1],'rb').read()
NAMES={0x4D4D:'MAIN',0x3D3D:'EDIT',0x4000:'OBJ',0x4100:'MESH',0x4110:'VERTS',0x4120:'FACES',0x4130:'MATREF',0x4140:'UV',0x4160:'XFORM',0x4600:'LIGHT',0x4700:'CAMERA',0xAFFF:'MATERIAL',0xA000:'MATNAME',0xA200:'TEXMAP',0xA300:'TEXFILE',0xB000:'KFDATA',0xB002:'KF_OBJ',0xB003:'KF_CAM',0xB004:'KF_TARGET',0xB005:'KF_LIGHT',0xB008:'KF_RANGE',0xB009:'KF_CURTIME',0xB010:'NODE_HDR',0xB020:'POS',0xB021:'ROT',0xB022:'SCL',0xB023:'FOV',0xB024:'ROLL',0xB030:'NODE_ID',0x0002:'VER',0x100:'MASTERSCALE'}
def walk(o,e,dep,mx):
    while o<e:
        cid,ln=struct.unpack_from('<HI',d,o)
        n=NAMES.get(cid,hex(cid)); body=o+6
        extra=''
        if cid in(0x4000,0xA000,0xA300,0xB010): 
            s=d[body:body+40].split(b'\0')[0].decode('latin1'); extra=repr(s)
            if cid==0xB010: 
                extra+=' flags'+str(struct.unpack_from('<HHH',d,body+len(s)+1))
        if cid==0x4110: extra=str(struct.unpack_from('<H',d,body)[0])+' verts'
        if cid==0x4120: extra=str(struct.unpack_from('<H',d,body)[0])+' faces'
        if cid==0xB008: extra=str(struct.unpack_from('<II',d,body))
        if cid in(0xB020,0xB021,0xB022,0xB023,0xB024):
            nk=struct.unpack_from('<H',d,body+10)[0]; extra=str(nk)+' keys'
        if cid in NAMES or dep<mx:
            if cid in(0x4110,0x4120,0x4140,0x4160) or cid in NAMES or True: print('  '*dep+n,hex(o),ln,extra)
        if cid in (0x4D4D,0x3D3D,0x4000,0x4100,0xB000,0xB002,0xB003,0xB004,0xB005,0xAFFF,0xA200,0x4700,0x4600):
            sub=body
            if cid==0x4000: sub=body+len(d[body:body+64].split(b'\0')[0])+1
            if cid==0x4700: sub=body+32; 
            if cid==0x4600: sub=body+12+0
            if cid in (0x4700,0x4600): 
                if cid==0x4700: print('  '*(dep+1),'cam pos/tgt/roll/fov',struct.unpack_from('<6f2f',d,body))
            else: walk(sub,o+ln,dep+1,mx)
        o+=ln
walk(0,len(d),0,2)
