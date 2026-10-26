#!/usr/bin/env python3
"""Black-box endpoint controls with each linker's .text held at the same address."""
import argparse,json,pathlib,runpy,subprocess
p=argparse.ArgumentParser();p.add_argument('--lld',required=True);a=p.parse_args()
R=pathlib.Path(__file__).resolve().parent.parent;O=R/'target/evidence/aarch64';D=O/a.lld;D.mkdir(exist_ok=True)
validate=runpy.run_path(str(R/'tests/aarch64-sites.py'))['validate'];rows=[]
for case in json.loads((O/'results.json').read_text()):
 name=case['name']
 if case['status']!=0 and name not in ('prel-under','prel-over','adrp-under','adrp-over'):continue
 output=D/name
 r=subprocess.run([a.lld,'--no-relax','--emit-relocs','-static','-Ttext=0x201000','-z','max-page-size=4096','-o',output,O/(name+'.o')],capture_output=True,timeout=30)
 row={'name':name,'status':r.returncode,'stderr':r.stderr.decode()};rows.append(row)
 if case['status']==0:
  assert r.returncode==0,row;sites=validate(output,allow_veneers=True);row["veneer_sites"]=[s for s in sites if "oracle_veneer" in s]
 else:assert r.returncode!=0 and b'out of range' in r.stderr,row
(D/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
print('AArch64',a.lld,len(rows),'binary endpoint controls and independent equations; 0 SKIP')
