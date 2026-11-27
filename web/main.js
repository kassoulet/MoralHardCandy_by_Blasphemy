// main.js - storyboard stage: music (libopenmpt via chiptune3) + the golden frames captured from the original, pause/seek on the music clock.
const $=id=>document.getElementById(id), cvs=$('c'), ctx=cvs.getContext('2d'), sk=$('seek');
const fmt=s=>Math.floor(s/60)+':'+String(Math.floor(s%60)).padStart(2,'0');
let frames=[], imgs=[], dur=259.74, playing=false, tBase=0, wall0=0, cp=null, ac=null, buf=null, started=false, last=-1;
const now=()=>performance.now()/1000, cur=()=>playing?Math.min(dur,tBase+(now()-wall0)):tBase;
let parts=[]; try{ const j=await (await fetch('assets/parts.json')).json(); parts=j.parts; dur=j.length; sk.max=Math.round(dur*10); }catch(e){}
// Golden frames: what the ORIGINAL CANDYD.EXE drew (512x256 surface, captured under emulation every 0.2 s, see re/harness.py), letterboxed in 512x384.
// parts.json = the original's 14-part table at music times.
const STEP=0.2, cache=new Map(), urls=new Map();   // urls: frame index -> blob URL of the preloaded file
const frameAt=i=>{ let im=cache.get(i); if(!im){ im=new Image(); im.src=urls.get(i)||'assets/gold/g'+String(i).padStart(4,'0')+'.webp'; im.decode().catch(()=>{}); cache.set(i,im); if(cache.size>400) cache.delete(cache.keys().next().value); } return im; };
import {renderPart0,loadPart0,W as PW,H as PH} from './part0.js';
let shown=-1, A0=null, lastT=-1; const js=$('js'), buf0=new Uint8ClampedArray(PW*PH*4), id0=new ImageData(buf0,PW,PH);
try{ A0=await loadPart0('assets/part0.bin'); }catch(e){ js.disabled=true; }
// Part 2 (te2rb, 26.5-56 s) in JS: 0x36250 pass (te2rb.js + recompiled poly_gen/fill_gen) + compositing (te2rbfx.js, flash via stretch_gen). Pure function of t, ~10 ms/frame.
let T2=null, S2=null, FX2=null, st2=null; const buf2=new Uint8ClampedArray(PW*PH*4), id2=new ImageData(buf2,PW,PH), surf2=new Uint32Array(PW*PH);
const infl=async u=>new Uint8Array(await new Response((await fetch(u)).body.pipeThrough(new DecompressionStream('deflate'))).arrayBuffer());
(async()=>{ try{ const [{Te2rb},fxm]=await Promise.all([import('./te2rb.js'),import('./te2rbfx.js')]);
  const [d,tex,fx]=await Promise.all([fetch('assets/te2rb.json').then(r=>r.json()),fetch('assets/te2rb_tex.bin').then(r=>r.arrayBuffer()),infl('assets/te2rb_fx.bin')]);
  T2=new Te2rb(d,new Uint8Array(tex)); FX2=fxm.parseFx(fx); S2=fxm; }catch(e){ console.warn('te2rb port unavailable, golden frames used',e); } })();
function renderTe2rb(t){ T2.render(t,surf2); S2.compose(surf2,t,FX2,S2.state(t));
  for(let i=0;i<surf2.length;i++){ const p=surf2[i]; buf2[4*i]=p>>>16; buf2[4*i+1]=p>>>8; buf2[4*i+2]=p; buf2[4*i+3]=255; } }
