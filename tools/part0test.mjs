// node tools/part0test.mjs GOLDEN_RAW_DIR : part 1 (web/part0.js) vs the original's frames, along the stepped sequence t=0,0.2..26.4 (g%04d.rgb, 512x256 rgb, made by tools/mkgold.py).
// Exit 1 if a frame differs by more than 1 level or more than 300 bytes in total (x87 extended precision vs JS doubles can flip a trunc at a boundary: 246 bytes, off by 1, at t=16.6).
import fs from 'fs';import {renderPart0,W,H} from '../web/part0.js';
const zl=await import('zlib');const b=zl.inflateSync(fs.readFileSync(new URL('../web/assets/part0.bin',import.meta.url)));let o=0;const cut=n=>b.subarray(o,o+=n);
const A={bg:cut(W*H*3),logo:cut(300*90*4),box:cut(W*H*4),T:cut(96*256)};
let worst=0,bad=0,tot=0;for(let k=0;k<=132;k++){const t=k*0.2,r=renderPart0(new Uint8ClampedArray(W*H*4),t,A),g=fs.readFileSync(`${process.argv[2]}/g${String(k).padStart(4,'0')}.rgb`);
 let n=0,m=0;for(let p=0;p<W*H;p++)for(let c=0;c<3;c++){const d=Math.abs(r[p*4+c]-g[p*3+c]);if(d){n++;if(d>m)m=d;}}
 if(n){bad++;if(m>worst)worst=m;if(bad<6)console.log('t',t.toFixed(1),'differing bytes',n,'max',m);}tot+=n;}
console.log('frames',133,'frames with differences',bad,'bytes',tot,'max diff',worst);process.exit(worst>1||tot>300?1:0);
