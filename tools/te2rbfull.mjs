// node tools/te2rbfull.mjs [t1,t2,...] [rawdir] - full te2rb frame (web/te2rb.js 0x36250 pass + web/te2rbfx.js compositing) vs the emulator's golden surface (re/golden/raw/tTTTT.TTT.rgb, see tools/mkraw.py)
import fs from 'fs'; import zlib from 'zlib';
import {Te2rb} from '../web/te2rb.js'; import {parseFx,compose,state} from '../web/te2rbfx.js';
const ts=(process.argv[2]||'27,27.2,27.4,27.6,27.8').split(',').map(Number), dir=process.argv[3]||'re/golden/raw';
const d=JSON.parse(fs.readFileSync('web/assets/te2rb.json')),tex=fs.readFileSync('web/assets/te2rb_tex.bin');
const fx=parseFx(new Uint8Array(zlib.inflateSync(fs.readFileSync('web/assets/te2rb_fx.bin'))));
const T=new Te2rb(d,tex), surf=new Uint32Array(512*256);
// ACC=t0,step: use the harness' accumulated clock (t0+step+step... in doubles) for the render instead of the rounded name time
const acc=process.env.ACC&&process.env.ACC.split(',').map(Number),accT=n=>{let x=acc[0];for(let i=0;i<n;i++)x+=acc[1];return x;};
for(const tn of ts){ const t=acc?accT(Math.round((tn-acc[0])/acc[1])):tn;
  const t0=Date.now(); T.render(t,surf); const t1=Date.now(); compose(surf,t,fx,state(t)); const t2=Date.now();
  const g=fs.readFileSync(`${dir}/t${tn.toFixed(3).padStart(8,'0')}.rgb`); let bad=0,maxd=0,first=-1;
  for(let i=0;i<512*256;i++){const p=surf[i],r=p>>>16&255,gg=p>>>8&255,b=p&255,dd=Math.max(Math.abs(r-g[3*i]),Math.abs(gg-g[3*i+1]),Math.abs(b-g[3*i+2])); if(dd){bad++;if(first<0)first=i;maxd=Math.max(maxd,dd);}}
  console.log(`t=${tn}: ${bad} differing px (max diff ${maxd}${bad?`, first ${first%512},${first>>9}`:''}); render ${t1-t0} ms, compose ${t2-t1} ms`);
}
