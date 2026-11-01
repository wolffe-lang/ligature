#!/usr/bin/env python3
"""The musl runtime's digest refusal executes before any archive member is extracted."""
import pathlib,runpy,urllib.request
ROOT=pathlib.Path(__file__).resolve().parent.parent
original=urllib.request.urlretrieve
calls=[]
def wrong(url,path):
    calls.append(url);pathlib.Path(path).write_bytes(b'not the pinned archive')
try:
    urllib.request.urlretrieve=wrong
    try:runpy.run_path(str(ROOT/'tools/fetch-musl-runtime'),run_name='__main__')
    except SystemExit as e:assert str(e).startswith('REFUSED musl runtime archive digest'),e
    except Exception as e:raise AssertionError(f'musl runtime digest mismatch accepted: the tool went on to {type(e).__name__}') from e
    else:raise AssertionError('musl runtime digest mismatch accepted')
finally:urllib.request.urlretrieve=original
assert len(calls)==1 and calls[0].endswith('/wolf-rt-0.2.36-x86_64-unknown-linux-musl.tar.gz'),calls
print('fetch-musl-runtime: mismatched archive refused before extraction; 0 SKIP')
