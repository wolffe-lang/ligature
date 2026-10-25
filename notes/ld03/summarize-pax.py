#!/usr/bin/env python3
import hashlib,json,pathlib,tarfile
base=pathlib.Path.home()/'lanes/ld03';root=base/'ligature';out=root/'notes/ld03/evidence';records=[]
for p in sorted((base/'pax-results').glob('*/*/complete.json')):
    r=json.loads(p.read_text());status=json.loads((p.parent/'status.json').read_text());result=json.loads((p.parent/'result.json').read_text())
    assert r['status']==status and status['halt_status']==0
    assert len(result['rows'])==3 and len({json.dumps(x['actual'],sort_keys=True) for x in result['rows']})==1
    serial=p.parent/'serial.log'
    reads=[hashlib.sha256(serial.read_bytes()).hexdigest() for _ in range(2)]
    assert reads==r['hashes_read_twice'][str(serial)]
    records.append({'case':r['case'],'boot':r['boot'],'classification':r['classification'],'status':status,'serial_sha256':reads[0],'hash_reads':2,'rows':result['rows']})
assert len(records)==56 and len({r['case'] for r in records})==14
named=[r for r in records if r['classification']=='named-red-pax#175'];assert len(named)==4 and all(r['case']=='pax-fork' for r in named)
assert all(r['status']['row_status']==(1 if r in named else 0) for r in records)
summary={'kernel_source':'edbd385c91f2ff0eadb1ab4e52b276f1a1412b63','kernel_policy':'Reused immutable ld02a native/release ELF binaries, verified twice; no kernel rebuild or claim of current PAX trunk','boots':56,'program_runs':168,'halted':56,'linux_equal':52,'named_red':4,'unexpected_failures':0,'raw_exit':int((base/'pax.exit').read_text()),'records':records}
assert summary['raw_exit']==1
(out/'pax-results.json').write_text(json.dumps(summary,indent=2)+'\n')
archive=out/'pax-evidence.tar.gz'
with tarfile.open(archive,'w:gz') as tar:
    for p in sorted((base/'pax-results').rglob('*')):
        if p.is_file() and (p.suffix in ('.log','.json','.sha256') or p.name.endswith(('.meta','.halt','.regs1','.regs2'))):tar.add(p,arcname=str(p.relative_to(base)),recursive=False)
    tar.add(base/'pax.log',arcname='pax.log');tar.add(base/'pax.exit',arcname='pax.exit')
sha=[hashlib.sha256(archive.read_bytes()).hexdigest() for _ in range(2)];assert sha[0]==sha[1]
(out/'pax-evidence-index.json').write_text(json.dumps({'path':'pax-evidence.tar.gz','bytes':archive.stat().st_size,'sha256_read_twice':sha,'contents':'Every boot result, status, atomic checkpoint, serial/halt/QEMU metadata and image SHA record; large generated images remain under the lane directory'},indent=2)+'\n')
print(json.dumps({k:v for k,v in summary.items() if k!='records'},indent=2));print('archive',archive.stat().st_size,sha[0])
