#!/usr/bin/env python3
"""Record black-box high-half GOT relaxation; never execute a kernel-address ELF."""
import json,pathlib,subprocess
ROOT=pathlib.Path(__file__).resolve().parent.parent
OUT=ROOT/'target/evidence/kernel-edge';OUT.mkdir(parents=True,exist_ok=True)
asm=OUT/'edge.s';script=OUT/'edge.ld';obj=OUT/'edge.o'
asm.write_text('.text\n.global _start\n_start: mov far@GOTPCREL(%rip),%rax\nret\n.section .far,"a",@progbits\n.global far\n.type far,@object\nfar: .quad 0\n.section .note.GNU-stack,"",@progbits\n')
script.write_text('ENTRY(_start)\nPHDRS { far PT_LOAD FLAGS(4); text PT_LOAD FLAGS(5); data PT_LOAD FLAGS(6); }\nSECTIONS { .far 0xffffffff00000003 : { *(.far) } :far\n.text 0xffffffff80000000 : { *(.text) } :text\n.got 0xffffffff80001000 : { *(.got) } :data\n/DISCARD/ : { *(.note.GNU-stack) } }\n')
subprocess.run(['as','--64','-o',obj,asm],check=True)
rows=[]
for name,ld,options in [('lld17','ld.lld-17',[]),('gnu','ld.bfd',[]),('gnu-no-relax','ld.bfd',['--no-relax'])]:
    exe=OUT/name
    p=subprocess.run([ld,'-static',*options,'-T',script,'-o',exe,obj],capture_output=True)
    row={'oracle':name,'status':p.returncode,'stdout':p.stdout.decode(),'stderr':p.stderr.decode()}
    if p.returncode==0:
        row['view']=subprocess.check_output(['readelf','-hW','-x','.text','-x','.got',exe],text=True)
    rows.append(row)
(OUT/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
assert rows[0]['status']!=0 and '-2147483652' in rows[0]['stderr'],rows[0]
assert rows[1]['status']!=0 and 'failed to convert GOTPCREL' in rows[1]['stderr'],rows[1]
assert rows[2]['status']==0,rows[2]
assert '488b05' in rows[2]['view'] and '03000000 ffffffff' in rows[2]['view'],rows[1]
print('kernel edge: lld17 refuses -2147483652; GNU default refuses, GNU --no-relax keeps GOT load; LLD18 control is separate in tests/ld04-controls.py')
