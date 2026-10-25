#!/usr/bin/env python3
"""Independent static-link execution, overflow, GC, TLS and determinism gates."""
import hashlib,json,pathlib,struct,subprocess
ROOT=pathlib.Path(__file__).resolve().parent.parent
OUT=ROOT/'target/evidence/writer';OUT.mkdir(parents=True,exist_ok=True)
BIN=ROOT/'target/ligature'
rows=[]
def call(args,status=0,contains=None):
    p=subprocess.run(list(map(str,args)),capture_output=True,timeout=120)
    assert p.returncode==status,(args,p.returncode,p.stdout,p.stderr)
    if contains:assert contains.encode() in p.stderr,p.stderr
    return p
def asm(name,text):
    p=OUT/(name+'.s');o=OUT/(name+'.o')
    p.write_text(text+'\n.section .note.GNU-stack,"",@progbits\n')
    call(['as','--64',p,'-o',o]);return o
def run_case(name,objects,expected,options=()):
    answers={}
    for label,linker in [('ligature',BIN),('lld','ld.lld-17'),('gnu','ld.bfd')]:
        exe=OUT/(name+'-'+label)
        cmd=[linker,*(['-nostdlib'] if label=='ligature' else []),'-static','--gc-sections',*options,'-o',exe,*objects]
        call(cmd);call([BIN,'verify',exe])
        p=call([exe],expected[2]);answer=(p.stdout,p.stderr,p.returncode)
        assert answer==expected,(name,label,answer,expected)
        answers[label]={'stdout_hex':p.stdout.hex(),'stderr_hex':p.stderr.hex(),'status':p.returncode,'sha256':hashlib.sha256(exe.read_bytes()).hexdigest()}
        first=exe.read_bytes();call(cmd);assert exe.read_bytes()==first,(name,label,'nondeterministic')
    rows.append({'case':name,'outputs':answers})
    return OUT/(name+'-ligature')
start=asm('start','.text\n.global _start\n_start:\n mov choice(%rip),%edi\n mov $60,%eax\n syscall')
strong=asm('strong','.data\n.global choice\nchoice: .long 11')
weak=asm('weak','.data\n.weak choice\nchoice: .long 22')
common=asm('common','.comm choice,16,16')
for name,objs,status in [('strong-weak',[strong,weak],11),('weak-strong',[weak,strong],11),('strong-common',[strong,common],11),('common',[common],0)]:
    run_case(name,[start,*objs],(b'',b'',status))
hidden=asm('hidden-ref','.text\n.global _start\n.hidden choice\n_start: mov choice(%rip),%edi\n mov $60,%eax\n syscall')
exe=run_case('hidden-reference',[hidden,strong],(b'',b'',11))
assert b' choice' not in call(['nm','-g',exe]).stdout
# Forced roots, aliases, forward GOT and collected unreachable section.
gc=asm('gc','.section .text.start,"ax"\n.global _start\n_start: mov alias(%rip),%edi\n mov $60,%eax\n syscall\n.section .text.dead,"ax"\n.global unreachable\nunreachable: .quad missing\n.data\n.global choice\nchoice: .long 19')
exe=run_case('alias-gc',[gc],(b'',b'',19),['--defsym=alias=choice'])
assert b'unreachable' not in call(['nm',exe]).stdout
# Absolute 32S overflow and unrecognized relocation get a named refusal, not a trap.
overflow=asm('overflow','.text\n.global _start\n_start: mov $huge,%rax\n.global huge\n.set huge,0x80000000')
# Force a relocation (assembler folds same-file ABS symbols).
oref=asm('overflow-ref','.text\n.global _start\n_start: mov $huge,%rax')
odef=asm('overflow-def','.global huge\n.set huge,0x80000000')
call([BIN,'-nostdlib','-o',OUT/'overflow',oref,odef],1,'relocation overflow')
unsupported=asm('unsupported','.text\n.global _start\n_start: .word choice\n.data\n.global choice\nchoice: .long 0')
call([BIN,'-nostdlib','-o',OUT/'unsupported',unsupported],1,'table 4.9')
# Real musl startup, constructor order and all static TLS access models.
source=OUT/'tls.c'
source.write_text('#include <stdio.h>\n__thread int tls=7; static __thread int local; int value;\n__attribute__((constructor)) static void init(void) { value=35; local=3; }\nint main(void) { printf("writer %d %d\\n",tls+value,local); return 0; }\n')
lib=pathlib.Path('/usr/lib/x86_64-linux-musl')
for model in ('local-exec','initial-exec','global-dynamic','local-dynamic'):
    obj=OUT/(model+'.o')
    call(['musl-gcc','-c','-fPIC','-ffunction-sections','-fdata-sections',f'-ftls-model={model}',source,'-o',obj])
    exe=run_case(model,[lib/'crt1.o',lib/'crti.o',obj,lib/'libc.a',lib/'crtn.o'],(b'writer 42 3\n',b'',0))
    records=[json.loads(x) for x in call([BIN,'inspect',exe]).stdout.splitlines()]
    tls=next(r for r in records if r['row']=='program' and r['kind']==7)
    data=bytearray(exe.read_bytes());phoff=struct.unpack_from('<Q',data,32)[0]
    struct.pack_into('<Q',data,phoff+tls['index']*56+32,0)
    bad=OUT/(model+'-bad-template');bad.write_bytes(data)
    call([BIN,'verify',bad],1,'TLS')
(OUT/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
print(f'writer: {len(rows)} three-linker behavior rows, determinism, named refusals and TLS-negative rows; 0 SKIP')
