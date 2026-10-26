#!/usr/bin/env python3
"""Actual clang AArch64 objects and emulated candidate/oracle hello execution."""
import argparse,hashlib,json,pathlib,runpy,subprocess
p=argparse.ArgumentParser();p.add_argument('--lld',default='ld.lld-18');p.add_argument('--reuse',action='store_true');a=p.parse_args()
R=pathlib.Path(__file__).resolve().parent.parent;O=R/'target/evidence/aarch64-live';O.mkdir(parents=True,exist_ok=True);B=R/'target/ligature';commands=[]
validate=runpy.run_path(str(R/'tests/aarch64-sites.py'))['validate']
def call(args):
 r=subprocess.run(list(map(str,args)),capture_output=True,timeout=60);commands.append({'argv':list(map(str,args)),'status':r.returncode,'stdout':r.stdout.decode(),'stderr':r.stderr.decode()});assert r.returncode==0,commands[-1];return r.stdout
message=b'hello, AArch64\n'
sources={
'entry':f'''.text
.global _start
_start:
 adrp x1, message
 add x1, x1, :lo12:message
 mov x0, #1
 mov x2, #{len(message)}
 mov x8, #64
 svc #0
 bl read_values
 b finish
.data
.global absolute_pointer, relative_pointer
absolute_pointer: .quad message
relative_pointer: .word finish - .
''',
'functions': '''.text
.global read_values, finish
read_values:
 adrp x3, value
 ldr x0, [x3, :lo12:value]
 adrp x4, :got:extra
 ldr x4, [x4, :got_lo12:extra]
 ldr x5, [x4]
 add x0, x0, x5
 ret
finish:
 cmp x0, #42
 b.ne failure
 mov x0, #0
 mov x8, #93
 svc #0
failure:
 mov x0, #99
 mov x8, #93
 svc #0
''',
'data': '''.section .rodata,"a",@progbits
.global message
message: .asciz "hello, AArch64\\n"
.data
.balign 8
.global value, extra
value: .quad 40
extra: .quad 2
'''}
objects=[]
for name,text in sources.items():
 src=O/(name+'.s');obj=O/(name+'.o')
 if not a.reuse:src.write_text(text);call(['clang-18','--target=aarch64-linux-gnu','-c',src,'-o',obj])
 else:assert src.read_text()==text
 objects.append(obj)
archive=O/'helpers.a';call([B,'archive',archive,*objects[1:]])
counts={};hashes={}
for label,ld in [('candidate',B),('oracle-'+a.lld,a.lld)]:
 out=O/label
 args=[ld,'-static','-o',out,objects[0],archive]
 args[1:1]=['-nostdlib'] if label=='candidate' else ['--no-relax','--emit-relocs']
 call(args);call([B,'verify',out]);sites=validate(out);counts[label]=len(sites)
 assert {r['type'] for r in sites}=={257,261,275,277,282,283,286,311,312},sites
 assert call(['qemu-aarch64-static',out])==message
 hashes[label]=[hashlib.sha256(out.read_bytes()).hexdigest() for _ in range(2)]
 if label=='candidate':
  repeat=O/'repeat';call([B,'-nostdlib','-static','-o',repeat,objects[0],archive]);assert repeat.read_bytes()==out.read_bytes()
result={'emulation':'explicit user mode, not native AArch64','emulator':call(['qemu-aarch64-static','--version']).decode(),'oracle':call([a.lld,'--version']).decode(),'site_counts':counts,'hashes_read_twice':hashes,'commands':commands}
(O/('results-'+a.lld+'.json')).write_text(json.dumps(result,indent=2)+'\n')
print('aarch64-live:',counts,'all nine types independently proved; candidate and oracle hello executed under qemu user mode; 0 SKIP')
