// Part 1 (title) port of CANDYD.EXE 0x28770 (render) + row blitters 0x82e05 (A) / 0x82f07 (B). Pure function of t (t = seconds since part start).
// Pixels: dst = graybg; dst = dst*v>>8 (column streaks v[x]); logo2 sprite with opacity (B rows, table T); mhcbox sprite (A rows).
export const W=512,H=256;
export async function loadPart0(url){
  const b=new Uint8Array(await new Response((await fetch(url)).body.pipeThrough(new DecompressionStream('deflate'))).arrayBuffer()); let o=0;
  const cut=n=>b.subarray(o,o+=n); return {bg:cut(W*H*3),logo:cut(300*90*4),box:cut(W*H*4),T:cut(96*256)};
}
export function renderPart0(out,t,A){   // out: Uint8ClampedArray W*H*4
  const S=Math,clamp=(v,l,h)=>v<l?l:v>h?h:v;
  // the original's background copy (0x43590) leaves a 1-pixel black border (golden frames: rows 0,255 and columns 0,511 are 0; clip behaviour not traced further)
  out.fill(0); for(let y=1;y<H-1;y++) for(let x=1;x<W-1;x++){ const i=(y*W+x)*4,j=(y*W+x)*3; out[i]=A.bg[j]; out[i+1]=A.bg[j+1]; out[i+2]=A.bg[j+2]; }
  for(let i=3;i<out.length;i+=4) out[i]=255;
  const a=S.fround(clamp(t*0.01491,0,3)), c1=t*1.1231,c2=t*1.0131,c3=t*1.3431,c4=t*1.5631,c5=t*0.5731, v=new Uint8Array(W);
  for(let x=0;x<W;x++){
    const s=0.1*S.sin(.125*x-c1)+0.1*S.cos(.071*x+c2)+0.1*S.cos(.363*x-c3)+0.1*S.sin(.33*x+c4)+0.1*S.sin(.705*x-c5)+(a-0.3);
    v[x]=clamp(S.trunc(s*255),0,255);
  }
  for(let y=0;y<H;y++) for(let x=0;x<W;x++){ const i=(y*W+x)*4; for(let c=0;c<3;c++) out[i+c]=(out[i+c]*v[x])>>8; }
  const f=clamp((t-2)*0.03822,0,1), op=clamp(S.trunc(S.fround(f*0.3)*256),0,255);
  if(f>0) for(let y=0;y<90;y++) for(let x=0;x<300;x++){ const s=(y*300+x)*4,al=A.logo[s+3]; if(!al) continue;
    const i=((y+83)*W+x+106)*4,w=op<96?A.T[op*256+255-al]:0; for(let c=0;c<3;c++) out[i+c]=(((out[i+c]*w)>>8)+((A.logo[s+c]*op)>>8))&255; }
  for(let p=0;p<W*H;p++){ const s=p*4,al=A.box[s+3]; if(!al) continue; for(let c=0;c<3;c++) out[s+c]=(((out[s+c]*(255-al))>>8)+A.box[s+c])&255; }
  return out;
}
