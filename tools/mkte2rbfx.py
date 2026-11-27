#!/usr/bin/env python3
"""mkte2rbfx.py DATDIR BOOT.mem OUT - te2rb compositing assets (deflate): kasser rgba 512x256 | dna rgba 640x17 | offrun 218x218 indices | its palette (256 BGRX dwords, BGR of the PNG palette) | blend table T[256][256] (the engine's 0x113328)."""
import sys,zlib,struct,numpy as np
from PIL import Image
d,mem,out=sys.argv[1:4]
rgba=lambda n:np.array(Image.open(f'{d}/{n}.png').convert('RGBA')).tobytes()
o=Image.open(f'{d}/offrun.png'); pal=np.zeros((256,4),np.uint8); pp=np.array(o.getpalette()[:768],np.uint8).reshape(-1,3); pal[:len(pp),0]=pp[:,2]; pal[:len(pp),1]=pp[:,1]; pal[:len(pp),2]=pp[:,0]
m=zlib.decompress(open(mem,'rb').read()); p=struct.unpack('<I',m[0x113328:0x11332c])[0]
open(out,'wb').write(zlib.compress(rgba('kasser')+rgba('dna')+np.array(o).tobytes()+pal.tobytes()+m[p:p+65536],9))
