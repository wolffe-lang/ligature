#!/usr/bin/env python3
"""Replay a genuine guest capture and require every stream/status mutation to fail."""
import pathlib,subprocess,sys,tempfile
ROOT=pathlib.Path(__file__).resolve().parent.parent;fixture=ROOT/'tests/fixtures/pax-hello';OUT=ROOT/'target/evidence/pax-validator';OUT.mkdir(parents=True,exist_ok=True)
raw=(fixture/'serial.log').read_bytes().replace(b'\r\n',b'\n')
mutations={'stdout':raw.replace(b'LD01 ligature OUT\nhello, wolf',b'LD01 ligature OUT\nwrong, wolf',1),'stderr':raw.replace(b'LD01 ligature ERR\n',b'LD01 ligature ERR\nunexpected\n',1),'status':raw.replace(b'LD01 ligature STATUS 0',b'LD01 ligature STATUS 1',1),'missing':raw.replace(b'LD01 ligature OUT\n',b'BROKEN HEADER\n',1)}
with tempfile.TemporaryDirectory(dir=OUT) as tmp:
    directory=pathlib.Path(tmp)
    for name,data in [('positive',raw),*mutations.items()]:
        if name!='positive':assert data!=raw,name
        log=directory/(name+'.log');log.write_bytes(data);pathlib.Path(str(log)+'.meta').write_bytes((fixture/'serial.log.meta').read_bytes())
        p=subprocess.run([sys.executable,'-I',ROOT/'tests/pax-row.py',log,fixture,directory/(name+'.json')],capture_output=True)
        (OUT/(name+'.stdout')).write_bytes(p.stdout);(OUT/(name+'.stderr')).write_bytes(p.stderr)
        if name=='positive':assert p.returncode==0,p.stderr
        else:assert p.returncode!=0,('PAX validator accepted mutation',name)
print('PAX transcript validator: one genuine capture, four rejected mutations; replay only, 0 SKIP')
