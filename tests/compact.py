#!/usr/bin/env python3
"""Malformed compact tables are refused even with freshly forged digest seals."""
import copy,hashlib,json,pathlib,runpy,struct,subprocess
ROOT=pathlib.Path(__file__).resolve().parent.parent;BIN=ROOT/'target/ligature'
c=runpy.run_path(str(ROOT/'tests/manifest-codec.py'))
path=ROOT/'target/evidence/attribution/program';data=path.read_bytes()
sh=struct.unpack_from('<Q',data,40)[0];n,ns=struct.unpack_from('<HH',data,60)
hs=[struct.unpack_from('<IIQQQQIIQQ',data,sh+64*i) for i in range(n)]
h=hs[ns];names=data[h[4]:h[4]+h[5]]
sec={names[h[0]:].split(b'\0',1)[0].decode():h for h in hs};m=sec['.wolf.link.manifest'];note=sec['.note.wolf.link'][4]
raw=data[m[4]:m[4]+m[5]];doc=c['decode'](raw);out=ROOT/'target/evidence/compact';out.mkdir(exist_ok=True)
def seal(raw,label):
    b=bytearray(data);assert len(raw)==m[5];b[m[4]:m[4]+m[5]]=raw;b[note+44:note+108]=bytes(64)
    whole=hashlib.sha256(b).digest();b[note+44:note+76]=hashlib.sha256(raw).digest();b[note+76:note+108]=whole
    p=out/label;p.write_bytes(b);return p
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
