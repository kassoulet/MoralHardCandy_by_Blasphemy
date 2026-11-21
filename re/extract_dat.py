#!/usr/bin/env python3
"""extract_dat.py CANDY.DAT OUTDIR - Blasphemy library file: [data XOR 0x2a][dir: n x {name[13], size u32, offset u32}][dir_off u32, n u32, 'OYZO'(xor'd 'EPMU'?)]"""
import sys,struct,os
d=open(sys.argv[1],'rb').read(); out=sys.argv[2]; os.makedirs(out,exist_ok=True)
do,n,mg=struct.unpack('<II4s',d[-12:]); assert mg==b'OYZO'
for i in range(n):
    e=d[do+21*i:do+21*i+21]; nm=e[:13].split(b'\0')[0].decode('latin1'); sz,of=struct.unpack('<II',e[13:])
    open(os.path.join(out,nm.lower()),'wb').write(bytes(b^0x2a for b in d[of:of+sz]))
print(n,'files')
