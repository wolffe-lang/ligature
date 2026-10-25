#!/usr/bin/env python3
"""Compile separately, then exercise cc-shaped argv without a system linker."""
import os,pathlib,subprocess
ROOT=pathlib.Path(__file__).resolve().parent.parent;OUT=ROOT/'target/evidence/cc';OUT.mkdir(parents=True,exist_ok=True)
source=OUT/'hello.c';source.write_text('#include <stdio.h>\nint main(void){puts("cc frontend");return 0;}\n')
obj=OUT/'hello.o';exe=OUT/'hello'
subprocess.run(['musl-gcc','-ffunction-sections','-fdata-sections','-c',source,'-o',obj],check=True)
env=dict(os.environ,LIGATURE_SYSROOT='/usr/lib/x86_64-linux-musl')
p=subprocess.run([ROOT/'target/ligature','-o',exe,obj,'-lpthread','-ldl','-lm','-Wl,--gc-sections','-fuse-ld=lld'],env=env,capture_output=True)
assert p.returncode==0,p.stderr
p=subprocess.run([exe],capture_output=True);assert (p.stdout,p.stderr,p.returncode)==(b'cc frontend\n',b'',0)
print('cc frontend: exact compiler-style option subset links and runs; 0 SKIP')
