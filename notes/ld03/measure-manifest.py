#!/usr/bin/env python3
"""Compare freshly linked compact hello with read-only ld02a JSON evidence."""
import gzip,hashlib,json,pathlib,runpy,struct,sys
ROOT=pathlib.Path(__file__).resolve().parents[2];codec=runpy.run_path(str(ROOT/'tests/manifest-codec.py'))
def read(path):
    b=gzip.decompress(path.read_bytes()) if path.suffix=='.gz' else path.read_bytes()
    sh=struct.unpack_from('<Q',b,40)[0];n,ns=struct.unpack_from('<HH',b,60);hs=[struct.unpack_from('<IIQQQQIIQQ',b,sh+64*i) for i in range(n)]
    h=hs[ns];names=b[h[4]:h[4]+h[5]];m=next(h for h in hs if names[h[0]:].split(b'\0',1)[0]==b'.wolf.link.manifest')
    raw=b[m[4]:m[4]+m[5]];return b,raw,codec['decode'](raw)
oldpath,newpath=map(pathlib.Path,sys.argv[1:3]);old,oldraw,a=read(oldpath);new,newraw,b=read(newpath)
assert len(a['patches'])==len(b['patches'])==590358
fields=['patches','inputs','members','input_ranges','memory_ranges','symbols','pulls']
for key in fields:assert a[key]==b[key],key
assert len(oldraw)/len(newraw)>=10
assert codec['encode'](b)==newraw
hashes=[]
for _ in range(2):
    old2,_,_=read(oldpath);new2,_,_=read(newpath)
    hashes.append({'old':hashlib.sha256(old2).hexdigest(),'new':hashlib.sha256(new2).hexdigest()})
assert hashes[0]==hashes[1]
report={'old_bytes':len(oldraw),'new_bytes':len(newraw),'ratio':len(oldraw)/len(newraw),'sites':len(b['patches']),'bytes_per_site_before':len(oldraw)/len(a['patches']),'bytes_per_site_after':len(newraw)/len(b['patches']),'equal_fields':fields,'hashes_read_twice':hashes,'discard_records':len(b['discarded']),'canonical_independent_encoder_equal':True}
(ROOT/'notes/ld03/measurement-after.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2),flush=True)
