#!/usr/bin/env python3
"""Whole-link wall time, including provenance and readback; no work is excluded."""
import argparse
import hashlib
import json
import os
import pathlib
import selectors
import subprocess
import time
import tomllib

ROOT = pathlib.Path(__file__).resolve().parent.parent
BOUND_SECONDS = 30.0


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def measured(argv, output, env):
    start = time.monotonic()
    phases = []
    with output.with_suffix('.stdout').open('wb') as stdout:
        child = subprocess.Popen(list(map(str, argv)), stdout=stdout, stderr=subprocess.PIPE, env=env)
        stderr = bytearray()
        pending = bytearray()
        try:
            with selectors.DefaultSelector() as selector:
                selector.register(child.stderr, selectors.EVENT_READ)
                while selector.get_map():
                    if time.monotonic() - start > 600:
                        raise TimeoutError('hello link exceeded the 600-second safety limit')
                    for key, _ in selector.select(timeout=1):
                        data = os.read(key.fd, 65536)
                        if not data:
                            selector.unregister(key.fileobj)
                            continue
                        stderr.extend(data)
                        pending.extend(data)
                        while b'\n' in pending:
                            line, _, pending = pending.partition(b'\n')
                            if line.startswith(b'ligature-phase '):
                                name = line.decode().split(' ', 1)[1]
                                phases.append({'name': name, 'at_seconds': time.monotonic() - start})
                                print('PHASE', phases[-1], flush=True)
                status = child.wait(timeout=10)
        finally:
            if child.poll() is None:
                child.kill()  # Only this harness's child pid, inside the test container.
                child.wait()
            child.stderr.close()
            output.with_suffix('.stderr').write_bytes(stderr)
    elapsed = time.monotonic() - start
    for current, following in zip(phases, phases[1:]):
        current['seconds'] = following['at_seconds'] - current['at_seconds']
    return {'seconds': elapsed, 'exit': status, 'phases': phases}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--linker', type=pathlib.Path, default=ROOT / 'target/ligature')
    parser.add_argument('--runs', type=int, choices=(1, 3), default=3)
    args = parser.parse_args()
    out = ROOT / 'target/hello-budget'
    out.mkdir(parents=True, exist_ok=True)
    inputs = ROOT / '.link-inputs'
    runtime = ROOT / '.wolf-bin/musl/libwolf_rt.a'
    pin = tomllib.loads((ROOT / 'wolf-toolchain.toml').read_text())['wolf-rt']
    for _ in range(2):
        assert digest(runtime) == pin['libwolf_rt'], 'musl runtime digest mismatch'
        for row in (ROOT / 'tests/pax-link.sums').read_text().splitlines():
            name, sha, size = row.split()
            path = inputs / name
            assert path.stat().st_size == int(size) and digest(path) == sha, name
    env = dict(os.environ, WOLF_STD=str(ROOT / '.wolf-bin/std'))
    subprocess.run([str(ROOT / '.wolf-bin/wolf'), 'build', '--emit=obj',
                    str(ROOT / 'tests/corpus/hello/hello.lu'), '-o', str(out / 'hello.o')],
                   env=env, check=True, timeout=180)
    lib = inputs / 'sysroot'
    exe = out / 'hello'
    argv = [args.linker, '-static', '-nostdlib', '--gc-sections',
            '--undefined=__wolf_rt_trap_at', '--defsym=wolf_trap=__wolf_rt_trap_at',
            '-o', exe, lib / 'crt1.o', lib / 'crti.o', '--start-group',
            out / 'hello.o', runtime, lib / 'libc.a', lib / 'libunwind.a',
            '--end-group', lib / 'crtn.o']
    rows = []
    hashes = []
    for index in range(args.runs):
        row = measured(argv, out / f'link-{index}', dict(env, LIGATURE_PROFILE='1'))
        rows.append(row)
        report = {'bound_seconds': BOUND_SECONDS, 'rows': rows, 'hashes': hashes,
                  'source_head': os.environ.get('LIGATURE_SOURCE_HEAD', 'unrecorded')}
        (out / 'results.json').write_text(json.dumps(report, indent=2) + '\n')
        assert row['exit'] == 0, ('hello-link', row)
        hashes.append(digest(exe))
        report['hashes'] = hashes
        (out / 'results.json').write_text(json.dumps(report, indent=2) + '\n')
        print('HELLO', index, row['seconds'], hashes[-1], flush=True)
    assert len(set(hashes)) == 1, 'nondeterministic hello'
    subprocess.run([str(args.linker), 'verify', str(exe)], check=True, timeout=600)
    result = subprocess.run([str(exe)], capture_output=True, timeout=30)
    assert (result.returncode, result.stdout, result.stderr) == (0, b'hello, wolf\n', b''), result
    assert all(row['seconds'] <= BOUND_SECONDS for row in rows), ('hello-link-budget-30s', rows)
    print('hello-link-budget-30s: PASS; deterministic, verified, executed; 0 SKIP')


if __name__ == '__main__':
    main()
