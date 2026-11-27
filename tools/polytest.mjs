// node tools/polytest.mjs re/golden/poly   - te2rb polygon pass: recompiled 0x40660 + span 0x83540 vs the emulator capture (probe_poly.py -> export_poly.py)
import fs from 'fs';
import {poly,f32up} from '../web/poly_gen.js';
import {setupMem,SURF,spanFn,TEXB} from '../web/poly.js';
const dir=process.argv[2]||'re/golden/poly';
const J=JSON.parse(fs.readFileSync(dir+'/polys.json')); const tex=fs.readFileSync(dir+'/tex.bin');
const {m,mem}=setupMem(tex);
let badSpan=0,badPix=0,nspan=0,npoly=0,pixTot=0;
const b64=s=>Buffer.from(s,'base64');
for(const P of J.polys){
  const calls=[]; const surf32=new Uint32Array(mem,SURF,512*256); surf32.fill(0);
  const fn=(m,id,argp)=>{const a=[];for(let i=0;i<8;i++)a.push(m.getInt32(argp+4*i,true)); calls.push(a); spanFn(m,argp);};
  const item=setupItem(m,P);
  poly(m,item,0x1f0000,fn); npoly++;
  // spans: dst/tex relative to their bases
  let ok=calls.length==P.spans.length;
  for(let i=0;ok&&i<calls.length;i++){const c=calls[i],e=P.spans[i];
    const ex=[e[0]-J.surf+SURF,e[1]-J.texbuf+TEXB,e[2]|0,e[3]|0,e[4]|0,e[5]|0,e[6]|0,e[7]|0];
    for(let k=0;k<8;k++) if(c[k]!=ex[k]){ok=false; if(badSpan<5)console.log('poly',npoly-1,'span',i,'arg',k,c[k],ex[k]); break;}}
  nspan+=P.spans.length; if(!ok)badSpan++;
  // pixels
  let pb=0; const [ix,,post]=P.chg; const seen=new Set(ix);
  for(let i=0;i<ix.length;i++) if(surf32[ix[i]]!==post[i]>>>0) pb++;
  let nz=0; for(let i=0;i<surf32.length;i++) if(surf32[i]&&!seen.has(i)) nz++;
  pixTot+=ix.length; if(pb||nz){badPix++; if(badPix<5)console.log('poly',npoly-1,'pix diff',pb,'extra',nz,'of',ix.length);}
}
console.log(`${npoly} polys, ${nspan} spans: ${badSpan} polys with differing span calls, ${badPix} polys with differing pixels (${pixTot} px)`);
function setupItem(m,P){
  const ITEM=0x200000,VA=0x200100,VB=0x201000,MAT=0x203000,TEXO=0x203100,SO=0x203200,CTX=0x203300,X=0x203400,OBJ=0x203500;
  const w=(a,b)=>{for(let i=0;i<b.length;i++)m.setUint8(a+i,b[i]);};
  w(ITEM,b64(P.item)); w(MAT,b64(P.mat));
  for(let k=0;k<P.nv;k++){w(VB+0x80*k,b64(P.verts[k])); m.setInt32(VA+4*k,VB+0x80*k,true);}
  m.setInt32(ITEM+4,OBJ,true); m.setInt32(OBJ,1,true);
  m.setInt32(ITEM+0x10,VA,true); m.setInt32(ITEM+0x38,MAT,true); m.setInt32(ITEM+0x64,CTX,true);
  m.setInt32(CTX+0x48,X,true); m.setInt32(X+0xc,SO,true);
  m.setInt32(SO,512,true); m.setInt32(SO+4,256,true); m.setInt32(SO+8,2048,true); m.setInt32(SO+0x10,SURF,true);
  m.setInt32(MAT+0x18,TEXO,true); m.setInt32(TEXO,256,true); m.setInt32(TEXO+4,256,true); m.setInt32(TEXO+8,1024,true); m.setInt32(TEXO+0x10,TEXB,true);
  return ITEM;
}
