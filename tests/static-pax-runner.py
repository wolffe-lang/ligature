#!/usr/bin/env python3
"""A command's own JSON report must survive command-metadata recording."""
import json,pathlib,runpy,sys,tempfile
ROOT=pathlib.Path(__file__).resolve().parent.parent
checked=runpy.run_path(str(ROOT/'tests/static-pax.py'),run_name='runner_test')['checked']
out=ROOT/'target/evidence/runner';out.mkdir(parents=True,exist_ok=True)
with tempfile.TemporaryDirectory(dir=out) as tmp:
    base=pathlib.Path(tmp)/'lld-differ'
    report=base.with_suffix('.json')
    expected={'format':'ligature.differ.v1','differences':[{'kind':'symbols'}],'unexplained':[{'kind':'symbols'}]}
    script='import json,pathlib,sys;pathlib.Path(sys.argv[1]).write_text(sys.argv[2]);raise SystemExit(1)'
    p=checked([sys.executable,'-I','-c',script,report,json.dumps(expected)],base,allowed=(0,1))
    assert json.loads(report.read_text())==expected,'command report overwritten by runner metadata'
    meta=json.loads(pathlib.Path(str(base)+'.command.json').read_text())
    assert meta['status']==p.returncode==1
    assert meta['argv'][4]==str(report)
    assert pathlib.Path(str(base)+'.stdout').is_file()
    assert pathlib.Path(str(base)+'.stderr').is_file()
print('static-pax runner: report preserved, nonzero differ status preserved, 0 SKIP')
