#!/usr/bin/env python3
"""Compare independently captured stdout/stderr/status for every guest linker."""
import hashlib,json,pathlib,re,sys
serial,case,out=map(pathlib.Path,sys.argv[1:4]);raw=serial.read_bytes();text=raw.replace(b'\r\n',b'\n')
# Match PAX's published session rule: kernel user diagnostics are not process output.
clean=[]
for line in text.splitlines(keepends=True):
    if b'user: ' in line:line=line.split(b'user: ',1)[0]
    clean.append(line)
text=b''.join(clean)
manifest=json.loads((case/'manifest.json').read_text());rows=[]
for name in ('ligature','lld','gnu'):
    n=name.encode();pattern=rb'LD01 '+n+rb' STATUS ([0-9]+)\nLD01 '+n+rb' OUT\n(.*?)\nLD01 '+n+rb' ERR\n(.*?)\nLD01 '+n+rb' END\n'
    matches=list(re.finditer(pattern,text,re.S));assert len(matches)==1,(name,'missing/duplicate output record',text[-3000:])
    m=matches[0];actual={'stdout_hex':m[2].hex(),'stderr_hex':m[3].hex(),'status':int(m[1])}
    expected=manifest['lld' if name=='ligature' else name]['run']
    rows.append({'linker':name,'actual':actual,'expected':expected,'equal':actual==expected})
meta=pathlib.Path(str(serial)+'.meta').read_text();result={'case':case.name,'serial_sha256':hashlib.sha256(raw).hexdigest(),'meta':meta,'rows':rows}
out.write_text(json.dumps(result,indent=2)+'\n')
assert b'LD01 COMPLETE\n' in text and b'PANIC ' not in text,text[-3000:]
assert all(r['equal'] for r in rows),rows
print('PAX',case.name,'three stdout/stderr/status records equal Linux; serial',result['serial_sha256'])
