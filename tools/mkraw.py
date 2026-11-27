#!/usr/bin/env python3
"""mkraw.py OUTDIR PNG... - crop the 512x256 surface out of the harness's 640x480 PNGs (offset 64,112) as raw RGB (tTTTT.TTT.rgb)."""
import sys,os
from PIL import Image
o=sys.argv[1]; os.makedirs(o,exist_ok=True)
for f in sys.argv[2:]: open(f'{o}/{os.path.basename(f)[:-4]}.rgb','wb').write(Image.open(f).convert('RGB').crop((64,112,576,368)).tobytes())
