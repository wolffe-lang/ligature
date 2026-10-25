#!/usr/bin/env python3
import fcntl,gzip,hashlib,json,pathlib,statistics
base=pathlib.Path.home()/'lanes/ld03';root=base/'ligature';corpus=root/'target/static-pax';result=json.loads((corpus/'results.json').read_text());classes=json.loads((root/'notes/ld03/current-structural-classes.json').read_text());lookup={(r['case'],r['oracle']):r for r in classes['rows']};rows=[]
for r in result['rows']:
    assert r['status']=='behavior-verified-structural-recorded' and r['deterministic'] and r['verified']
    row={'case':r['case'],'sha256':r['sha256'],'link_seconds':[json.loads((corpus/r['case']/f'link{i}.command.json').read_text())['elapsed'] for i in (1,2)],'verify_seconds':json.loads((corpus/r['case']/'verify.command.json').read_text())['elapsed'],'comparisons':[]}
    for d in r['structural']:
      with (base.parent/'kasumi-cores-12-15.lock').open('a') as lease:
        fcntl.flock(lease,fcntl.LOCK_EX)
        path=corpus/d['record'];reads=[]
        for _ in range(2):
            with gzip.open(path,'rb') as f:reads.append(hashlib.file_digest(f,'sha256').hexdigest())
        assert reads==[lookup[(r['case'],d['oracle'])]['sha256']]*2
        with gzip.open(path,'rt') as f:report=json.load(f)
        checks=[x for x in report['differences'] if x['kind']=='relocation-validation'];assert all(not x['candidate'] and not x['reference'] for x in checks)
        rel=next(x for x in report['differences'] if x['kind']=='relocations')
        row['comparisons'].append({'oracle':d['oracle'],'record':d['record'],'sha256_read_twice':reads,'candidate_sites':len(rel['candidate']),'reference_sites':len(rel['reference']),'validation_findings':0,'kinds':d['kinds']})
    rows.append(row);print('indexed',r['case'],flush=True)
hello=next(r for r in rows if r['case']=='hello-hello')
summary={'source_head':'f76ae9cb4dd8092ef823e4a654a1c4da91316797','cases':14,'functional_failures':result['functional_failures'],'deterministic_relinks':14,'findings':classes['counts'],'total_findings':classes['total'],'hello_link_seconds':hello['link_seconds'],'hello_verify_seconds':hello['verify_seconds'],'rows':rows}
(root/'notes/ld03/evidence/linux-qualified.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps({k:v for k,v in summary.items() if k!='rows'},indent=2))
