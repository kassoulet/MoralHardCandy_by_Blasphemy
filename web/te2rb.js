// te2rb (part 2) 3D pass in JS: camera/matrices/vertices in float32 (Math.fround per operation, in the order of the engine's x87 code with PC=24),
// Sphere01 textured polygons (recompiled 0x40660, poly_gen.js) + Tube03 wire (AA additive lines, 0x300a0 setup + 0x2ff80). Port of re/te2rb_{f32,wire,line,draw,poly}.py.
import {poly} from './poly_gen.js';
import {setupMem,SURF,TEXB,spanFn,buildItem} from './poly.js';
const f=Math.fround;
const b64=s=>{const b=atob(s),u=new Uint8Array(b.length);for(let i=0;i<b.length;i++)u[i]=b.charCodeAt(i);return u.buffer;};
const START=26.5;
const PIH=1.5707963267948966;
// ---- camera (te2rb_f32.py)
function hermite(keys,fr,comp){
  const n=keys.length; fr=f(fr);
  if(fr<keys[0].f) return keys[0].v;
  if(fr>=keys[n-1].f) return keys[n-1].v;
  let i=0; while(i<n-2&&!(keys[i+1].f>=fr))i++;
  const k0=keys[i],k1=keys[i+1];
  const u=f(f(fr-k0.f)/f(k1.f-k0.f)),A=f(u*u),B=f(A*u),A2=f(2*A),A3=f(3*A),B2=f(2*B);
  const h2=f(f(-B2)+A3),h1=f(f(B2-A3)+1),h3=f(f(B-A2)+u),h4=f(B-A);
  const out=[];
  for(let c=0;c<comp;c++){let s=f(f(h2*k1.v[c])+f(h1*k0.v[c])); s=f(s+f(h3*k0.to[c])); out.push(f(s+f(h4*k1.ti[c])));}
  return out;
}
const mid=()=>{const m=new Float32Array(16);m[0]=m[5]=m[10]=m[15]=1;return m;};
function mm(A,B){const o=new Float32Array(16);
  for(let i=0;i<4;i++)for(let j=0;j<4;j++){const p=[0,1,2,3].map(k=>f(A[i*4+k]*B[k*4+j]));o[i*4+j]=f(f(f(p[0]+p[1])+p[2])+p[3]);}
  return o;}
