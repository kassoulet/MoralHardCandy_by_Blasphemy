#!/usr/bin/env python3
"""mkgold.py GOLD_PNG_DIR WEBDIR RAWDIR : tNNN.NNN.png (640x480 letterboxed, from re/harness.py) -> web/assets/gold/gNNNN.webp (512x256) + raw rgb copies for tools/part0test.mjs"""
import sys,os,glob
from PIL import Image
src,web,raw=sys.argv[1:4]; os.makedirs(web,exist_ok=True); os.makedirs(raw,exist_ok=True)
for f in sorted(glob.glob(src+'/t*.png')):
    t=float(os.path.basename(f)[1:-4]); i=round(t/0.2); im=Image.open(f).convert('RGB').crop((64,112,576,368))
    im.save('%s/g%04d.webp'%(web,i),quality=78); open('%s/g%04d.rgb'%(raw,i),'wb').write(im.tobytes())
