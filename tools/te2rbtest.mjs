// node tools/te2rbtest.mjs re/golden/poly   - web/te2rb.js (float32 scene) vs captures: wire line calls (wirecap.json) and polygon items (mine.json = emulator-verified te2rb_poly)
import fs from 'fs';
import {Te2rb,setWireLog} from '../web/te2rb.js';
const dir=process.argv[2]||'re/golden/poly';
const d=JSON.parse(fs.readFileSync('web/assets/te2rb.json')),tex=fs.readFileSync('web/assets/te2rb_tex.bin');
const T=new Te2rb(d,tex); const surf=new Uint32Array(512*256);
const cap=JSON.parse(fs.readFileSync(dir+'/wirecap.json')),mine=JSON.parse(fs.readFileSync(dir+'/mine.json'));
const BASE=0x402ffb8;
for(const t of Object.keys(cap)){
  const log=[]; setWireLog(log); const t0=Date.now(); T.render(parseFloat(t),surf); setWireLog(null);
  const mk=r=>[BASE+r.a,r.cnt,r.frac,r.xs>>>0,r.ys>>>0,r.slope].join();
  const c=cap[t].map(x=>x.join()), p=log.map(mk);
  const same=c.length==p.length&&c.every((x,i)=>x===p[i]);
  // polygon items
  const it=T.items(parseFloat(t)).filter(e=>e.kind); const mt=mine.filter(m=>m.t==parseFloat(t));
  const ps=it.length==mt.length&&it.every((e,i)=>e.vs.every((v,k)=>v.sx==mt[i].v[k][0]&&v.sy==mt[i].v[k][1]&&v.uz==mt[i].v[k][2]&&v.vz==mt[i].v[k][3]&&v.iz==mt[i].v[k][4]));
  console.log(`t=${t}: wire calls captured ${c.length} mine ${p.length} identical-in-order=${same}; polygons ${it.length}/${mt.length} identical=${ps}; ${Date.now()-t0} ms`);
}
