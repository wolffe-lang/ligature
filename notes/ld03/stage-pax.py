#!/usr/bin/env python3
import fcntl,gzip,hashlib,json,pathlib
base=pathlib.Path.home()/'lanes/ld03';previous=base.parent/'ld02a';root=base/'ligature';corpus=root/'target/static-pax'
def digest(p,expand=False):
    with (gzip.open(p,'rb') if expand else p.open('rb')) as f:return hashlib.file_digest(f,'sha256').hexdigest()
index=[]
with (base.parent/'kasumi-cores-12-15.lock').open('a') as lease:
 fcntl.flock(lease,fcntl.LOCK_EX)
 for row in json.loads((corpus/'results.json').read_text())['rows']:
    assert row['status']=='behavior-verified-structural-recorded'
    d=base/'pax-cases'/row['case'];d.mkdir(parents=True,exist_ok=True);original=corpus/row['case']
    m=json.loads((original/'oracle/manifest.json').read_text());m['ligature']={'sha256':row['sha256'],'run':row['run']}
    for linker,path in {'ligature':original/'program','lld':original/'oracle/lld/program','gnu':original/'oracle/gnu/program'}.items():
        for _ in range(2):assert digest(path)==m[linker]['sha256'],(row['case'],linker)
        dest=d/linker
        if not dest.exists():dest.symlink_to(path)
    (d/'manifest.json').write_text(json.dumps(m,indent=2)+'\n');index.append({'case':row['case'],'hashes_read_twice':{k:v['sha256'] for k,v in m.items()}})
 inherited=[]
 paths=[(previous/'pax-evidence.tar.gz','d1ba3d8f44def38928eb9c14f7a0875c20138633903dd44a4ea0a3e309bbae72',False)]
 for n in ['first','second']:paths.append((previous/f'ligature/target/evidence/self-link/ligature-{n}.gz','c07f2300982e528f7556c398e91f45586ff671cad431fd1e1d4b08dbacf49600',True))
 for tier,sha in [('native','2ef1e4cfc0c9ed9a0dcd8f41d238f040a56b58ca8af5763c0c560902b3c97198'),('release','265b2f3deb8f3dc3d76de0f34e346e7cd6872753f399e9c063e15a3abee46df2')]:paths.append((previous/f'pax-results/kernel-{tier}/build/kmain_console.elf',sha,False))
 for row in json.loads((root/'notes/ld02a/evidence/structural-classes-v2.json').read_text())['rows']:paths.append((previous/'ligature/target/static-pax'/row['record'],row['sha256'],True))
 for p,sha,expand in paths:
    reads=[digest(p,expand) for _ in range(2)];assert reads==[sha,sha],p
    inherited.append({'path':str(p),'sha256':sha,'reads':2,'decompressed':expand})
(root/'notes/ld03/evidence/pax-inputs.json').write_text(json.dumps(index,indent=2)+'\n')
(root/'notes/ld03/evidence/inherited-hashes.json').write_text(json.dumps(inherited,indent=2)+'\n')
print('Staged 14 cases; all program, inherited kernel/self-link/transcript archive and structural hashes read twice',flush=True)
