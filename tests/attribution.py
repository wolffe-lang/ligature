#!/usr/bin/env python3
"""Whole-byte attribution, resealed negative manifests, queries and change locality."""
import runpy,copy,hashlib,json,pathlib,struct,subprocess
ROOT=pathlib.Path(__file__).resolve().parent.parent;BIN=ROOT/'target/ligature'
codec=runpy.run_path(str(ROOT/'tests/manifest-codec.py'));decode_manifest=codec['decode'];encode_manifest=codec['encode']
OUT=ROOT/'target/evidence/attribution';OUT.mkdir(parents=True,exist_ok=True)
def call(args,status=0):
    p=subprocess.run(list(map(str,args)),capture_output=True,timeout=180)
    assert p.returncode==status,(args,p.returncode,p.stdout,p.stderr)
    return p

def decode(path):
    data=path.read_bytes();shoff=struct.unpack_from('<Q',data,40)[0];n,ns=struct.unpack_from('<HH',data,60)
    headers=[struct.unpack_from('<IIQQQQIIQQ',data,shoff+64*i) for i in range(n)]
    names=headers[ns];text=data[names[4]:names[4]+names[5]]
    sections={text[h[0]:].split(b'\0',1)[0].decode():h for h in headers}
    m=sections['.wolf.link.manifest'];doc=decode_manifest(data[m[4]:m[4]+m[5]])
    return data,sections,doc

def reseal(data,sections):
    data=bytearray(data);n=sections['.note.wolf.link'][4];m=sections['.wolf.link.manifest']
    data[n+44:n+108]=bytes(64);whole=hashlib.sha256(data).digest()
    data[n+44:n+76]=hashlib.sha256(data[m[4]:m[4]+m[5]]).digest();data[n+76:n+108]=whole
    return data

source=OUT/'change.s';obj=OUT/'change.o';exe=OUT/'program'
def link(value):
    source.write_text(f'''.text
.global _start
_start: mov $60,%eax
 xor %edi,%edi
 syscall
.data
.global target,pointer
pointer: .quad target
target: .quad {value}
.section .note.GNU-stack,"",@progbits
''')
    call(['as','--64',source,'-o',obj]);call([BIN,'-nostdlib','-o',exe,obj])
    return decode(exe)
a,sections,doc=link(41)
assert doc['coverage']=='bytes-and-patches'
assert a[sections['.wolf.link.manifest'][4]:][:sections['.wolf.link.manifest'][5]]==encode_manifest(doc)
cursor=0
for r in doc['ranges']:
    assert r['start']==cursor and r['end']>cursor;rsize=r['end']-r['start'];cursor=r['end']
    if r['origin']=='input':
        member=doc['members'][r['member']]
        assert 0<=r['input_offset']<=member['size']-rsize
assert cursor==len(a)
for p in doc['patches']:assert a[p['start']:p['end']].hex()==p['after']
assert doc['patches']
symbols=json.loads(call([BIN,'explain',exe,'--symbol','target']).stdout)
assert len(symbols)==1 and symbols[0]['name']=='target'
address=symbols[0]['address']
answer=json.loads(call([BIN,'explain',exe,'--address',hex(address)]).stdout)
assert any(x.get('name')=='target' for x in answer)
assert json.loads(call([BIN,'explain',exe,'--why','target']).stdout)
call([BIN,'explain',exe,'--symbol','absent'],1)
call([BIN,'explain',exe,'--address','0xffffffffffffffffffff'],1)
call([BIN,'-nostdlib','-o',exe,obj]);assert exe.read_bytes()==a
b,sections2,doc2=link(42)
assert len(a)==len(b)
allowed=[]
for name in ('.data','.wolf.link.manifest','.note.wolf.link'):
    h=sections[name];allowed.append((h[4],h[4]+h[5]))
deltas=[i for i,(x,y) in enumerate(zip(a,b)) if x!=y]
assert deltas and all(any(lo<=i<hi for lo,hi in allowed) for i in deltas),deltas
# Re-seal intentional lies: a digest proves integrity, not truth or authorship.
mutations=[]
gap=copy.deepcopy(doc2);gap['ranges'][1]['start']+=1;mutations.append(('gap',gap))
overlap=copy.deepcopy(doc2);overlap['ranges'][1]['start']-=1;mutations.append(('overlap',overlap))
wrong=copy.deepcopy(doc2);next(r for r in wrong['ranges'] if r['origin']=='input')['input_offset']=-1;mutations.append(('input-slice',wrong))
wrong=copy.deepcopy(doc2);p=wrong['patches'][0];p['after']=('00' if p['after'][:2]!='00' else '01')+p['after'][2:];mutations.append(('patch-bytes',wrong))
wrong=copy.deepcopy(doc2);wrong['coverage']='unknown';mutations.append(('coverage',wrong))
wrong=copy.deepcopy(doc2);wrong['patches'].pop();mutations.append(('dropped-provenance-record',wrong))
for name,record in mutations:
    raw=encode_manifest(record);m=sections2['.wolf.link.manifest']
    assert len(raw)<=m[5],(name,len(raw),m[5])
    data=bytearray(b);data[m[4]:m[4]+m[5]]=raw+bytes(m[5]-len(raw));data=reseal(data,sections2)
    path=OUT/('bad-'+name);path.write_bytes(data)
    call([BIN,'verify',path],1)
    p=call([BIN,'explain',path,'--symbol','target'],2);assert not p.stdout
