// te2rb textured polygons: memory model + span function 0x83540 (hand port, literal) for the recompiled scan converter web/poly_gen.js
export const SURF=0x300000, TEXB=0x400000;   // flat address space: 512x256x4 target (pitch 2048), 256x256x4 texture (pitch 1024)
export function setupMem(tex){
  const mem=new ArrayBuffer(0x800000), m=new DataView(mem);
  m.setFloat64(0x1032a0,65536,true); m.setFloat64(0x1032a8,65536,true); m.setFloat32(0x107468,0.0625,true);
  for(let n=1;n<=16;n++) m.setFloat32(0x107bd0+4*n,1/n,true);   // table of float32 1/n (n=0 -> 0)
  if(tex) new Uint8Array(mem,TEXB,tex.length).set(tex);
  return {m,mem};
}
// 0x83540: dst, tex, count, u, v, du, dv, mask (cdecl); 16.16 coordinates, nearest texel copy
export function spanFn(m,argp){
  let dst=m.getInt32(argp,true),tex=m.getInt32(argp+4,true),n=m.getInt32(argp+8,true),u=m.getInt32(argp+12,true),v=m.getInt32(argp+16,true);
  const du=m.getInt32(argp+20,true),dv=m.getInt32(argp+24,true),mask=m.getInt32(argp+28,true);
  while(n-->0){ m.setInt32(dst,m.getInt32(tex+(((u&mask)>>>14)|((v&mask)>>>6)),true),true); dst+=4; u=(u+du)|0; v=(v+dv)|0; }
}
