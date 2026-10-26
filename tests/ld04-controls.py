#!/usr/bin/env python3
"""Explicit supplementary controls: clang/LLD 18 required, no execution claims.
Run in the observed as02b-rust image. This is not the hosted/core gate and does
not substitute for a kernel link, actual runtime census or AArch64 behavior.
"""
import collections, hashlib, json, pathlib, struct, subprocess
ROOT=pathlib.Path(__file__).resolve().parent.parent
OUT=ROOT/'target/evidence/ld04-controls';OUT.mkdir(parents=True,exist_ok=True)
BIN=ROOT/'target/ligature'; commands=[]
def run(args, status=0):
    p=subprocess.run(list(map(str,args)),capture_output=True,timeout=60)
    commands.append({'argv':list(map(str,args)),'status':p.returncode,'stdout':p.stdout.decode(errors='replace'),'stderr':p.stderr.decode(errors='replace')})
    if status is not None: assert p.returncode==status,commands[-1]
    return p
versions={x:run([x,'--version']).stdout.decode() for x in ('clang-18','ld.lld-18','ld.bfd','readelf')}
assert '18.1.3' in versions['ld.lld-18'],versions
# Same high-half boundary as the existing LLD17/GNU control, not a kernel source.
edge=OUT/'edge.s';script=OUT/'edge.ld';obj=OUT/'edge.o'
edge.write_text('.text\n.global _start\n_start: mov far@GOTPCREL(%rip),%rax\nret\n.section .far,"a",@progbits\n.global far\n.type far,@object\nfar: .quad 0\n.section .note.GNU-stack,"",@progbits\n')
script.write_text('ENTRY(_start)\nPHDRS { far PT_LOAD FLAGS(4); text PT_LOAD FLAGS(5); data PT_LOAD FLAGS(6); }\nSECTIONS { .far 0xffffffff00000003 : { *(.far) } :far\n.text 0xffffffff80000000 : { *(.text) } :text\n.got 0xffffffff80001000 : { *(.got) } :data\n/DISCARD/ : { *(.note.GNU-stack) } }\n')
run(['as','--64','-o',obj,edge]);p=run(['ld.lld-18','-static','-T',script,'-o',OUT/'edge-lld18',obj],None)
edge_result={'status':p.returncode,'stderr':p.stderr.decode(),'executed':False}
assert p.returncode == 0, edge_result
edge_result['view']=run(['readelf','-hW','-x','.text','-x','.got',OUT/'edge-lld18']).stdout.decode()
assert '488b05f9 0f0000c3' in edge_result['view'] and '03000000 ffffffff' in edge_result['view'], edge_result
# Produce actual AArch64 machine instructions and relocations, not patched headers.
fixtures={
'core': '''.text
.global _start
_start:
 bl target
 b target
 adrp x0, value
 add x0, x0, :lo12:value
 adrp x1, value
 ldr x1, [x1, :lo12:value]
.data
.quad value
.word target - .
''',
'definitions': '''.text
.global target
target: mov x0, #0
 mov x8, #93
 svc #0
.data
.balign 8
.global value
value: .quad 42
''',
'got': '''.text
.global got_probe
got_probe:
 adrp x0, :got:value
 ldr x0, [x0, :got_lo12:value]
 ret
''',
}
objects=[]
def census(path):
    b=path.read_bytes();assert struct.unpack_from('<H',b,18)[0]==183
    off=struct.unpack_from('<Q',b,40)[0];num=struct.unpack_from('<H',b,60)[0]
    sections=[struct.unpack_from('<IIQQQQIIQQ',b,off+64*i) for i in range(num)]
    relocs=[]
    for i,s in enumerate(sections):
        if s[1]!=4:continue
        for at in range(s[4],s[4]+s[5],24):
            place,info,addend=struct.unpack_from('<QQq',b,at)
            relocs.append({'table':i,'target_section':s[7],'offset':place,'symbol':info>>32,'type':info&0xffffffff,'addend':addend})
    return {'file':path.name,'sha256':hashlib.sha256(b).hexdigest(),'machine':183,'relocations':relocs,'readelf':run(['readelf','-rW',path]).stdout.decode()}
for name,source in fixtures.items():
    src=OUT/(name+'.s');o=OUT/(name+'.o');src.write_text(source)
    run(['clang-18','--target=aarch64-linux-gnu','-c',src,'-o',o]);objects.append(census(o))
core_types={r['type'] for r in objects[0]['relocations']}
assert core_types=={257,261,275,277,282,283,286},core_types
assert {r['type'] for r in objects[2]['relocations']}=={311,312}
run([BIN,'roundtrip',OUT/'core.o']);run([BIN,'roundtrip',OUT/'definitions.o'])
got=run([BIN,'roundtrip',OUT/'got.o'],1);assert b'unsupported AArch64 relocation 311' in got.stderr
run([BIN,'archive',OUT/'core.a',OUT/'core.o',OUT/'definitions.o']);run([BIN,'roundtrip',OUT/'core.a'])
run(['ld.lld-18','-static','--no-relax','--emit-relocs','-o',OUT/'aarch64-oracle',OUT/'core.a'])
assert struct.unpack_from('<H',(OUT/'aarch64-oracle').read_bytes(),18)[0]==183
run([BIN,'verify',OUT/'aarch64-oracle'])
refusal=run([BIN,'-nostdlib','-u','_start','-o',OUT/'must-not-exist',OUT/'core.a'],1)
assert b'EM_AARCH64 linking refused' in refusal.stderr
assert not (OUT/'must-not-exist').exists()
result={'scope':'own assembly fixtures only; not the compiler/runtime AArch64 input census','versions':versions,'kernel_edge_lld18':edge_result,'aarch64':objects,'aarch64_oracle_executed':False,'candidate_aarch64_linking':False,'commands':commands}
(OUT/'results.json').write_text(json.dumps(result,indent=2)+'\n')
print('ld04 supplementary controls: LLD18 kernel edge status',edge_result['status'],'; actual AArch64 relocation types',sorted(core_types|{311,312}),'; archive and oracle ELF verified; execution NOT RUN')
