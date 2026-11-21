#!/usr/bin/env python3
"""mkpart0.py DATDIR BOOT.mem OUT - raw assets of part 1 (deflate): graybg rgb 512x256 | logo2 rgba 300x90 | mhcbox rgba 512x256 | blend table T[op][a], op<96 (the engine's 0x113328 table, copied from the memory snapshot)."""
import sys,zlib,struct,numpy as np
from PIL import Image
d,mem,out=sys.argv[1:4]
im=lambda n,m:np.array(Image.open(f'{d}/{n}.png').convert(m)).tobytes()
m=zlib.decompress(open(mem,'rb').read()); p=struct.unpack('<I',m[0x113328:0x11332c])[0]
open(out,'wb').write(zlib.compress(im('graybg','RGB')+im('logo2','RGBA')+im('mhcbox','RGBA')+m[p:p+96*256],9))
