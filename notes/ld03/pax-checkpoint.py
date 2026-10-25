#!/usr/bin/env python3
import gzip,hashlib,json,os,pathlib,sys
verify=sys.argv[1:2]==['--verify']
out,case,elf,image=map(pathlib.Path,sys.argv[2:] if verify else sys.argv[1:])
r=json.loads((out/'result.json').read_text());status=json.loads((out/'status.json').read_text())
assert r['case']==case.name and status['halt_status']==0
actual=[row['actual'] for row in r['rows']];assert actual[0]==actual[1]==actual[2]
if case.name=='pax-fork':
    assert status['row_status']==1 and all(not row['equal'] for row in r['rows'])
    assert actual[0]=={'stdout_hex':b'fork: io\n'.hex(),'stderr_hex':'','status':0},actual
else:assert status['row_status']==0 and all(row['equal'] for row in r['rows'])
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
if verify:
    marker=json.loads((out/'complete.json').read_text())
    assert marker['case']==case.name and marker['boot']==out.name and marker['status']==status
    expected={str(p) for p in [out/'serial.log',out/'result.json',elf,image,case/'manifest.json']}
    assert set(marker['hashes_read_twice'])==expected
    for name,reads in marker['hashes_read_twice'].items():
        p=pathlib.Path(name)
        if p.exists():observed=sha(p)
        else:
            with gzip.open(str(p)+'.gz','rb') as f:observed=hashlib.file_digest(f,'sha256').hexdigest()
        assert reads==[observed,observed],name
    m=json.loads((case/'manifest.json').read_text())
    for linker in ('ligature','lld','gnu'):assert sha(case/linker)==m[linker]['sha256']
    print('RESUME verified',case.name,out.name)
    raise SystemExit(0)
hashes={str(p):[sha(p),sha(p)] for p in [out/'serial.log',out/'result.json',elf,image,case/'manifest.json']}
assert all(v[0]==v[1] for v in hashes.values())
value={'case':case.name,'boot':out.name,'status':status,'classification':'named-red-pax#175' if case.name=='pax-fork' else 'linux-equal','hashes_read_twice':hashes}
p=out/'complete.json.new'
with p.open('w') as f:json.dump(value,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
p.replace(out/'complete.json')
fd=os.open(out,os.O_DIRECTORY);os.fsync(fd);os.close(fd)
