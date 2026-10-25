#!/usr/bin/env python3
"""Losslessly compress only this lane's completed oracle text views."""
import fcntl,gzip,hashlib,json,pathlib,shutil
base=pathlib.Path.home()/'lanes/ld03';root=base/'ligature';corpus=root/'target/static-pax';index=root/'notes/ld03/evidence/compressed-views.json'
rows=json.loads(index.read_text()) if index.exists() else []
for case in json.loads((corpus/'results.json').read_text())['rows']:
 assert case['status']=='behavior-verified-structural-recorded'
 for oracle in ('lld','gnu'):
  for name in ('inspect.jsonl','readelf.txt','objdump.txt','link.map'):
   p=corpus/case['case']/'oracle'/oracle/name
   if not p.exists():
    assert any(r['path']==str(p) for r in rows) and pathlib.Path(str(p)+'.gz').exists();continue
   with (base.parent/'kasumi-cores-12-15.lock').open('a') as lease:
    fcntl.flock(lease,fcntl.LOCK_EX)
    with p.open('rb') as f:sha=hashlib.file_digest(f,'sha256').hexdigest()
    z=pathlib.Path(str(p)+'.gz');tmp=pathlib.Path(str(z)+'.new')
    with p.open('rb') as src,gzip.open(tmp,'wb',compresslevel=1) as dest:shutil.copyfileobj(src,dest)
    with gzip.open(tmp,'rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==sha
    tmp.replace(z)
    row={'path':str(p),'original_bytes':p.stat().st_size,'compressed_bytes':z.stat().st_size,'uncompressed_sha256':sha,'verified_compression':True}
    rows=[r for r in rows if r['path']!=str(p)]+[row]
    temp=index.with_suffix('.new');temp.write_text(json.dumps(rows,indent=2)+'\n');temp.replace(index)
    p.unlink()
 print('compressed views',case['case'],flush=True)
print('reclaimed',sum(r['original_bytes']-r['compressed_bytes'] for r in rows),'bytes',flush=True)
