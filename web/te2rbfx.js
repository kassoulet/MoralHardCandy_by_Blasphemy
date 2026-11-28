// te2rb (part 2) compositing after the 0x36250 pass, port of 0x29da0 (non-flash branch): background frame sprite 0x31030 (row fn A 0x82e05),
// palette filter 0x43990 + 8bpp additive blit 0x30e30 (row fn 0x83155) of the 218x218 halo, two scan-bar sprites tiled with 0x31030 (row fn B 0x82f07, table T) into a
// 431-px-wide view of the surface (x offset 40). Surface = Uint32Array 512x256, byte order B,G,R,X (little-endian 0xXXRRGGBB).
import {stretch} from './stretch_gen.js';
const f=Math.fround, W=512, H=256, START=26.5;
// music events of part 2 (handler 0x2a410, args = the double at part+0x34): 0x500 sets part+0x24 (halo factor 0.67) and starts a flash, 0x600 clears +0x24 and starts a flash.
// Times are the raw arg doubles captured from the emulator (float32-precision values), re/probe_events.py.
const dbl=(lo,hi)=>new Float64Array(new Uint32Array([lo,hi]).buffer)[0];
// [row time (fires when the music position reaches it; 1e-6 slack for the harness' accumulated frame clock), code, flash start = the arg double]
export const EVENTS=[[30.4,0x500,dbl(0x60000000,0x403e6666)],[35.2,0x600,dbl(0xa0000000,0x40419999)]];
export function state(t,slack=1e-6){let pal24=0,start=-1;for(const [et,c,a] of EVENTS) if(t>=et-slack){start=a;pal24=c===0x500?1:0;} return {pal24,start};}
export function parseFx(b){   // b: inflated bytes of te2rb_fx.bin
  let o=0; const cut=n=>b.subarray(o,o+=n);
  const spr=(w,h)=>{const r=cut(w*h*4),d=new Uint32Array(w*h); for(let i=0;i<w*h;i++) d[i]=((255-r[4*i+3])<<24|r[4*i]<<16|r[4*i+1]<<8|r[4*i+2])>>>0; return {w,h,d};};  // stored: R,G,B + (255-alpha) in byte 3
  const kasser=spr(512,256), dna=spr(640,17), img=cut(218*218), pal=new Uint8Array(cut(1024)), T=cut(65536);
  return {kasser,dna,img,pal,T};
}
// row fn A: dst = ((dst*sa)>>8) + src, bytewise wrap, alpha byte cleared (0x82e05)
const rowA=(d,s)=>{const a=s>>>24; let r=0; for(let k=0;k<24;k+=8) r|=((((d>>>k&255)*a>>8)+(s>>>k&255))&255)<<k; return r>>>0;};
// row fn B: dst = ((dst*T[op][sa])>>8) + ((src*op)>>8) (0x82f07)
const rowB=(d,s,op,T)=>{const w=T[op*256+(s>>>24)]; let r=0; for(let k=0;k<24;k+=8) r|=((((d>>>k&255)*w>>8)+((s>>>k&255)*op>>8))&255)<<k; return r>>>0;};
const TRANSP=0xff000000;
// 0x31030: sprite at (x,y) into the view (vx,vw) x full height, opacity o (float32)
function sprite(surf,sp,x,y,o,vx,vw,T){
  const op=Math.trunc(f(o*256));   // op==0 is still drawn (row fn B with T[0][sa] = 255 darkens by 1)
  const A=o>=1||op>=255;
  const x0=Math.max(0,x),x1=Math.min(vw,x+sp.w),y0=Math.max(0,y),y1=Math.min(H,y+sp.h);
  for(let yy=y0;yy<y1;yy++) for(let xx=x0;xx<x1;xx++){
    const s=sp.d[(yy-y)*sp.w+xx-x]; if(s===TRANSP) continue;
    const i=yy*W+vx+xx; surf[i]=A?rowA(surf[i],s):rowB(surf[i],s,op,T);
  }
}
// 0x43990: palette bytes B,G,R: min(255, trunc(f32(byte*factor)))
const filterPal=(pal,fac)=>{const o=new Uint8Array(pal); fac=f(fac); for(let i=0;i<256;i++) for(let c=0;c<3;c++) o[4*i+c]=Math.min(255,Math.trunc(f(pal[4*i+c]*fac))); return o;};
// 0x83155: dst = paddusb(dst, pal[idx]) for the 218x218 image at (147,19)
function halo(surf,fx,pal){
  for(let y=0;y<218;y++) for(let x=0;x<218;x++){
    const p=fx.img[y*218+x], i=(y+19)*W+x+147, d=surf[i]; let r=0;
    for(let k=0;k<32;k+=8) r|=Math.min(255,(d>>>k&255)+pal[4*p+(k>>3)])<<k;
    surf[i]=r>>>0;
  }
}
// bars (0x29f5b..0x2a3d0): t' = t - start
function bars(surf,tp,fx){
  let a=f(tp*0.041); if(a>=1) a=1;
  const o=f(a*0.6);
  for(const [dir,y] of [[-36,22],[36,217]]){
    const off=Math.trunc(f(tp*dir)), w=fx.dna.w; let rem=off%w; while(w+rem>0) rem-=w;
    for(let x=rem;x<431;x+=w) sprite(surf,fx.dna,x,y,o,40,431,fx.T);
  }
}
// flash branch (0x29fea..0x2a28b), runs while f32((t-start)*1.2)<1: a 256-entry gray palette from a 5-term sin/cos sum is stretched (row fn 0x827b2, additive nearest) over the whole
// surface by 0x2fdb0/0x2f8e0 (recompiled: stretch_gen.js). Own flat memory: surface 0x1000, stack 0x1f0000, views 0x1e0000.
const SURF=0x1000,STK=0x1f0000,VD=0x1e0000,VS=0x1e0040,PAL=0x1e1000,fm=new DataView(new ArrayBuffer(1<<21));
fm.setFloat64(0x102b2e,0.5,true); fm.setFloat64(0x102b36,65536,true); fm.setFloat64(0x102b3e,-1,true);   // the doubles 0x2f8e0 reads from the data section
const stretchRow=(m,id,a)=>{ if(id!==0x827b2) throw new Error('row fn '+id.toString(16));
  const [dst,src,sx0,sy0,dx,dy,w,h,dp,sp]=[0,1,2,3,4,5,6,7,8,9].map(i=>m.getInt32(a+4*i,true)); let sy=sy0>>>0;
  for(let y=0,d=dst;y<h;y++,d+=dp-4*w,sy=(sy+dy)>>>0){ const row=src+(sy>>>16)*sp; let sx=sx0>>>0;
    for(let x=0;x<w;x++,d+=4,sx=(sx+dx)>>>0){ const a_=m.getUint32(d,true),b=m.getUint32(row+(sx>>>16)*4,true); let r=0;
      for(let k=0;k<32;k+=8) r|=Math.min(255,(a_>>>k&255)+(b>>>k&255))<<k; m.setUint32(d,r>>>0,true);} } };
