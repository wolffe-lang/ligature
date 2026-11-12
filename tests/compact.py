#!/usr/bin/env python3
"""Malformed compact tables are refused even with freshly forged digest seals."""
import copy,hashlib,json,pathlib,runpy,struct,subprocess
ROOT=pathlib.Path(__file__).resolve().parent.parent;BIN=ROOT/'target/ligature'
c=runpy.run_path(str(ROOT/'tests/manifest-codec.py'))
files=runpy.run_path(str(ROOT/'tests/provenance-files.py'))
# The manifest is read from wherever the output's note says it is: the sidecar by default.
path=ROOT/'target/evidence/attribution/program';prov=files['load'](path)
raw=prov['manifest'];doc=c['decode'](raw);out=ROOT/'target/evidence/compact';out.mkdir(exist_ok=True)
def seal(raw,label):
    assert len(raw)==prov['manifest_size'];return files['write'](prov,out/label,manifest=raw)
for label,offset,value in [('metadata-length',8,2**64-1),('pool-count',16,2**64-1),('row-count',24,2**64-1),('table-length',32,2**64-1)]:
    b=bytearray(raw);struct.pack_into('<Q',b,offset,value);p=seal(b,label)
    r=subprocess.run([BIN,'verify',p],capture_output=True);assert r.returncode==1,(label,r.stderr)
b=bytearray(raw);b[-1]=1;p=seal(b,'padding')
r=subprocess.run([BIN,'verify',p],capture_output=True);assert r.returncode==1 and b'padding' in r.stderr
for value in (-2**63,2**63-1):
    d=copy.deepcopy(doc);d['patches'][0]['addend']=value;p=seal(c['encode'](d,len(raw)),'signed-'+str(value))
    r=subprocess.run([BIN,'explain',p,'--dependencies','pointer'],capture_output=True)
    assert r.returncode==0 and json.loads(r.stdout)[0]['addend']==value,r.stderr
print('compact-manifest: five resealed decoder corruptions rejected, signed addend endpoints preserved; 0 SKIP')

# Arbitrary byte names must preserve the legacy JSON semantics, not silently
# switch only the patch table to a different Unicode interpretation.
obj=bytearray((ROOT/'target/evidence/relocation-witness/site.o').read_bytes())
sh=struct.unpack_from('<Q',obj,40)[0];n,ns=struct.unpack_from('<HH',obj,60)
hs=[struct.unpack_from('<IIQQQQIIQQ',obj,sh+64*i) for i in range(n)]
h=hs[ns];names=obj[h[4]:h[4]+h[5]]
strings=next(h for h in hs if names[h[0]:].split(b'\0',1)[0]==b'.strtab')
at=obj.index(b'target\0',strings[4],strings[4]+strings[5]);obj[at]=255
source=out/'byte-name.o';source.write_bytes(obj);exe=out/'byte-name'
r=subprocess.run([BIN,'-nostdlib','-o',exe,source],capture_output=True);assert r.returncode==0,r.stderr
manifest=files['load'](exe)['manifest'];d=c['decode'](manifest)
legacy_name=bytes([195,191]).decode('latin1')+'arget'
assert any(s['name']==legacy_name for s in d['symbols'])
assert any(p['symbol']==legacy_name for p in d['patches']),d['patches']
assert c['encode'](d)==manifest
print('compact-manifest: arbitrary-byte symbol text matches legacy JSON origins; 0 SKIP')
