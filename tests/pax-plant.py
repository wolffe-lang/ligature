#!/usr/bin/env python3
import json,pathlib,subprocess
root=pathlib.Path(__file__).resolve().parent.parent
exe=root/'target/oracle/hello-hello/lld/program'
p=subprocess.run([root/'target/ligature','inspect',exe],check=True,capture_output=True)
sec=next(r for r in map(json.loads,p.stdout.splitlines()) if r['row']=='section' and r['name']=='.rodata')
bad=exe.with_name('planted-byte');data=bytearray(exe.read_bytes());data[sec['offset']]^=1;bad.write_bytes(data);bad.chmod(0o755)
p=subprocess.run([root/'tools/differ',exe,bad,'--output',root/'target/evidence/pax-plant.json'],capture_output=True,timeout=120)
assert p.returncode==1,(p.returncode,p.stderr)
print('PAX pinned lld allocated-byte flip: RED as required')
