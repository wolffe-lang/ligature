#!/usr/bin/env python3
"""Black-box strong/weak/common and archive extraction witnesses."""
import json,pathlib,subprocess
ROOT=pathlib.Path(__file__).resolve().parent.parent;OUT=ROOT/'target/evidence/resolution';OUT.mkdir(parents=True,exist_ok=True)
import argparse
ap=argparse.ArgumentParser();ap.add_argument('--lld',default='ld.lld-17');a=ap.parse_args()
def command(args):return subprocess.run(list(map(str,args)),capture_output=True,timeout=30)
def object_file(name,text):
 p=OUT/(name+'.s');p.write_text(text+'\n.section .note.GNU-stack,"",@progbits\n');out=OUT/(name+'.o');r=command(['as','--64',p,'-o',out]);assert r.returncode==0,r.stderr;return out
main=object_file('start','.text\n.global _start\n_start:\n mov choice(%rip),%edi\n mov $60,%eax\n syscall')
def definition(name,value,weak=False):return object_file(name,f'.data\n.{"weak" if weak else "global"} choice\n.type choice,@object\n.size choice,4\nchoice: .long {value}')
strong=definition('strong',11);weak1=definition('weak1',22,True);weak2=definition('weak2',33,True)
common=object_file('common','.comm choice,16,16');common2=object_file('common2','.comm choice,32,32')
rows=[]
for name,objects,status in [('strong-weak',[strong,weak1],11),('weak-strong',[weak1,strong],11),('weak-first',[weak1,weak2],22),('weak-reverse',[weak2,weak1],33),('strong-common',[strong,common],11),('common-common',[common,common2],0),('duplicate-strong',[strong,strong],None)]:
 for oracle,ld in [('lld',a.lld),('gnu','ld.bfd')]:
  exe=OUT/(name+'-'+oracle);p=command([ld,'-static','-o',exe,main,*objects])
  if status is None:assert p.returncode!=0 and b'duplicate' in p.stderr.lower() or p.returncode!=0 and b'multiple definition' in p.stderr.lower()
  else:
   assert p.returncode==0,p.stderr;run=command([exe]);assert run.returncode==status,(name,oracle,run.returncode)
  nm=command(['nm','-S',exe]).stdout.decode() if p.returncode==0 else ''
  rows.append({'case':name,'oracle':oracle,'link_status':p.returncode,'expected_run_status':status,'stderr':p.stderr.decode(),'choice':[x for x in nm.splitlines() if x.endswith(' choice')]})
# Index search extracts only the defining member needed by a reference.
archive=OUT/'choices.a';p=command(['ar','rcs',archive,strong,weak1,weak2]);assert p.returncode==0
for oracle,ld in [('lld',a.lld),('gnu','ld.bfd')]:
 exe=OUT/('archive-'+oracle);p=command([ld,'--trace','-static','-o',exe,main,archive]);assert p.returncode==0,p.stderr
 assert command([exe]).returncode==11
 rows.append({'case':'archive-first-definition','oracle':oracle,'trace':p.stdout.decode(),'run_status':11})
(OUT/'results.json').write_text(json.dumps(rows,indent=2)+'\n');print('resolution: 16 oracle rows, 0 SKIP')
