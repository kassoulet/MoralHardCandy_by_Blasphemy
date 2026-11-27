// te2rb textured polygons: memory model + span function 0x83540 (hand port, literal) for the recompiled scan converter web/poly_gen.js
export const SURF=0x300000, TEXB=0x400000;   // flat address space: 512x256x4 target (pitch 2048), 256x256x4 texture (pitch 1024)
export function setupMem(tex){
  const mem=new ArrayBuffer(0x800000), m=new DataView(mem);
  m.setFloat64(0x1032a0,65536,true); m.setFloat64(0x1032a8,65536,true); m.setFloat32(0x107468,0.0625,true);
  for(let n=1;n<=16;n++) m.setFloat32(0x107bd0+4*n,1/n,true);   // table of float32 1/n (n=0 -> 0)
  if(tex) new Uint8Array(mem,TEXB,tex.length).set(tex);
  return {m,mem};
}
const U=new WeakMap(), u32of=m=>{let u=U.get(m); if(!u){u=new Uint32Array(m.buffer);U.set(m,u);} return u;};   // dst/texel addresses are 4-aligned: index the memory as dwords
// 0x83540: dst, tex, count, u, v, du, dv, mask (cdecl); 16.16 coordinates, nearest texel copy
export function spanFn(m,argp){
  let dst=m.getInt32(argp,true),tex=m.getInt32(argp+4,true),n=m.getInt32(argp+8,true),u=m.getInt32(argp+12,true),v=m.getInt32(argp+16,true);
  const du=m.getInt32(argp+20,true),dv=m.getInt32(argp+24,true),mask=m.getInt32(argp+28,true),M=u32of(m); dst>>>=2; tex>>>=2;
  while(n-->0){ M[dst++]=M[tex+((((u&mask)>>>14)|((v&mask)>>>6))>>>2)]; u=(u+du)|0; v=(v+dv)|0; }
}
// build a polygon item (what 0x36250 queues) for 0x40660 in the flat memory: verts = [[sx,sy,u/z,v/z,1/z],...] (float32 values); returns the item address
export function buildItem(m,verts,tex={w:256,pitch:1024}){
  const ITEM=0x200000,VA=0x200100,VB=0x201000,MAT=0x203000,TEXO=0x203100,SO=0x203200,CTX=0x203300,X=0x203400,OBJ=0x203500;
  for(let i=0;i<0x80;i+=4) m.setInt32(ITEM+i,0,true);
  m.setInt32(ITEM+0xc,verts.length,true); m.setInt32(ITEM+4,OBJ,true); m.setInt32(OBJ,1,true);
  verts.forEach((v,k)=>{const a=VB+0x80*k; m.setInt32(VA+4*k,a,true);
    m.setFloat32(a+0x18,v[0],true); m.setFloat32(a+0x1c,v[1],true); m.setFloat32(a+0x40,v[2],true); m.setFloat32(a+0x44,v[3],true); m.setFloat32(a+0x50,v[4],true);});
  m.setInt32(ITEM+0x10,VA,true); m.setInt32(ITEM+0x38,MAT,true); m.setInt32(ITEM+0x64,CTX,true); m.setInt32(CTX+0x48,X,true); m.setInt32(X+0xc,SO,true);
  m.setInt32(SO,512,true); m.setInt32(SO+4,256,true); m.setInt32(SO+8,2048,true); m.setInt32(SO+0x10,SURF,true);
  m.setInt32(MAT+0xc,0xff,true); m.setInt32(MAT+0x18,TEXO,true); m.setInt32(TEXO,tex.w,true); m.setInt32(TEXO+4,256,true); m.setInt32(TEXO+8,tex.pitch,true); m.setInt32(TEXO+0x10,TEXB,true);
  return ITEM;
}
// 0x83301: dst = paddusb(dst, color) for count dwords (args dst,color,count)
export function addFill(m,argp){
  let dst=m.getInt32(argp,true)>>>2; const c=m.getInt32(argp+4,true),n=m.getInt32(argp+8,true),M=u32of(m),c0=c&255,c1=c>>>8&255,c2=c>>>16&255,c3=c>>>24;
  for(let i=0;i<n;i++,dst++){ const d=M[dst]; let x;
    M[dst]=(Math.min(255,(d&255)+c0)|Math.min(255,(d>>>8&255)+c1)<<8|Math.min(255,(d>>>16&255)+c2)<<16|Math.min(255,(d>>>24)+c3)<<24)>>>0; }
}
// flat additive face item for the recompiled 0x3fd50: material table (256 colours at +0xc) indexed by the face's light index at +0x58
export function buildFill(m,verts,idx,ramp){
  const ITEM=0x200000,VA=0x200100,VB=0x201000,MATF=0x204000,OBJF=0x204800,SO=0x203200,CTX=0x203300,X=0x203400;
  for(let i=0;i<0x80;i+=4) m.setInt32(ITEM+i,0,true);
  m.setInt32(ITEM+0xc,verts.length,true); m.setInt32(ITEM+4,OBJF,true); m.setInt32(OBJF,0x83301,true);
  verts.forEach((v,k)=>{const a=VB+0x80*k; m.setInt32(VA+4*k,a,true); m.setFloat32(a+0x18,v[0],true); m.setFloat32(a+0x1c,v[1],true);});
  m.setInt32(ITEM+0x10,VA,true); m.setInt32(ITEM+0x38,MATF,true); m.setInt32(ITEM+0x58,idx,true); m.setInt32(ITEM+0x64,CTX,true); m.setInt32(CTX+0x48,X,true); m.setInt32(X+0xc,SO,true);
  m.setInt32(SO,512,true); m.setInt32(SO+4,256,true); m.setInt32(SO+8,2048,true); m.setInt32(SO+0x10,SURF,true);
  for(let i=0;i<256;i++) m.setUint32(MATF+0xc+4*i,ramp[i],true);
  return ITEM;
}
