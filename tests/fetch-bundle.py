#!/usr/bin/env python3
"""The bundle's digest refusal executes before any archive member is extracted."""
import pathlib,runpy,urllib.request
ROOT=pathlib.Path(__file__).resolve().parent.parent
original=urllib.request.urlretrieve
calls=[]
def wrong(url,path):
    calls.append(url);pathlib.Path(path).write_bytes(b'not the pinned archive')
try:
    urllib.request.urlretrieve=wrong
    try:runpy.run_path(str(ROOT/'tools/fetch-bundle'),run_name='__main__')
    except SystemExit as e:assert str(e).startswith('REFUSED link bundle digest'),e
    else:raise AssertionError('bundle digest mismatch accepted')
finally:urllib.request.urlretrieve=original
assert len(calls)==1
print('fetch-bundle: mismatched archive refused before extraction; 0 SKIP')
