#!/usr/bin/env python3
"""Compile separately, then exercise cc-shaped argv without a system linker."""
import os,pathlib,subprocess
ROOT=pathlib.Path(__file__).resolve().parent.parent;OUT=ROOT/'target/evidence/cc';OUT.mkdir(parents=True,exist_ok=True)
source=OUT/'hello.c';source.write_text('#include <stdio.h>\nextern void ligature_hello_marker(void);\nint main(void){ligature_hello_marker();puts("cc frontend");return 0;}\n')
obj=OUT/'hello.o';exe=OUT/'hello'
subprocess.run(['musl-gcc','-ffunction-sections','-fdata-sections','-c',source,'-o',obj],check=True)
marker=OUT/'marker.s';marker_obj=OUT/'marker.o'
# Unlike ENDBR64, skipping this first byte changes execution: RET becomes UD2.
marker.write_text('.section .text.ligature_hello_marker,"ax",@progbits\n.global ligature_hello_marker\n.type ligature_hello_marker,@function\nligature_hello_marker: ret\n ud2\n.size ligature_hello_marker,.-ligature_hello_marker\n.section .note.GNU-stack,"",@progbits\n')
subprocess.run(['as','--64',marker,'-o',marker_obj],check=True)
env=dict(os.environ,LIGATURE_SYSROOT='/usr/lib/x86_64-linux-musl')
p=subprocess.run([ROOT/'target/ligature','-o',exe,obj,marker_obj,'-lpthread','-ldl','-lm','-Wl,--gc-sections','-fuse-ld=lld'],env=env,capture_output=True)
assert p.returncode==0,p.stderr
p=subprocess.run([exe],capture_output=True);assert (p.stdout,p.stderr,p.returncode)==(b'cc frontend\n',b'',0),(p.stdout,p.stderr,p.returncode)
print('cc frontend: exact compiler-style option subset links and runs; 0 SKIP')
