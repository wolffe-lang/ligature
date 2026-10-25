#!/usr/bin/env python3
"""Black-box merge-string, unwind and permitted PAX script observations."""
import hashlib,json,pathlib,struct,subprocess
ROOT=pathlib.Path(__file__).resolve().parent.parent;OUT=ROOT/'target/evidence/layout-controls';OUT.mkdir(parents=True,exist_ok=True)
def call(args):
    r=subprocess.run(list(map(str,args)),capture_output=True);assert r.returncode==0,(args,r.stderr);return r.stdout
def elf(path):
    b=path.read_bytes();sh=struct.unpack_from('<Q',b,40)[0];n,ns=struct.unpack_from('<HH',b,60);hs=[struct.unpack_from('<IIQQQQIIQQ',b,sh+64*i) for i in range(n)]
    h=hs[ns];names=b[h[4]:h[4]+h[5]];secs={names[h[0]:].split(b'\0',1)[0].decode():h for h in hs}
    ph=struct.unpack_from('<Q',b,32)[0];pn=struct.unpack_from('<H',b,56)[0];loads=[struct.unpack_from('<IIQQQQQQ',b,ph+56*i) for i in range(pn)]
    return b,secs,loads
source=OUT/'controls.s';obj=OUT/'controls.o'
source.write_text('''.text
.global _start
.type _start,@function
_start:
.cfi_startproc
mov $60,%eax
xor %edi,%edi
syscall
.cfi_endproc
.size _start,.-_start
.section .rodata.str1.1,"aMS",@progbits,1
.global first,second,suffix
first: .asciz "shared-tail"
second: .asciz "shared-tail"
suffix: .asciz "tail"
.data
.quad first,second,suffix
.section .note.GNU-stack,"",@progbits
''')
call(['as','--64',source,'-o',obj]);rows=[]
for name,ld in [('ligature',ROOT/'target/ligature'),('lld','ld.lld-17'),('gnu','ld.bfd')]:
    out=OUT/name;args=[ld,'-static','-o',out,obj]
    if name!='ligature':args+=['--emit-relocs','--eh-frame-hdr']
    else:args+=['-nostdlib']
    call(args);assert call([out])==b''
    b,secs,loads=elf(out);ro=secs['.rodata'];rows.append({'oracle':name,'rodata_bytes':ro[5],'rodata_hex':b[ro[4]:ro[4]+ro[5]].hex(),'eh_frame_bytes':secs['.eh_frame'][5],'eh_frame_hdr':'.eh_frame_hdr' in secs,'symbols':call(['nm','-n',out]).decode()})
assert rows[0]['rodata_bytes']==29 and not rows[0]['eh_frame_hdr'],rows
assert all(r['rodata_bytes']<29 and r['eh_frame_hdr'] for r in rows[1:]),rows
script=ROOT/'tests/fixtures/pax-kernel.ld'
source.write_text('''.text
.global _start
_start: ret
.section .text.extra,"ax",@progbits
nop
.section .rodata.extra,"a",@progbits
.quad 1
.section .data.rel.ro.extra,"aw",@progbits
.quad _start
.section .data.limine,"aw",@progbits
.quad 2
.data
.quad 3
.section .bss.extra,"aw",@nobits
.space 17
.comm common,32,16
.section .comment,"",@progbits
.asciz "discard witness"
.section .eh_frame,"a",@progbits
.long 0
.section .note.GNU-stack,"",@progbits
''');call(['as','--64',source,'-o',obj]);kernel=[]
for name,ld in [('lld','ld.lld-17'),('gnu','ld.bfd')]:
    out=OUT/('kernel-'+name);call([ld,'-static','-T',script,'-o',out,obj]);b,secs,loads=elf(out)
    assert struct.unpack_from('<Q',b,24)[0]==0xffffffff80000000
    assert [p[1] for p in loads if p[0]==1]==[5,4,6]
    assert all(p[3]>=0xffffffff80000000 and p[3]%4096==0 for p in loads if p[0]==1)
    assert not {'.comment','.eh_frame','.note.GNU-stack'} & secs.keys()
    assert secs['.bss'][1]==8
    symbols=call(['nm','-n',out]).decode();assert all(x in symbols for x in ['__pax_image_start','__pax_image_end','__pax_text_end','__pax_rodata_end','__pax_data_start','common'])
    kernel.append({'oracle':name,'sha256':hashlib.sha256(b).hexdigest(),'headers':call(['readelf','-lSW',out]).decode(),'symbols':symbols,'executed':False})
(OUT/'results.json').write_text(json.dumps({'merge_unwind':rows,'kernel_script_sha256':hashlib.sha256(script.read_bytes()).hexdigest(),'kernel':kernel},indent=2)+'\n')
print('layout-controls: three-linker merge/unwind measurements and two-oracle kernel.ld scope; no high-half ELF executed; 0 SKIP')
