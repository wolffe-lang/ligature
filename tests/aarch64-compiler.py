#!/usr/bin/env python3
"""Reproduce wolf-lang#614 without a guard workaround. BLOCKED is exit 2, not PASS."""
import argparse,hashlib,json,pathlib,subprocess,sys
p=argparse.ArgumentParser();p.add_argument('--compiler',type=pathlib.Path,required=True);p.add_argument('--sysroot',required=True);p.add_argument('--out',type=pathlib.Path,required=True);a=p.parse_args()
R=pathlib.Path(__file__).resolve().parent.parent;a.out.mkdir(parents=True,exist_ok=True)
base=['qemu-aarch64-static','-L',a.sysroot,str(a.compiler)];rows=[]
version=subprocess.run([*base,'--version'],capture_output=True,check=True).stdout.decode()
for tier,flags,suffix in [('native',['--emit=obj'],'.o'),('release',['--release','--emit=llvm-ir'],'.ll')]:
 out=a.out/('hello-'+tier+suffix);assert not out.exists(),'probe requires a fresh output name'
 args=[*base,'build',*flags,str(R/'tests/corpus/hello/hello.lu'),'-o',str(out)]
 r=subprocess.run(args,capture_output=True,timeout=180)
 (a.out/(tier+'.stdout')).write_bytes(r.stdout);(a.out/(tier+'.stderr')).write_bytes(r.stderr)
 rows.append({'tier':tier,'argv':args,'status':r.returncode,'stdout':r.stdout.decode(),'stderr':r.stderr.decode(),'output_exists':out.exists()})
 assert r.returncode==2 and f'this host cannot run the {tier} tier'.encode() in r.stderr and not out.exists(),rows[-1]
hashes=[hashlib.sha256(a.compiler.read_bytes()).hexdigest() for _ in range(2)];assert hashes[0]==hashes[1]
(a.out/'results.json').write_text(json.dumps({'status':'BLOCKED','issue':'wolf-lang#614','compiler_version':version,'compiler_sha256_read_twice':hashes,'emulation':'explicit qemu user mode; no binfmt or host-guard workaround','rows':rows},indent=2)+'\n')
print('BLOCKED wolf-lang#614: verified AArch64 compiler refuses both native object emission and release IR emission with status 2; no compiler objects or Wolf hello claimed',flush=True)
sys.exit(2)
