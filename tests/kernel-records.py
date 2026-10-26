#!/usr/bin/env python3
"""Retain kernel structural differences and strict-verifier refusals, never execute."""
import argparse,collections,gzip,hashlib,json,pathlib,subprocess
p=argparse.ArgumentParser();p.add_argument('inputs',type=pathlib.Path);p.add_argument('output',type=pathlib.Path);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
R=pathlib.Path(__file__).resolve().parent.parent;B=R/'target/ligature';records=[];findings=[]
for tier in ('native','release'):
 views={}
 for name in ('candidate','lld17','lld18','gnu'):
  path=a.inputs/tier/(name+'.elf')
  v=subprocess.run([B,'verify',path],capture_output=True,timeout=60)
  if name=='candidate':assert v.returncode==0,v.stderr
  elif v.returncode:assert v.returncode==1 and b'writable section in nonwritable PT_LOAD' in v.stderr,v.stderr
  data=subprocess.run([B,'inspect',path],capture_output=True,check=True,timeout=60).stdout
  dest=a.output/(tier+'-'+name+'.jsonl.gz');dest.write_bytes(gzip.compress(data,mtime=0));assert gzip.decompress(dest.read_bytes())==data
  rows=[json.loads(line) for line in data.splitlines()];sections={r['index']:r for r in rows if r['row']=='section'}
  view={'program_headers':[r for r in rows if r['row']=='program'], 'rodata_flags':next(s['flags'] for s in sections.values() if s['name']=='.rodata'), 'script_symbols':{r['name']:{'binding':r['binding'],'type':r['type'],'value':r['value'],'section':sections.get(r['section'],{}).get('name',r['section'])} for r in rows if r['row']=='symbol' and r['binding']!=0 and r['name'].startswith('__pax_')}, 'relocation_counts':dict(collections.Counter(str(r['type']) for r in rows if r['row']=='rela'))}
  hashes=[hashlib.sha256(dest.read_bytes()).hexdigest() for _ in range(2)];assert hashes[0]==hashes[1]
  records.append({'tier':tier,'linker':name,'record':dest.name,'sha256_read_twice':hashes,'verify_status':v.returncode,'verify_stderr':v.stderr.decode(),'executed':False})
  views[name]=view
  if v.returncode:findings.append({'name':f'kernel/{tier}/{name}/strict-verifier','status':'retained','reason':v.stderr.decode().strip(),'equivalent':False})
 for name in ('lld17','lld18','gnu'):
  for key,value in views['candidate'].items():
   if value!=views[name][key]:findings.append({'name':f'kernel/{tier}/{name}/{key}','status':'retained','candidate':value,'reference':views[name][key],'equivalent':False})
result={'format':'ligature.kernel.structural.v1','records':records,'findings':findings,'waivers':[],'equivalent':not findings,'scope':'separate from the inherited 87 user-program findings; strict oracle verifier refusals retained, not waived; no ELF execution'}
(a.output/'index.json').write_text(json.dumps(result,indent=2)+'\n')
print('kernel-records:',len(findings),'named structural observations/refusals retained; 0 waivers; whole-ELF equivalence NOT claimed')
