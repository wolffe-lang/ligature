#!/usr/bin/env python3
"""Independent ELF/note decoding and hashlib checks, including corruptions."""
import hashlib,json,pathlib,struct,subprocess
ROOT=pathlib.Path(__file__).resolve().parent.parent;BIN=ROOT/'target/ligature';OUT=ROOT/'target/evidence/provenance';OUT.mkdir(parents=True,exist_ok=True)
exe=ROOT/'target/evidence/cc/hello';data=exe.read_bytes()
shoff=struct.unpack_from('<Q',data,40)[0];count,names=struct.unpack_from('<HH',data,60)
headers=[struct.unpack_from('<IIQQQQIIQQ',data,shoff+64*i) for i in range(count)]
ns=headers[names];strings=data[ns[4]:ns[4]+ns[5]]
sections={strings[h[0]:].split(b'\0',1)[0].decode():h for h in headers}
n=sections['.note.wolf.link'];m=sections['.wolf.link.manifest'];raw=data[n[4]:n[4]+n[5]]
assert (n[1],n[2],n[5],n[8])==(7,0,116,4)
assert struct.unpack_from('<III',raw)==(5,96,1)
assert raw[12:20]==b'WOLF'+bytes(4)
version,flags,total,size=struct.unpack_from('<IIQQ',raw,20)
assert (version,flags,total,size)==(1,0,len(data),m[5])
assert struct.unpack_from('<Q',raw,108)[0]==m[4]
manifest=data[m[4]:m[4]+m[5]]
assert hashlib.sha256(manifest).digest()==raw[44:76]
zeroed=bytearray(data);zeroed[n[4]+44:n[4]+108]=bytes(64)
assert hashlib.sha256(zeroed).digest()==raw[76:108]
record=json.loads(manifest)
assert manifest==(json.dumps(record,sort_keys=True,separators=(',',':'))+'\n').encode()
assert record['coverage']=='sections' and record['output']['sha256'] is None
assert record['output']['bytes']==len(data)
assert all('/' not in x['path'] and len(x['sha256'])==64 for x in record['inputs'])
assert all(r['file_start']<=r['file_end']<=len(data) for r in record['input_ranges'] if r['file_start']!=r['file_end'])
for label,offset,reason in [('manifest',m[4]+1,'manifest digest'),('digest',n[4]+44,'manifest digest'),('version',n[4]+20,'version'),('output',sections['.text'][4],'output digest')]:
    bad=bytearray(data);bad[offset]^=1;path=OUT/label;path.write_bytes(bad)
    p=subprocess.run([BIN,'verify',path],capture_output=True)
    assert p.returncode==1 and reason.encode() in p.stderr,(label,p.returncode,p.stderr)
print('provenance: canonical manifest, independent SHA256 checks, four negative rows; 0 SKIP')
