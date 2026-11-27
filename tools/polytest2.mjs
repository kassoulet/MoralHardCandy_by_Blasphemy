// node tools/polytest2.mjs re/golden/poly   - our own polygon items (re/te2rb_poly.py) rendered by the recompiled 0x40660 vs the emulator's per-item changed pixels
import fs from 'fs';
import {poly} from '../web/poly_gen.js';
import {setupMem,SURF,spanFn,TEXB} from '../web/poly.js';
import {buildItem} from '../web/poly.js';
const dir=process.argv[2]||'re/golden/poly';
const L=JSON.parse(fs.readFileSync(dir+'/mine.json')); const tex=fs.readFileSync(dir+'/tex.bin');
const {m,mem}=setupMem(tex); const surf32=new Uint32Array(mem,SURF,512*256);
let bad=0,px=0; const perT={};
for(const P of L){
  surf32.fill(0); const item=buildItem(m,P.v); poly(m,item,0x1f0000,(m,id,a)=>spanFn(m,a));
  const [ix,post]=P.chg; const seen=new Set(ix); let b=0;
  for(let i=0;i<ix.length;i++) if(surf32[ix[i]]!==post[i]>>>0) b++;
  for(let i=0;i<surf32.length;i++) if(surf32[i]&&!seen.has(i)) b++;
  px+=ix.length; if(b) bad++; (perT[P.t]??=[0,0])[0]++; if(b)perT[P.t][1]++;
}
console.log(L.length,'items',px,'px,',bad,'items with differing pixels'); console.log(JSON.stringify(perT));
