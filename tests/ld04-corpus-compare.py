#!/usr/bin/env python3
"""Require the fresh corpus to retain every named finding and deciding fact."""
import hashlib,json,pathlib,subprocess,sys
R=pathlib.Path(__file__).resolve().parent.parent
base=R/'target/static-pax'
results=json.loads((base/'results.json').read_text())
assert len(results['rows'])==14 and results['functional_failures']==0,results
assert all(r['deterministic'] and r['verified'] and r['status']=='behavior-verified-structural-recorded' for r in results['rows'])
subprocess.run([sys.executable,'-I',R/'tools/classify-static',base,base/'classified.json'],check=True)
previous={f['name']:f for f in json.loads((R/'notes/ld03/findings.json').read_text())['findings']}
fresh={};rows=[]
for case in json.loads((base/'classified.json').read_text())['rows']:
 for fact in case['classes']:
  name=f"{case['case']}/{case['oracle']}/{fact['kind']}"
  assert name not in fresh,name
  fresh[name]=fact
  record=base/case['record'];hashes=[hashlib.sha256(record.read_bytes()).hexdigest() for _ in range(2)];assert hashes[0]==hashes[1]
  rows.append({'name':name,'record':case['record'],'record_sha256_read_twice':hashes,'facts':fact,'previous_facts':previous.get(name,{}).get('facts'),'facts_equal':fact==previous.get(name,{}).get('facts')})
report={'format':'ligature.ld04.corpus-delta.v1','cases':14,'functional_failures':0,'missing':sorted(previous.keys()-fresh.keys()),'new':sorted(fresh.keys()-previous.keys()),'rows':rows,'waivers':[]}
(base/'ld04-comparison.json').write_text(json.dumps(report,indent=2)+'\n')
assert previous.keys()==fresh.keys(),('finding identities changed',report['missing'],report['new'])
assert all(row['facts_equal'] for row in rows),('deciding facts changed',[r['name'] for r in rows if not r['facts_equal']])
print('ld04 full corpus: 14 behavior/verify/determinism rows, all 87 named deciding facts retained exactly, 0 waivers; no PAX rerun claimed',flush=True)
