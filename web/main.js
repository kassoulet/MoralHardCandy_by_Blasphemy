// main.js - storyboard stage: music (libopenmpt via chiptune3) + the golden frames captured from the original, pause/seek on the music clock.
const $=id=>document.getElementById(id), cvs=$('c'), ctx=cvs.getContext('2d'), sk=$('seek');
const fmt=s=>Math.floor(s/60)+':'+String(Math.floor(s%60)).padStart(2,'0');
let frames=[], imgs=[], dur=259.74, playing=false, tBase=0, wall0=0, cp=null, ac=null, buf=null, started=false, last=-1;
const now=()=>performance.now()/1000, cur=()=>playing?Math.min(dur,tBase+(now()-wall0)):tBase;
let parts=[]; try{ const j=await (await fetch('assets/parts.json')).json(); parts=j.parts; dur=j.length; sk.max=Math.round(dur*10); }catch(e){}
// Golden frames: what the ORIGINAL CANDYD.EXE drew (512x256 surface, captured under emulation every 0.2 s, see re/harness.py), letterboxed in 640x480.
// parts.json = the original's 14-part table at music times.
const STEP=0.2, cache=new Map();
const frameAt=i=>{ let im=cache.get(i); if(!im){ im=new Image(); im.src='assets/gold/g'+String(i).padStart(4,'0')+'.webp'; cache.set(i,im); if(cache.size>400) cache.delete(cache.keys().next().value); } return im; };
import {renderPart0,loadPart0,W as PW,H as PH} from './part0.js';
let shown=-1, A0=null; const js=$('js'), buf0=new Uint8ClampedArray(PW*PH*4), id0=new ImageData(buf0,PW,PH);
try{ A0=await loadPart0('assets/part0.bin'); }catch(e){ js.disabled=true; }
js.onchange=()=>{ shown=-1; };
function draw(){
  const t=cur(), i=Math.min(Math.floor(dur/STEP),Math.floor(t/STEP)), p=parts.find(p=>t>=p.t0&&t<p.t1)||parts[parts.length-1];
  for(let k=1;k<=5;k++) frameAt(i+k);
  if(js.checked&&A0&&t<26.5){ renderPart0(buf0,t,A0); ctx.fillStyle='#000'; ctx.fillRect(0,0,640,480); ctx.putImageData(id0,64,112); shown=-2; } else {
  const im=frameAt(i);
  if(im.complete&&im.naturalWidth&&shown!==i){ ctx.fillStyle='#000'; ctx.fillRect(0,0,640,480); ctx.drawImage(im,64,112); shown=i; } }
  $('msg').textContent=p?'part '+(p.i+1)+'/'+parts.length+'  '+(partfiles[p.i]||[]).join(' '):'';
  $('tm').textContent=fmt(t)+' / '+fmt(dur); if(!sk.matches(':active')) sk.value=Math.round(t*10);
  requestAnimationFrame(draw);
}
let partfiles=[]; try{ partfiles=(await (await fetch('assets/partfiles.json')).json()).map(o=>o.files); }catch(e){}
async function start(){
  if(started) return; started=true; $('msg').textContent='';
  const {ChiptuneJsPlayer}=await import('./vendor/chiptune3.js');
  ac=new AudioContext(); cp=new ChiptuneJsPlayer({context:ac,repeatCount:0,interpolationFilter:8});
  await new Promise(r=>cp.onInitialized(r));
  buf=await (await fetch('assets/7kingsi2.xm')).arrayBuffer(); cp.play(buf); playing=true; tBase=0; wall0=now(); $('pp').textContent='Pause';
}
function seek(t){ t=Math.max(0,Math.min(dur-0.01,t)); tBase=t; wall0=now(); cp&&cp.setPos(t); shown=-1; }
async function toggle(){
  if(!started) return start();
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
window.demoReady=true;
