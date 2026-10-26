#!/usr/bin/env python3
"""Independent ELF fixtures: all nine implementations and exact ABI endpoints."""
import json,pathlib,runpy,struct,subprocess
R=pathlib.Path(__file__).resolve().parent.parent;O=R/'target/evidence/aarch64';O.mkdir(parents=True,exist_ok=True);B=R/'target/ligature'
helper=runpy.run_path(str(R/'tests/aarch64-sites.py'));validate=helper['validate'];P=0x201000;rows=[]
def object_file(path,code,relocs,value=P,machine=183):
 names=b'\0.text\0.rela.text\0.symtab\0.strtab\0.shstrtab\0';labels=b'\0_start\0target\0'
 syms=bytes(24)+struct.pack('<IBBHQQ',1,0x12,0,1,0,len(code))+struct.pack('<IBBHQQ',8,0x11,0,0xfff1,value,0)
 rela=b''.join(struct.pack('<QQq',off,(2<<32)|kind,a) for off,kind,a in relocs)
 bodies=[b'',code,rela,syms,labels,names];out=bytearray(64);sections=[bytes(64)]
 for i in range(1,6):
  out.extend(bytes((-len(out))%8));offset=len(out);out.extend(bodies[i]);kind=[0,1,4,2,3,3][i]
  sections.append(struct.pack('<IIQQQQIIQQ',names.index([b'',b'.text',b'.rela.text',b'.symtab',b'.strtab',b'.shstrtab'][i]),kind,6 if i==1 else 0,0,offset,len(bodies[i]),3 if i==2 else 4 if i==3 else 0,1 if i in (2,3) else 0,4 if i==1 else 8 if i in (2,3) else 1,24 if i in (2,3) else 0))
 out.extend(bytes((-len(out))%8));shoff=len(out);out.extend(b''.join(sections))
 out[:64]=b'\x7fELF\x02\x01\x01'+bytes(9)+struct.pack('<HHIQQQIHHHHHH',1,machine,1,0,0,shoff,0,64,0,0,64,6,5);path.write_bytes(out)
def case(name,code,relocs,value=P,reason=None):
 obj=O/(name+'.o');out=O/name;object_file(obj,code,relocs,value)
 out.write_bytes(b'unchanged')
 p=subprocess.run([B,'-nostdlib','-o',out,obj],capture_output=True,timeout=30)
 if reason:
  assert p.returncode==1 and reason.encode() in p.stderr,(name,p.returncode,p.stderr)
  assert out.read_bytes()==b'unchanged'
 else:
  assert p.returncode==0,(name,p.stderr);validate(out)
 rows.append({'name':name,'status':p.returncode,'stderr':p.stderr.decode()});return out
word=lambda n:struct.pack('<I',n)
for k,opcode in [(282,0x14000000),(283,0x94000000)]:
 for label,delta in [('min',-2**27),('max',2**27-4),('zero',0)]:case(f'{k}-{label}',word(opcode),[(0,k,delta)])
 for label,delta in [('under',-2**27-4),('over',2**27)]:case(f'{k}-{label}',word(opcode),[(0,k,delta)],reason='branch range')
 case(f'{k}-target-align',word(opcode),[(0,k,2)],reason='target alignment')
 case(f'{k}-mask',word(0xd65f03c0),[(0,k,0)],reason='instruction mask')
 case(f'{k}-site-align',b'x'+word(opcode),[(1,k,0)],reason='relocation alignment')
for label,delta in [('min',-2**31),('max',2**32-1),('unsigned',2**31)]:case('prel-'+label,bytes(4),[(0,261,delta)])
for label,delta in [('under',-2**31-1),('over',2**32)]:case('prel-'+label,bytes(4),[(0,261,delta)],reason='PREL32 overflow')
case('abs-max',bytes(8),[(0,257,0)],2**64-1)
case('abs-wrap',bytes(8),[(0,257,1)],2**64-1)
case('abs-negative',bytes(8),[(0,257,-1)],0)
case('abs-unaligned',b'x'+bytes(8),[(1,257,0)],0x123456789abcdef0)
case('prel-unaligned',b'x'+bytes(4),[(1,261,1)])
for label,delta in [('min',-2**32),('max',2**32-4096),('negative-low',-1)]:case('adrp-'+label,word(0x90000000),[(0,275,delta)])
for label,delta in [('under',-2**32-4096),('over',2**32)]:case('adrp-'+label,word(0x90000000),[(0,275,delta)],reason='ADRP range')
case('adrp-mask',word(0x10000000),[(0,275,0)],reason='instruction mask')
for k,low in [(277,0x91000000),(286,0xf9400000),(312,0xf9400000)]:
 high=311 if k==312 else 275
 case(f'pair-{k}',word(0x90000000)+word(low),[(0,high,0),(4,k,0)],P+0x1ff8)
 case(f'pair-{k}-register',word(0x90000001)+word(low),[(0,high,0),(4,k,0)],reason='register')
 case(f'pair-{k}-missing',word(low),[(0,k,0)],reason='preceding ADRP')
 case(f'pair-{k}-addend',word(0x90000000)+word(low),[(0,high,0),(4,k,8)],reason='GOT addend' if k==312 else 'addend mismatch')
case('ldst-align',word(0x90000000)+word(0xf9400000),[(0,275,0),(4,286,0)],P+1,reason='target alignment')
case('add-mask',word(0x90000000)+word(0x91400000),[(0,275,0),(4,277,0)],reason='instruction mask')
case('load-mask',word(0x90000000)+word(0xb9400000),[(0,275,0),(4,286,0)],reason='instruction mask')
case('unknown',word(0),[(0,313,0)],reason='unsupported AArch64 relocation 313')
case('tls',word(0),[(0,541,0)],reason='unsupported AArch64 relocation 541')
(O/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
print(f'aarch64: {len(rows)} independent ELF/range/alignment/mask/pair/GOT/refusal rows; no fixture execution claimed, 0 SKIP')