const rz=a=>{a=f(a);const s=f(Math.sin(a)),c=f(Math.cos(a)),m=mid();m[0]=c;m[1]=s;m[4]=-s;m[5]=c;return m;};
const rx=a=>{a=f(a);const s=f(Math.sin(a)),c=f(Math.cos(a)),m=mid();m[5]=c;m[6]=s;m[9]=-s;m[10]=c;return m;};
const ry=a=>{a=f(a);const s=f(Math.sin(a)),c=f(Math.cos(a)),m=mid();m[0]=c;m[2]=-s;m[8]=s;m[10]=c;return m;};
const trans=(x,y,z)=>{const m=mid();m[12]=x;m[13]=y;m[14]=z;return m;};
const asinE=s=>{const q=f(Math.sqrt(f(1-f(s*s))));return Math.atan2(s,q);};   // fpatan is not rounded by the x87 precision control: extended in the original, double here
function viewMatrix(pos,tgt,roll){
  const [px,py,pz]=pos.map(f),[tx,ty,tz]=tgt.map(f);
  const dx=f(tx-px),dy=f(ty-py),dz=f(tz-pz),dy2=f(dy*dy),dx2=f(dx*dx),dz2=f(dz*dz);
  const Lq=f(Math.sqrt(f(f(dy2+dx2)+dz2))),H=f(Math.sqrt(f(dz2+dx2)));
  const pitch=f(asinE(f(dy/Lq))),c=f(dz/H);
  let yaw=f(PIH-asinE(c)); if(tx>px)yaw=-yaw;
  let R=f(f(roll*2)*Math.PI); R=f(R*0.0027777777777777775);
  let m=mm(trans(-px,-py,-pz),ry(yaw)); m=mm(m,rx(pitch)); return mm(m,rz(R));
}
const PROJ=(()=>{const m=mid();m[0]=f(2/8);m[5]=f(2/4);return m;})();
// ---- scene
export const setWireLog=l=>{WIRELOG=l;};
export class Te2rb{
  constructor(d,tex){
    this.cam=d.cam; this.mem=setupMem(tex);
    const T=d.tube,S=d.sphere;
    this.tube={v:new Float32Array(b64(T.v)),f:new Uint16Array(b64(T.f)),ff:new Uint8Array(b64(T.ff)),t:T.t};
    this.sph={v:new Float32Array(b64(S.v)),uv:new Float32Array(b64(S.uv)),f:new Uint16Array(b64(S.f)),W:new Float32Array(b64(S.W))};
    this.ramp=new Uint32Array(256); for(let i=0;i<256;i++){const c=Math.min(255,Math.trunc(0.25*i));this.ramp[i]=((c<<16|c<<8|c)&0xfefeff)>>>0;}  // 0x2fe70 ramp, g=0.25 (every probed frame)
  }
  view(t){const fr=f(f(t-START)*35),c=this.cam;
    return viewMatrix(hermite(c.pos,fr,3),hermite(c.tgt,fr,3),hermite(c.roll,fr,1)[0]);}
  // camera-space vertices: cam = ((x*M0+y*M4)+z*M8)+M12 per component, float32 per op
  xform(P,M){const n=P.length/3,o=new Float32Array(n*3);
    for(let i=0;i<n;i++){const x=P[3*i],y=P[3*i+1],z=P[3*i+2];
      for(let j=0;j<3;j++) o[3*i+j]=f(f(f(f(x*M[j])+f(y*M[4+j]))+f(z*M[8+j]))+M[12+j]);}
    return o;}
  items(t){
    const V=this.view(t),Vp=mm(V,PROJ),q=[];
    // Sphere01: textured polygons
    {const S=this.sph,C=this.xform(S.v,mm(S.W,Vp));
     for(let k=0;k<S.f.length;k+=3){
       const P=[0,1,2].map(i=>{const a=S.f[k+i];return {c:[C[3*a],C[3*a+1],C[3*a+2]],uv:[S.uv[2*a],S.uv[2*a+1]],fl:0};});
       const r=this.face(P,true); if(r)q.push({idx:r.idx,n:q.length,kind:1,vs:r.vs});}}
    // Tube03: wire
    {const T=this.tube,M=mm(worldTube(T.t),Vp),C=this.xform(T.v,M);
     for(let k=0;k<T.f.length/3;k++){
       const P=[0,1,2].map(i=>{const a=T.f[3*k+i];return {c:[C[3*a],C[3*a+1],C[3*a+2]],uv:null,fl:0};});
       const r=this.face(P,false,T.ff[k]); if(r)q.push({idx:r.idx,n:q.length,kind:0,vs:r.vs,fl:r.fl});}}
    q.sort((a,b)=>a.idx-b.idx||b.n-a.n);   // buckets 0..4095, head insertion (LIFO within a bucket)
    return q.filter(e=>e.idx>=0&&e.idx<4096);
  }
  // cull, outcode, clip, project: one queued face or null
  face(P,tex,fl=0){
    const p0=P[0].c,p1=P[1].c,p2=P[2].c;
    const e=[0,1,2].map(k=>f(p1[k]-p0[k])),d=[0,1,2].map(k=>f(p2[k]-p0[k]));
    const n=[f(f(e[1]*d[2])-f(d[1]*e[2])),f(f(e[2]*d[0])-f(d[2]*e[0])),f(f(e[0]*d[1])-f(d[0]*e[1]))];
    const dot=f(f(f(n[1]*p0[1])+f(n[0]*p0[0]))+f(n[2]*p0[2]));
    if(dot<0)return null;
    const cs=P.map(p=>code(p.c));
    if(cs[0]&cs[1]&cs[2])return null;
    if(cs[0]|cs[1]|cs[2]){P.forEach((p,i)=>p.fl=(fl>>i)&1); P=clip(P); if(!P)return null;}
    else P.forEach((p,i)=>p.fl=(fl>>i)&1);
    const vs=P.map(p=>{const iz=f(1/p.c[2]);
      const v={c:p.c,sx:f(f(f(256*p.c[0])*iz)+255.5),sy:f(127.5-f(f(128*p.c[1])*iz)),fl:p.fl};
      if(tex){const k=f(f(0.01)/p.c[2]);v.iz=k;v.uz=f(k*p.uv[0]);v.vz=f(k*p.uv[1]);} return v;});
    const dep=f(f(f(p(P,0)+p(P,1))+p(P,2))*f(1/3));
    const idx=rint(f(4095-f(dep*f(f(4096)/f(88000)))));
    return {idx,vs,fl};
  }
  // render one frame t into surf (Uint32Array 512x256, the 0x36250 pass; target not cleared by the original, every pixel is covered by the dome)
  render(t,surf){
    const {m,mem}=this.mem; const s32=new Uint32Array(mem,SURF,512*256);
    const fn=(m,id,a)=>spanFn(m,a);
    for(const it of this.items(t)){
      if(it.kind){poly(m,buildItem(m,it.vs.map(v=>[v.sx,v.sy,v.uz,v.vz,v.iz])),0x1f0000,fn);}
      else wire(it.vs,this.ramp,s32);
    }
    surf.set(s32);
  }
}
const p=(P,i)=>P[i].c[2];
const rint=x=>{const r=Math.round(x);return (r-x===0.5&&r%2!==0)?r-1:r;};   // round half to even (np.rint)
function worldTube(t){const W=new Float32Array(16);W[2]=-1;W[5]=1;W[8]=1;W[12]=t[0];W[13]=0;W[14]=t[1];W[15]=1;return W;}
function code(c){const [x,y,z]=c,nz=-z;let b=0;if(nz>x)b|=1;if(x>z)b|=2;if(nz>y)b|=4;if(y>z)b|=8;return b;}
function lerpv(A,B,t){t=f(t);const o=f(1-t);
  return {c:[0,1,2].map(k=>f(f(t*B.c[k])+f(o*A.c[k]))),uv:A.uv?[0,1].map(k=>f(f(t*B.uv[k])+f(o*A.uv[k]))):null,fl:0};}
