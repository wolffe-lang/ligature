#!/usr/bin/env python3
"""Compressed evidence must stage exactly the original program bytes."""
import gzip,hashlib,json,pathlib,subprocess,sys,tempfile
ROOT=pathlib.Path(__file__).resolve().parent.parent;OUT=ROOT/'target/evidence/pax-stage';OUT.mkdir(parents=True,exist_ok=True)
with tempfile.TemporaryDirectory(dir=OUT) as tmp:
    d=pathlib.Path(tmp);case=d/'case';case.mkdir()
    fields=[1,0,0,0,1,0,0,0,0,0,0,11,0]
    raw=b'070701'+b''.join(f'{v:08x}'.encode() for v in fields)+b'TRAILER!!!\0'
    original=d/'base.cpio';original.write_bytes(raw+bytes(-len(raw)%4))
    hashes={}
    for name in ('ligature','lld','gnu'):
        payload=b'program\0'+name.encode();(case/name).write_bytes(payload);hashes[name]=hashlib.sha256(payload).hexdigest()
    first=d/'first.cpio'
    p=subprocess.run([sys.executable,'-I',ROOT/'tools/pax-stage',original,case,first],capture_output=True,check=True)
    assert json.loads(p.stdout)['programs']==hashes
    for name in hashes:
        path=case/name
        with gzip.open(str(path)+'.gz','wb') as f:f.write(path.read_bytes())
        path.unlink()
    second=d/'second.cpio'
    p=subprocess.run([sys.executable,'-I',ROOT/'tools/pax-stage',original,case,second],capture_output=True,check=True)
    assert json.loads(p.stdout)['programs']==hashes and first.read_bytes()==second.read_bytes()
print('PAX staging: gzip evidence preserves exact program bytes and identical initramfs; 0 SKIP')
