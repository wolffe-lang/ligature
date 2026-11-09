#!/usr/bin/env python3
"""The bundle's digest refusal executes before any archive member is extracted.

With LIGATURE_BUNDLE_ARCHIVE set, the tool reads that file in place of the release asset, verifies
it exactly as it verifies a download, and never reaches the network."""
import os,pathlib,runpy,tempfile,urllib.request
ROOT=pathlib.Path(__file__).resolve().parent.parent
original=urllib.request.urlretrieve
calls=[]
def wrong(url,path):
    calls.append(url);pathlib.Path(path).write_bytes(b'not the pinned archive')
try:
    urllib.request.urlretrieve=wrong
    os.environ.pop('LIGATURE_BUNDLE_ARCHIVE',None)
    try:runpy.run_path(str(ROOT/'tools/fetch-bundle'),run_name='__main__')
    except SystemExit as e:assert str(e).startswith('REFUSED link bundle digest'),e
    else:raise AssertionError('bundle digest mismatch accepted')
    assert len(calls)==1
    (ROOT/'target').mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='fetch-bundle-test-',dir=ROOT/'target') as temp:
        local=pathlib.Path(temp)/'local.tar.gz';local.write_bytes(b'not the pinned archive either')
        os.environ['LIGATURE_BUNDLE_ARCHIVE']=str(local)
        try:runpy.run_path(str(ROOT/'tools/fetch-bundle'),run_name='__main__')
        except SystemExit as e:assert str(e).startswith('REFUSED link bundle digest'),e
        else:raise AssertionError('local bundle digest mismatch accepted')
        assert len(calls)==1,'FAIL fetch-bundle-local-override: the override reached the network'
        os.environ['LIGATURE_BUNDLE_ARCHIVE']=str(pathlib.Path(temp)/'absent.tar.gz')
        try:runpy.run_path(str(ROOT/'tools/fetch-bundle'),run_name='__main__')
        except SystemExit as e:assert str(e).startswith('REFUSED link bundle archive'),e
        else:raise AssertionError('absent local bundle accepted')
        assert len(calls)==1
finally:
    urllib.request.urlretrieve=original;os.environ.pop('LIGATURE_BUNDLE_ARCHIVE',None)
print('fetch-bundle: mismatched archive refused before extraction, from the release and from a local archive; the override never reaches the network; 0 SKIP')
