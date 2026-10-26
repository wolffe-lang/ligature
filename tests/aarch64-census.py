#!/usr/bin/env python3
"""Read every released compiler/runtime ELF relocation without an allowlist."""
import argparse,collections,hashlib,json,pathlib,struct
p=argparse.ArgumentParser();p.add_argument('inputs',nargs='+',type=pathlib.Path);p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args()
def elf(b,name):
 assert b[:6]==b'\x7fELF\x02\x01',(name,'not ELF64 LE')
 machine=struct.unpack_from('<H',b,18)[0];off=struct.unpack_from('<Q',b,40)[0];n,ns=struct.unpack_from('<HH',b,60)
 sh=[struct.unpack_from('<IIQQQQIIQQ',b,off+64*i) for i in range(n)];names=b[sh[ns][4]:sh[ns][4]+sh[ns][5]]
 counts=collections.Counter();examples={};section_types=collections.Counter();bindings=collections.Counter()
 for i,s in enumerate(sh):
  section_types[str(s[1])]+=1
  if s[1] in (2,11):
   for pos in range(s[4],s[4]+s[5],24):bindings[str(b[pos+4]>>4)]+=1
  if s[1]!=4:continue
  assert s[9]==24
  for pos in range(s[4],s[4]+s[5],24):
   place,info,add=struct.unpack_from('<QQq',b,pos);k=str(info&0xffffffff);counts[k]+=1
   if len(examples.setdefault(k,[]))<3:examples[k].append({'relocation_section':names[s[0]:].split(b'\0',1)[0].decode(errors='replace'),'target':s[7],'offset':place,'symbol':info>>32,'addend':add})
 return {'member':name,'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b),'machine':machine,'elf_type':struct.unpack_from('<H',b,16)[0],'relocations':dict(counts),'examples':examples,'section_types':dict(section_types),'symbol_bindings':dict(bindings)}
results=[];totals=collections.Counter()
for path in a.inputs:
 b=path.read_bytes();hashes=[hashlib.sha256(path.read_bytes()).hexdigest() for _ in range(2)];assert hashes[0]==hashes[1]
 members=[]
 if b.startswith(b'!<arch>\n'):
  at=8;names=b''
  while at<len(b):
   h=b[at:at+60];assert len(h)==60 and h[-2:]==b'`\n';name=h[:16].rstrip();size=int(h[48:58]);data=b[at+60:at+60+size];assert len(data)==size
   if name==b'//':names=data
   elif name not in (b'/',b'/SYM64/'):
    if name.startswith(b'/'):name=names[int(name[1:]):].split(b'/\n',1)[0]
    else:name=name.rstrip(b'/')
    assert data.startswith(b'\x7fELF'),(path,name,'non-ELF member')
    record=elf(data,name.decode());record['member_header_offset']=at;members.append(record)
   at+=60+size+size%2
  assert at==len(b)
 else:members=[elf(b,path.name)]
 for member in members:
  for k,count in member['relocations'].items():totals[f"{member['machine']}:{k}"]+=count
 results.append({'input':str(path),'sha256_read_twice':hashes,'members':members})
a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps({'format':'ligature.aarch64.census.v1','inputs':results,'totals':dict(totals)},indent=2)+'\n')
print('actual compiler/runtime census:',[(r['input'],len(r['members'])) for r in results]);print(json.dumps(dict(totals),sort_keys=True))
