#!/usr/bin/env python3
"""Real high-half executable links; no high-half executable is run by this test."""
import hashlib,json,pathlib,runpy,struct,subprocess
R=pathlib.Path(__file__).resolve().parent.parent; O=R/'target/evidence/kernel-script';O.mkdir(parents=True,exist_ok=True)
B=R/'target/ligature'; SCRIPT=R/'tests/fixtures/pax-kernel.ld'
codec=runpy.run_path(str(R/'tests/manifest-codec.py'));snapshot=runpy.run_path(str(R/'tools/differ'))['snapshot'];rows=[]
def call(args,status=0,reason=None):
 p=subprocess.run(list(map(str,args)),capture_output=True,timeout=120)
 assert p.returncode==status,(args,p.returncode,p.stderr)
 if reason:assert reason.encode() in p.stderr,(args,p.stderr)
 rows.append({'argv':list(map(str,args)),'status':p.returncode,'stdout':p.stdout.decode(errors='replace'),'stderr':p.stderr.decode(errors='replace')});return p

def elf(path):
 b=path.read_bytes();off=struct.unpack_from('<Q',b,40)[0];n,ns=struct.unpack_from('<HH',b,60)
 sh=[struct.unpack_from('<IIQQQQIIQQ',b,off+64*i) for i in range(n)];pool=b[sh[ns][4]:sh[ns][4]+sh[ns][5]]
 secs={pool[s[0]:].split(b'\0',1)[0].decode():s for s in sh};ph=struct.unpack_from('<Q',b,32)[0]
 loads=[struct.unpack_from('<IIQQQQQQ',b,ph+56*i) for i in range(struct.unpack_from('<H',b,56)[0])];return b,secs,[p for p in loads if p[0]==1]

def obj(name,text):
 s=O/(name+'.s');p=O/(name+'.o');s.write_text(text+'\n.section .note.GNU-stack,"",@progbits\n');call(['as','--64',s,'-o',p]);return p
first=obj('first','''.text
.global _start
_start: mov target@GOTPCREL(%rip),%rax
ret
.data
.global ordinary
ordinary: .quad target
.section .rodata,"a",@progbits
.global target
target: .quad 42
.section .debug_probe,"",@progbits
.quad target
.section .comment,"",@progbits
.asciz "explicit discard"
.section .eh_frame,"a",@progbits
.long 0
''')
second=obj('second','''.section .data.limine,"aw",@progbits
.global limine_first
limine_first: .quad 55
.section .data.rel.ro,"aw",@progbits
.quad _start
.bss
.balign 16
.space 17
.comm common,32,16
''')
outputs={};bounds={};names=['__pax_image_start','__pax_text_start','__pax_text_end','__pax_rodata_start','__pax_rodata_end','__pax_data_start','__pax_image_end']
for label,ld in [('candidate',B),('lld17','ld.lld-17'),('gnu','ld.bfd')]:
 out=O/label;args=[ld,'-static','-T',SCRIPT,'-o',out,first,second]
 if label=='candidate':args.insert(1,'-nostdlib')
 else:args.insert(1,'--emit-relocs')
 call(args);b,secs,loads=elf(out);outputs[label]=out
 assert struct.unpack_from('<Q',b,24)[0]==0xffffffff80000000
 assert [p[1] for p in loads]==[5,4,6]
 assert all(p[2]%4096==p[3]%4096==0 for p in loads)
 assert all((p[3]+p[6]+4095)//4096<=q[3]//4096 for p,q in zip(loads,loads[1:]))
 syms={line.split()[-1]:int(line.split()[0],16) for line in call(['nm','-n',out]).stdout.decode().splitlines() if len(line.split())==3}
 assert syms['limine_first']<syms['ordinary'] and syms['common']%16==0
 assert not {'.comment','.eh_frame','.note.GNU-stack'}&secs.keys()
 assert secs['.bss'][1]==8 and loads[2][6]>loads[2][5]
 bounds[label]={name:syms[name] for name in names}
 assert all(v%4096==0 for v in bounds[label].values())
 assert syms['__pax_text_start']<=loads[0][3] and loads[0][3]+loads[0][6]<=syms['__pax_text_end']
 assert syms['__pax_rodata_start']<=loads[1][3] and loads[1][3]+loads[1][6]<=syms['__pax_rodata_end']
 assert syms['__pax_data_start']<=loads[2][3] and loads[2][3]+loads[2][6]<=syms['__pax_image_end']
 if label=='candidate':
  call([B,'verify',out]);v=snapshot(out);assert not v['refused'],v['refused']
  for name in names:
   origin=json.loads(call([B,'explain',out,'--symbol',name]).stdout)[0]
   assert int(origin['address'])==syms[name] and origin['origin']=='script-symbol'
  result=json.loads(call([B,'explain',out,'--address','0xffffffff80000000']).stdout);assert result
  for name in ('.comment','.eh_frame','.note.GNU-stack'):
   records=json.loads(call([B,'explain',out,'--discarded',name]).stdout)
   assert all(r['reason']=='script-DISCARD' for r in records)
assert bounds['candidate']==bounds['lld17']==bounds['gnu'],bounds
again=O/'repeat';call([B,'-nostdlib','-T',SCRIPT,'-o',again,first,second]);assert again.read_bytes()==outputs['candidate'].read_bytes()
for name,source,reason in [('orphan','.section .orphan,"a",@progbits\n.quad 0','allocated orphan'),('tls','.section .tdata,"awT",@progbits\n.quad 0','allocated orphan'),('conflict','.global __pax_image_end\n.set __pax_image_end,1','conflicts')]:
 bad=obj(name,source);sentinel=O/'sentinel';sentinel.write_bytes(b'unchanged');call([B,'-nostdlib','-T',SCRIPT,'-o',sentinel,first,bad],1,reason);assert sentinel.read_bytes()==b'unchanged'
call([B,'-T',SCRIPT,first],1,'requires -nostdlib');call([B,'-nostdlib','-T',SCRIPT,'-T',SCRIPT,first],1,'duplicate -T')
# Forge the high-half metadata after rounding it, and re-seal both hashes.
b,secs,_=elf(outputs['candidate']);b=bytearray(b);m=secs['.wolf.link.manifest'];no=secs['.note.wolf.link'][4]
doc=codec['decode'](b[m[4]:m[4]+m[5]]);doc['sections'][0]['address']=str(0xffffffff80000001)
raw=codec['encode'](doc,m[5]);b[m[4]:m[4]+m[5]]=raw;b[no+44:no+108]=bytes(64);whole=hashlib.sha256(b).digest();b[no+44:no+76]=hashlib.sha256(raw).digest();b[no+76:no+108]=whole
bad=O/'rounded-metadata';bad.write_bytes(b);call([B,'verify',bad],1,'address differs')
(O/'results.json').write_text(json.dumps({'bounds':bounds,'processes':rows,'executed':False},indent=2)+'\n')
print('kernel-script: three executable links, u64 provenance, bounds, permissions, ordering, discards, independent sites, deterministic bytes and refusals; 0 SKIP')