(OUT/'results.json').write_text(json.dumps({'ranges':len(doc['ranges']),'patches':len(doc['patches']),'negative_rows':[x[0] for x in mutations],'changed_bytes':len(deltas),'manifest_bytes':sections['.wolf.link.manifest'][5]},indent=2)+'\n')
print('attribution: complete disjoint coverage, explain, deterministic relink, delta locality, five resealed negative rows; 0 SKIP')
alias=ROOT/'target/evidence/writer/alias-gc-ligature'
rows=json.loads(call([BIN,'explain',alias,'--symbol','alias']).stdout)
assert rows[0]['alias_of']=='choice'
chain=ROOT/'target/evidence/lazy-order/forward'
rows=json.loads(call([BIN,'explain',chain,'--why','c']).stdout)
assert rows and rows[0]['member']=='c.o' and all(x['parent']<x['object'] for x in rows)
tls=ROOT/'target/evidence/writer/local-exec-ligature'
_,_,tdoc=decode(tls)
local=next(s for s in tdoc['symbols'] if s['tls'] and s['nobits'])
rows=json.loads(call([BIN,'explain',tls,'--symbol',local['name'],'--input',str(local['member'])]).stdout)
assert rows[0]['tls'] and rows[0]['nobits'] and rows[0]['file_start']==-1
others=[]
for index in (1,2):
    src=OUT/f'local{index}.s';o=OUT/f'local{index}.o'
    src.write_text('.data\n.local duplicate\nduplicate: .quad 1\n.section .note.GNU-stack,"",@progbits\n')
    call(['as','--64',src,'-o',o]);others.append(o)
ambiguous=OUT/'ambiguous';call([BIN,'-nostdlib','-o',ambiguous,obj,*others])
call([BIN,'explain',ambiguous,'--symbol','duplicate'],1)
rows=json.loads(call([BIN,'explain',ambiguous,'--symbol','duplicate','--input','1']).stdout)
assert len(rows)==1 and rows[0]['member']==1
print('attribution: aliases, archive path, TLS/NOBITS, ambiguous locals and explicit member selection; 0 SKIP')

# Legacy JSON is still accepted by verify and every explain query.
legacy=json.dumps(doc2,sort_keys=True,separators=(',',':')).encode()
m=sections2['.wolf.link.manifest'];assert len(legacy)<=m[5]
old=bytearray(b);old[m[4]:m[4]+m[5]]=legacy+b' '*(m[5]-len(legacy));old=reseal(old,sections2)
oldpath=OUT/'legacy-json';oldpath.write_bytes(old)
call([BIN,'verify',oldpath])
for mode,value in [('--symbol','target'),('--address',hex(address)),('--why','target')]:
    assert json.loads(call([BIN,'explain',oldpath,mode,value]).stdout)==json.loads(call([BIN,'explain',exe,mode,value]).stdout)
print('compact-manifest: legacy JSON explain parity and dropped provenance record refused; 0 SKIP')
# Dependency queries expose the original section's relocation causes, not just archive pulls.
rows=json.loads(call([BIN,'explain',exe,'--dependencies','pointer']).stdout)
assert rows and rows[0]['symbol']=='target'
# GC and SHF_EXCLUDE have distinct causes; metadata regeneration is not GC.
source.write_text('''.text
.global _start
_start: mov $60,%eax
xor %edi,%edi
syscall
.section .text.dead,"ax",@progbits
ret
.section .excluded,"e",@progbits
.byte 1
.section .note.GNU-stack,"",@progbits
''')
call(['as','--64',source,'-o',obj]);gc=OUT/'gc-causes'
call([BIN,'-nostdlib','--gc-sections','-o',gc,obj])
for section,reason in [('.text.dead','GC-unreachable'),('.excluded','SHF_EXCLUDE'),('.note.GNU-stack','consumed-stack-policy'),('.symtab','regenerated-metadata')]:
    rows=json.loads(call([BIN,'explain',gc,'--discarded',section]).stdout)
    assert len(rows)==1 and rows[0]['reason']==reason,(section,rows)
print('explain: dependency sites and distinct discarded-section causes; 0 SKIP')