js.onchange=()=>{ shown=-1; };
function draw(){
  const t=cur(), i=Math.min(Math.floor(dur/STEP),Math.floor(t/STEP)), p=parts.find(p=>t>=p.t0&&t<p.t1)||parts[parts.length-1];
  for(let k=1;k<=5;k++) frameAt(i+k);
  if(js.checked&&A0&&t<26.5){ if(shown!==-2||t!==lastT){ renderPart0(buf0,t,A0); ctx.fillStyle='#000'; ctx.fillRect(0,0,512,384); ctx.putImageData(id0,0,64); shown=-2; lastT=t; } }
  else if(js.checked&&T2&&t>=26.5&&t<56){ if(shown!==-3||t!==lastT){ renderTe2rb(t); ctx.fillStyle='#000'; ctx.fillRect(0,0,512,384); ctx.putImageData(id2,0,64); shown=-3; lastT=t; } } else {
  const im=frameAt(i);
  if(im.complete&&im.naturalWidth&&shown!==i){ ctx.fillStyle='#000'; ctx.fillRect(0,0,512,384); ctx.drawImage(im,0,64); shown=i; } }
  $('msg').textContent=p?'part '+(p.i+1)+'/'+parts.length+'  '+(partfiles[p.i]||[]).join(' '):'';
  $('tm').textContent=fmt(t)+' / '+fmt(dur); if(!sk.matches(':active')) sk.value=Math.round(t*10);
  requestAnimationFrame(draw);
}
let partfiles=[]; try{ partfiles=(await (await fetch('assets/partfiles.json')).json()).map(o=>o.files); }catch(e){}
async function start(){
  if(started) return; started=true; $('msg').textContent='';
  const {ChiptuneJsPlayer}=await import('./vendor/chiptune3.js');
  ac=new AudioContext(); cp=new ChiptuneJsPlayer({context:ac,repeatCount:0,interpolationFilter:8});cp.gain.connect(ac.destination);
  await new Promise(r=>cp.onInitialized(r));
  buf=await (await fetch('assets/7kingsi2.xm')).arrayBuffer(); cp.play(buf); playing=true; tBase=0; wall0=now(); $('pp').textContent='Pause';
}
function seek(t){ t=Math.max(0,Math.min(dur-0.01,t)); tBase=t; wall0=now(); cp&&cp.setPos(t); shown=-1; }
async function toggle(){
  if(!started) return ready&&start();
  if(playing){ cp.pause(); tBase=cur(); playing=false; $('pp').textContent='Play'; }
  else { cp.unpause(); wall0=now(); playing=true; ac.resume(); $('pp').textContent='Pause'; }
}
$('pp').onclick=toggle; $('b5').onclick=()=>seek(cur()-5); $('f5').onclick=()=>seek(cur()+5);
sk.oninput=()=>seek(sk.value/10);
$('fs').onclick=()=>$('stage').requestFullscreen&&$('stage').requestFullscreen();
addEventListener('keydown',e=>{ if(e.target.tagName==='BUTTON'&&e.key===' ') return;
  if(e.key==='p'||e.key===' '){ e.preventDefault(); toggle(); }
  else if(e.key==='ArrowLeft'||e.key==='ArrowRight'){ e.preventDefault(); seek(cur()+(e.key==='ArrowLeft'?-1:1)*(e.shiftKey?10:5)); }
  else if(e.key==='Home') seek(0); else if(e.key==='f') $('fs').click(); });
requestAnimationFrame(draw);
// preload every golden frame (1274 webp, 23 MB) before playback can start, so nothing is fetched while the music plays (the draw loop only keeps its 5-frame decode lookahead)
let ready=false, nl=0; const NF=Math.floor(dur/STEP)+1, ppTxt=$('pp').textContent; $('pp').textContent='Loading 0/'+NF+'...';
(async()=>{ let next=0; const worker=async()=>{ while(next<NF){ const i=next++; try{ const r=await fetch('assets/gold/g'+String(i).padStart(4,'0')+'.webp'); if(r.ok) urls.set(i,URL.createObjectURL(await r.blob())); }catch(e){} $('pp').textContent='Loading '+(++nl)+'/'+NF+'...'; } };
  await Promise.all(Array.from({length:16},worker)); ready=true; $('pp').textContent=ppTxt; window.demoReady=true; })();
// Integer scale of 512x384 in device px (no resampling) once it fits; otherwise fit the window.
function fit(){const d=devicePixelRatio||1,st=document.getElementById('stage'),fs=!!document.fullscreenElement,aw=fs?innerWidth:innerWidth-26,ah=fs?innerHeight:innerHeight-172,f=Math.min(aw,ah*4/3)*d,k=Math.floor(f/512);if(k<1){st.style.width=st.style.height='';return;}st.style.width=(512*k/d)+'px';st.style.height=(384*k/d)+'px';}
addEventListener('resize',fit);document.addEventListener('fullscreenchange',fit);fit();