function flash(surf,tp,fade){
  const P=[8.521,9.331,24.5421,28.5621,10.4721].map(c=>tp*c);
  for(let i=0;i<256;i++){
    const e=[Math.sin(i*0.075+P[0]),Math.cos(i*0.213-P[1]),Math.cos(i*2.178-P[2]),Math.sin(i*2.805+P[3]),Math.sin(i*4.23-P[4])];
    let v=(0.5-fade)+0.1*e[0]; v+=0.1*e[1]; v+=0.1*e[2]; v+=0.1*e[3]; v+=0.1*e[4];
    v=Math.trunc(v*255); v=v<=0?0:v>=255?255:v; const g=Math.trunc(v*0.22); fm.setUint32(PAL+4*i,(g<<16|g<<8|g)>>>0,true);
  }
  new Uint32Array(fm.buffer,SURF,W*H).set(surf);
  const view=(a,w,h,p,b)=>{fm.setInt32(a,w,true);fm.setInt32(a+4,h,true);fm.setInt32(a+8,p,true);fm.setInt32(a+0x10,b,true);};
  view(VS,1,256,4,PAL); view(VD,W,H,W*4,SURF);
  const sp=STK; fm.setInt32(sp,0,true); [256,128,512,1].forEach((v,i)=>fm.setFloat32(sp+4+4*i,v,true)); fm.setInt32(sp+20,0x827b2,true);
  stretch(fm,VD,sp,stretchRow,VS);
  surf.set(new Uint32Array(fm.buffer,SURF,W*H));
}
// state: {pal24: part+0x24 flag (selects the filter factor), } ; frame must already hold the 0x36250 output
export function compose(surf,t,fx,st={}){
  sprite(surf,fx.kasser,0,0,1,0,W,fx.T);
  if(st.start>=0){ const fade=f(((t-st.start)*1.2)); if(fade<1) flash(surf,t-START,fade); }
  halo(surf,fx,filterPal(fx.pal,st.pal24?0.67:0.4));   // 0x3f2b851f / 0x3ecccccd
  bars(surf,t-START,fx);
  for(let x=0;x<W;x++) surf[x]=surf[(H-1)*W+x]=0;   // 0x1d400 (main loop, after the render): clear the 1-px border of the surface
  for(let y=0;y<H;y++) surf[y*W]=surf[y*W+W-1]=0;
  return surf;
}
