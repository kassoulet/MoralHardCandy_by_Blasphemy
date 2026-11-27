#!/usr/bin/env python3
"""mk_poly.py [poly_40660.dis] > ../web/poly_gen.js
Static recompile of the te2rb textured-polygon scan converter 0x40660 (objdump listing of 0x40660..0x41730) into JS.
Not a hand port: every x86/x87 instruction becomes one JS statement (registers = int32 vars, memory = DataView, x87 stack = array).
x87 model: the function runs with CW=0x0b3f (64-bit mantissa, round UP): arithmetic is done in doubles (nearest), stores to float32
round up (f32up), fist/fistp = ceil.  Only this subset of the ISA occurs; anything else raises."""
import re,sys
SRC=sys.argv[1] if len(sys.argv)>1 else __file__.rsplit('/',1)[0]+'/poly_40660.dis'
R32=('eax','ebx','ecx','edx','esi','edi','ebp','esp')
R8={'al':('eax',0),'cl':('ecx',0),'dl':('edx',0),'bl':('ebx',0),'ah':('eax',8),'ch':('ecx',8),'dh':('edx',8),'bh':('ebx',8)}
ins=[]
for l in open(SRC):
    m=re.match(r'\s*([0-9a-f]+):\t([0-9a-f ]+?)\s*\t(\S+)\s*(.*)$',l)
    if m: ins.append((int(m[1],16),m[3],m[4].strip()))
def addr(s):
    """address expression inside [..] or ds:imm"""
    m=re.search(r'ds:(0x[0-9a-f]+)',s)
    if m: return m[1]
    inner=re.search(r'\[(.*)\]',s)[1]; parts=[]
    for sign,t in re.findall(r'([+-]?)([^+-]+)',inner):
        t=t.strip(); sg='-' if sign=='-' else '+'
        if '*' in t: r,k=t.split('*'); parts.append(f'{sg}{r}*{k}')
        elif t in R32: parts.append(f'{sg}{t}')
        else: parts.append(f'{sg}{int(t,16)}')
    return '('+''.join(parts).lstrip('+')+')|0'
def size(s): return {'DWORD':4,'QWORD':8,'WORD':2,'BYTE':1}[s.split()[0]] if 'PTR' in s else 0
def ismem(s): return 'PTR' in s
def rd(s,sz=None):
    s=s.strip()
    if ismem(s):
        a=addr(s); z=size(s)
        return {4:f'm.getInt32({a},true)',2:f'm.getUint16({a},true)',1:f'm.getUint8({a})'}[z]
    if s in R32: return s
    if s in R8: r,sh=R8[s]; return f'(({r}>>{sh})&255)'
    if s.startswith('0x'): v=int(s,16); return str(v-(1<<32) if v>0x7fffffff else v)
    raise Exception('rd '+s)
def wr(s,v):
    s=s.strip()
    if ismem(s):
        a=addr(s); z=size(s)
        return {4:f'm.setInt32({a},{v},true)',2:f'm.setUint16({a},{v},true)',1:f'm.setUint8({a},{v})'}[z]+';'
    if s in R32: return f'{s}=({v})|0;'
    if s in R8: r,sh=R8[s]; return f'{r}=({r}&~(255<<{sh}))|((({v})&255)<<{sh});'
    raise Exception('wr '+s)
def sti(s):
    m=re.match(r'st\((\d)\)',s); return int(m[1]) if m else 0
def S(i): return f'st[st.length-{1+i}]'
def fm(s):   # float memory operand
    a=addr(s); return f'm.getFloat32({a},true)' if size(s)==4 else f'm.getFloat64({a},true)'
JCC={'je':{1:'a==b',0:'r==0',2:'a==b'},'jne':{1:'a!=b',0:'r!=0',2:'a!=b'},
 'jl':{1:'a<b',0:'r<0'},'jle':{1:'a<=b',0:'r<=0'},'jg':{1:'a>b',0:'r>0'},'jge':{1:'a>=b',0:'r>=0'},
 'ja':{1:'(a>>>0)>(b>>>0)',0:'r!=0',2:'a>b'},'jae':{1:'(a>>>0)>=(b>>>0)',0:'true',2:'a>=b'},
 'jbe':{1:'(a>>>0)<=(b>>>0)',0:'r==0',2:'a<=b'},'jb':{1:'(a>>>0)<(b>>>0)',0:'false',2:'a<b'}}
