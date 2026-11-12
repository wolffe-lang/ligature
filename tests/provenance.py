#!/usr/bin/env python3
"""Independent ELF/note decoding and hashlib checks, including corruptions."""
import runpy,hashlib,json,pathlib,struct,subprocess
ROOT=pathlib.Path(__file__).resolve().parent.parent;BIN=ROOT/'target/ligature';OUT=ROOT/'target/evidence/provenance';OUT.mkdir(parents=True,exist_ok=True)
codec=runpy.run_path(str(ROOT/'tests/manifest-codec.py'));decode_manifest=codec['decode'];encode_manifest=codec['encode']
files=runpy.run_path(str(ROOT/'tests/provenance-files.py'))
exe=ROOT/'target/evidence/cc/hello';prov=files['load'](exe);data=prov['data'];sections=prov['sections']
side=prov['mode']=='sidecar'
n=sections['.note.wolf.link'];raw=prov['note']
assert (n[1],n[2],n[5],n[8])==(7,0,116,4)
assert struct.unpack_from('<III',raw)==(5,96,1)
assert raw[12:20]==b'WOLF'+bytes(4)
version,flags,total,size=struct.unpack_from('<IIQQ',raw,20)
# Embedded: the manifest section's size and offset, and its digest. Sidecar: the sidecar's size, a
# zero offset, and the whole sidecar's digest; the output keeps no manifest or retained table.
assert (version,flags,total,size)==(1,1 if side else 0,len(data),len(prov['side']) if side else prov['manifest_size'])
assert struct.unpack_from('<Q',raw,108)[0]==(0 if side else prov['manifest_offset'])
manifest=prov['manifest']
assert hashlib.sha256(prov['side'] if side else manifest).digest()==raw[44:76]
if side:assert '.wolf.link.manifest' not in sections and all(h[1]!=4 for h in prov['headers'])
zeroed=bytearray(data);zeroed[n[4]+44:n[4]+108]=bytes(64)
assert hashlib.sha256(zeroed).digest()==raw[76:108]
record=decode_manifest(manifest)
assert manifest==encode_manifest(record)
assert record['coverage']=='bytes-and-patches' and record['output']['sha256'] is None
assert record['output']['bytes']==len(data)
assert len(record['patches'])==sum(len(t['entries'])//24 for t in prov['tables'])
assert all('/' not in x['path'] and len(x['sha256'])==64 for x in record['inputs'])
assert all(r['file_start']<=r['file_end']<=len(data) for r in record['input_ranges'] if r['file_start']!=r['file_end'])
held='sidecar digest' if side else 'manifest digest'
rows=[('manifest',prov['manifest_offset']+1,held),('digest',n[4]+44,held),('version',n[4]+20,'version'),('output',sections['.text'][4],'output digest')]
for label,offset,reason in rows:
    if side and label=='manifest':
        bad=bytearray(prov['side']);bad[offset]^=1;path=files['write'](prov,OUT/label,side=bad,reseal=False)
    else:
        bad=bytearray(data);bad[offset]^=1;path=files['write'](prov,OUT/label,data=bad,reseal=False)
    p=subprocess.run([BIN,'verify',path],capture_output=True)
    assert p.returncode==1 and reason.encode() in p.stderr,(label,p.returncode,p.stderr)
if side:
    path=OUT/'missing-sidecar';path.write_bytes(data)
    if files['sidecar'](path).exists():files['sidecar'](path).unlink()
    p=subprocess.run([BIN,'verify',path],capture_output=True)
    assert p.returncode==1 and b'missing provenance sidecar' in p.stderr,p.stderr
    rows.append(('missing-sidecar',0,'missing provenance sidecar'))
print(f'provenance: canonical manifest ({prov["mode"]}), independent SHA256 checks, {len(rows)} negative rows; 0 SKIP')
