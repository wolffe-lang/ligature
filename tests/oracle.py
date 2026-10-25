#!/usr/bin/env python3
"""Distro-musl oracle, deterministic links and deliberate-difference witnesses."""
import hashlib,json,pathlib,shutil,struct,subprocess
ROOT=pathlib.Path(__file__).resolve().parent.parent
OUT=ROOT/'target/evidence/distro-oracle';OUT.mkdir(parents=True,exist_ok=True)
BIN=ROOT/'target/ligature';DIFFER=ROOT/'tools/differ'

def call(args,status=0):
    p=subprocess.run(list(map(str,args)),capture_output=True,timeout=60)
    assert p.returncode==status,(list(map(str,args)),p.returncode,p.stdout,p.stderr)
    return p

source=OUT/'hello.c'
source.write_text('#include <stdio.h>\n__thread int tls = 7;\nint value;\n__attribute__((constructor)) static void init(void) { value = 35; }\nint main(void) { printf("oracle %d\\n", tls + value); return 0; }\n')
obj=OUT/'hello.o';call(['musl-gcc','-c','-ffunction-sections','-fdata-sections',source,'-o',obj])
# rustc also emits INIT_ARRAY with sh_entsize=0; byte width still must be 8.
raw=bytearray(obj.read_bytes());shoff=struct.unpack_from('<Q',raw,40)[0];count=struct.unpack_from('<H',raw,60)[0]
arrays=[i for i in range(count) if struct.unpack_from('<I',raw,shoff+i*64+4)[0]==14]
assert arrays
struct.pack_into('<Q',raw,shoff+arrays[0]*64+56,0)
zero=OUT/'zero-array-entsize.o';zero.write_bytes(raw);call([BIN,'roundtrip',zero])
lib=pathlib.Path('/usr/lib/x86_64-linux-musl')
outputs=[]
for name,linker in [('lld','ld.lld-17'),('gnu','ld.bfd')]:
    exe=OUT/name
    cmd=[linker,'-static','--emit-relocs','--gc-sections','-o',exe,lib/'crt1.o',lib/'crti.o',obj,lib/'libc.a',lib/'crtn.o']
    call(cmd);call([BIN,'verify',exe]);run=call([exe]);assert run.stdout==b'oracle 42\n' and run.stderr==b''
    call([DIFFER,exe,exe,'--output',OUT/(name+'-self.json')])
    first=exe.read_bytes();call(cmd);assert first==exe.read_bytes(),'nondeterministic link'
    rows=[json.loads(x) for x in call([BIN,'inspect',exe]).stdout.splitlines()]
    # Flip an allocated constant byte, not an ELF header or unallocated padding.
    ro=next(r for r in rows if r['row']=='section' and r['name']=='.rodata')
    bad=OUT/(name+'-flipped');data=bytearray(first);data[ro['offset']]^=1;bad.write_bytes(data);bad.chmod(0o755)
    call([BIN,'verify',bad])
    call([DIFFER,exe,bad,'--output',OUT/(name+'-flip.json')],1)
    wrong=OUT/(name+'-entry');data=bytearray(first);struct.pack_into('<Q',data,24,1);wrong.write_bytes(data)
    p=call([BIN,'verify',wrong],1);assert b'entry outside executable' in p.stderr
    # A TLS descriptor cannot overstate initialized or in-memory bytes.
    tls=next(r for r in rows if r['row']=='program' and r['kind']==7)
    data=bytearray(first);phoff=struct.unpack_from('<Q',data,32)[0];struct.pack_into('<Q',data,phoff+tls['index']*56+40,tls['memsz']+8)
    wrong.write_bytes(data);p=call([BIN,'verify',wrong],1);assert b'PT_TLS memory template' in p.stderr
    outputs.append({'oracle':name,'sha256':hashlib.sha256(first).hexdigest(),'stdout':run.stdout.decode(),'status':run.returncode,'plant':'allocated-byte flip red; entry and TLS corruption red'})
# Cross-oracle differences are recorded, never silently accepted as equivalent.
p=subprocess.run([str(DIFFER),str(OUT/'lld'),str(OUT/'gnu'),'--output',str(OUT/'cross.json')],capture_output=True,timeout=60)
assert p.returncode in (0,1),p.stderr
(OUT/'results.json').write_text(json.dumps(outputs,indent=2)+'\n')
print('oracle: 2 musl links, 2 deterministic relinks, 2 differ plants, 4 verify plants, 0 SKIP')