out=[]; E=out.append
for pc,op,args in ins:
    E(f'case 0x{pc:x}:')
    ops=[x.strip() for x in re.split(r',(?![^\[]*\])',args)] if args else []
    if op=='mov': E(wr(ops[0],rd(ops[1])))
    elif op=='lea': E(f'{ops[0]}=({addr(ops[1])})|0;')
    elif op=='push': E(f'esp=(esp-4)|0;m.setInt32(esp,{rd(ops[0])},true);')
    elif op=='pop': E(f'{ops[0]}=m.getInt32(esp,true);esp=(esp+4)|0;')
    elif op in('add','sub','and','xor','cmp','test'):
        a,b=rd(ops[0]),rd(ops[1]); E(f'A={a};B={b};')
        if op=='cmp': E('Fa=A;Fb=B;Fk=1;')
        else:
            e={'add':'A+B','sub':'A-B','and':'A&B','xor':'A^B','test':'A&B'}[op]
            if op=='sub': E('Fa=A;Fb=B;Fk=1;')
            else: E(f'Fr=({e})|0;Fk=0;')
            if op!='test': E(wr(ops[0],f'({e})|0'))
    elif op in('inc','dec'): E(f'Fr=({rd(ops[0])}{"+" if op=="inc" else "-"}1)|0;Fk=0;'+wr(ops[0],'Fr'))
    elif op=='shl': E(wr(ops[0],f'{rd(ops[0])}<<{rd(ops[1])}'))
    elif op=='imul': E(wr(ops[0],f'Math.imul({rd(ops[0])},{rd(ops[1])})'))
    elif op=='jmp': E(f'pc=0x{int(ops[0],16):x};continue;')
    elif op in JCC:
        c=JCC[op]
        sub=lambda e,**k:re.sub(r'\b([abr])\b',lambda m:'F'+m[1],e)
        e1=sub(c[1]); e0=sub(c[0]) if 0 in c else 'false'; e2=sub(c[2]) if 2 in c else 'false'
        E(f'if(Fk==1?({e1}):Fk==0?({e0}):({e2})){{pc=0x{int(ops[0],16):x};continue;}}')
    elif op=='call': E('esp=(esp-4)|0;callfn(m,m.getInt32('+addr(ops[0])+',true),esp+4);esp=(esp+4)|0;')
    elif op=='ret': E('return;')
    elif op in('fldcw',): E(';')
    elif op=='fstcw': E(f'm.setUint16({addr(ops[0])},0x37f,true);')
    elif op=='fld':
        if ismem(ops[0]): E(f'st.push({fm(ops[0])});')
        else: E(f'st.push({S(sti(ops[0]))});')
    elif op=='fild': E(f'st.push({rd(ops[0])});')
    elif op=='fld1': E('st.push(1);')
    elif op=='fldz': E('st.push(0);')
    elif op in('fst','fstp'):
        pop='st.pop();' if op=='fstp' else ''
        if size(ops[0])==4: E(f'm.setFloat32({addr(ops[0])},f32up({S(0)}),true);'+pop)
        else: E(f'm.setFloat64({addr(ops[0])},{S(0)},true);'+pop)
    elif op in('fist','fistp'):
        E(f'm.setInt32({addr(ops[0])},Math.ceil({S(0)}),true);'+('st.pop();' if op=='fistp' else ''))
    elif op=='fchs': E(f'{S(0)}=-{S(0)};')
    elif op=='fxch': E(f't=st.length-1;j=t-{sti(ops[0])};x=st[t];st[t]=st[j];st[j]=x;')
    elif op=='fcomp': E(f'Fa={S(0)};Fb={fm(ops[0])};Fk=2;st.pop();')
    elif op=='fcompp': E(f'Fa={S(0)};Fb={S(1)};Fk=2;st.pop();st.pop();')
    elif op in('fnstsw',): E(';')
    elif op=='sahf': E(';')
    elif op in('fadd','fsub','fsubr','fmul','fdiv','fdivr'):
        sym={'fadd':'a+b','fsub':'a-b','fsubr':'b-a','fmul':'a*b','fdiv':'a/b','fdivr':'b/a'}[op]
        if ismem(ops[0]): b=fm(ops[0]); E(f'{S(0)}='+sym.replace('a',S(0)).replace('b',b)+';')
        else:  # st,st(i)  (dest st)
            assert ops[0]=='st'; E(f'{S(0)}='+sym.replace('a',S(0)).replace('b',S(sti(ops[1])))+';')
    elif op in('faddp','fmulp','fsubp','fdivp','fdivrp','fsubrp'):
        i=sti(ops[0]); sym={'faddp':'a+b','fmulp':'a*b','fsubp':'a-b','fdivp':'a/b','fdivrp':'b/a','fsubrp':'b-a'}[op]
        E(f'{S(i)}='+sym.replace('a',S(i)).replace('b',S(0))+';st.pop();')
    else: raise Exception(f'{pc:x} {op} {args}')
# the objdump listing has fsubp after a fcomp pair sequence: fnstsw/sahf need Fk=2 kept: nothing to do.
body='\n'.join(out)
print('''// GENERATED by re/mk_poly.py from re/poly_40660.dis - do not edit. Static recompile of te2rb 0x40660 (textured polygon scan converter).
const f32=new Float32Array(1),u32=new Uint32Array(f32.buffer);
export function f32up(x){f32[0]=x;const r=f32[0];if(r>=x||x!==x)return r;u32[0]+=(r<0?-1:1);return f32[0];}  // round toward +inf (x87 RC=up store)
// m: DataView over the flat memory; item: address of the polygon item; stk: top of a free stack area (grows down, >=0x400 bytes);
// callfn(m,fnid,argp): span function, args at argp: dst,tex,count,u,v,du,dv,mask (each int32 at argp+4*i)
export function poly(m,item,stk,callfn){
let eax=item|0,ebx=0,ecx=0,edx=0,esi=0,edi=0,ebp=0,esp=stk|0,pc=0x40660;
let A=0,B=0,Fa=0,Fb=0,Fr=0,Fk=0,t=0,j=0,x=0;const st=[];
for(;;)switch(pc){''')
print(body)
print('default:throw new Error("pc "+pc.toString(16));}}')