function clip(poly_){
  for(const [m,ax,sg] of [[1,0,-1],[2,0,1],[4,1,-1],[8,1,1]]){
    const out=[],n=poly_.length;
    for(let i=0;i<n;i++){
      const a=poly_[i],b=poly_[(i+1)%n],ia=!(code(a.c)&m),ib=!(code(b.c)&m);
      if(ia)out.push(a);
      if(ia!==ib){
        let num,den;
        if(sg<0){num=f(-a.c[2]-a.c[ax]);den=f(f(b.c[ax]-a.c[ax])+f(b.c[2]-a.c[2]));}
        else{num=f(a.c[2]-a.c[ax]);den=f(f(b.c[ax]-a.c[ax])-f(b.c[2]-a.c[2]));}
        const v=lerpv(a,b,f(num/den)); v.fl=a.fl; out.push(v);   // new vertex carries the edge flag of the input vertex a
      }
    }
    poly_=out;
  }
  return poly_.length>=3?poly_:null;
}
// ---- wire: 0x3fcb0 (edges with flag bit) -> 0x300a0 clip+DDA setup -> 0x2ff80 AA additive line
export let WIRELOG=null;
function wire(vs,ramp,s32){
  const n=vs.length;
  for(let i=0;i<n;i++) if(vs[i].fl){const a=vs[i],b=vs[(i+1)%n]; const r=setup(a.sx,a.sy,b.sx,b.sy); if(r){if(WIRELOG)WIRELOG.push(r);drawLine(s32,ramp,r);}}
}
const cl=(v,hi)=>{v=v<=1?1:v;return v>=hi?hi:v;};
function clipLine(A,B,C,D,w,h){
  const hx=f(w-2),hy=f(h-2);
  let f0=(A<1?4:0)|(A>hx?8:0),f1=(C<1?4:0)|(C>hx?8:0);
  if(f0&f1)return null;
  if((f0|f1)&12){const m=f(f(D-B)/f(C-A)),b=f(B-f(A*m));const A1=cl(A,hx),B1=f(f(A1*m)+b),C1=cl(C,hx),D1=f(f(C1*m)+b);A=A1;B=B1;C=C1;D=D1;}
  f0=(B<1?1:0)|(B>hy?2:0);f1=(D<1?1:0)|(D>hy?2:0);
  if(f0&f1)return null;
  if((f0|f1)&3){const mi=f(f(C-A)/f(D-B)),b=f(A-f(B*mi));const B1=cl(B,hy),A1=cl(f(f(mi*B1)+b),hx),D1=cl(D,hy),C1=cl(f(f(mi*D1)+b),hx);A=A1;B=B1;C=C1;D=D1;}
  return [A,B,C,D];
}
const PITCH=2048;
function setup(x0,y0,x1,y1,w=512,h=256){
  const r=clipLine(f(x0),f(y0),f(x1),f(y1),w,h); if(!r)return null;
  let [A,B,C,D]=r; const dx=f(C-A),dy=f(D-B); let xs=4,ys=PITCH;
  if(0>=dx){xs=-4;A=-A;C=-C;} if(0>=dy){ys=-PITCH;B=-B;D=-D;}
  let adx=Math.abs(dx),ady=Math.abs(dy),bound=h-2;
  if(ady>adx){[adx,ady]=[ady,adx];[xs,ys]=[ys,xs];[A,B]=[B,A];C=D;bound=w-2;}
  if(adx===0)return null;
  const sl=f(ady/adx),slope=Math.trunc(Math.min(sl*4294967296,4294967295));
  const ai0=Math.trunc(A),ci=Math.trunc(C);let ai=ai0,cnt=ci-ai,v=0,mi=0;
  while(cnt>=0){v=f(f(f(ai-A)*sl)+B);mi=Math.trunc(v);if(mi<0)mi-=1;if(1<=Math.abs(mi)&&Math.abs(mi)<=bound)break;ai++;cnt--;}
  if(cnt<0)return null;
  const frac=Math.trunc((v-mi)*4294967296)%4294967296;   // low dword of the 64-bit fixed value
  return {a:mi*ys+ai*xs,cnt,frac:frac>>>0,xs,ys,slope};
}
function sat(p,t){const s=((p&0xfefeff)+t)>>>0,m=s&0x1010100;return (s|((m-(m>>>7))>>>0))>>>0;}
function drawLine(s32,ramp,{a,cnt,frac,xs,ys,slope}){
  let n=cnt,fr=frac,ms=ys;
  for(;;){
    const w=fr>>>24; let i=(a+ms)>>2; s32[i]=sat(s32[i],ramp[w]); i=a>>2; s32[i]=sat(s32[i],ramp[~w&255]);
    if(--n<0)break;
    fr+=slope; const carry=fr>4294967295; if(carry)fr-=4294967296; a+=xs; if(carry)a+=ms;
  }
}
