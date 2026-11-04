#!/usr/bin/env python3
"""Same-run baseline ratios and byte identity for hello and linker objects."""
import argparse
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / 'target/evidence/link-cost'
OUT.mkdir(parents=True, exist_ok=True)
WOLF = pathlib.Path(os.environ.get('WOLF', str(ROOT / '.wolf-bin/wolf'))).resolve()
BUNDLE = ROOT / '.link-inputs'
LIB = BUNDLE / 'sysroot'
BASELINE_SHA = '950485ee8728e685b7311495797f3b961dc306d1368314b8fed578510eb40c00'


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def call(args):
    started = time.monotonic()
    result = subprocess.run(list(map(str, args)), capture_output=True, timeout=1200)
    assert result.returncode == 0, (args, result.returncode, result.stderr[-2000:])
    return time.monotonic() - started, result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--case', choices=['hello', 'self-link', 'all'], default='all')
    args = parser.parse_args()
    control = ROOT / 'tests/fixtures/ld06-relocate.baseline'
    assert digest(control) == BASELINE_SHA, 'unreviewed relocation baseline'
    source = OUT / 'baseline-src'
    shutil.copytree(ROOT / 'src', source, dirs_exist_ok=True)
    shutil.copyfile(control, source / 'relocate/relocate.lu')
    baseline = OUT / 'baseline'
    call([WOLF, 'build', '--no-cache', '--deny-warnings', source / 'ligature.lu', '-o', baseline])
    rows = []
    for case in (['hello', 'self-link'] if args.case == 'all' else [args.case]):
        row = 'link-cost-' + case
        print('START', row, flush=True)
        objects_dir = OUT / (case + '-objects')
        objects_dir.mkdir(exist_ok=True)
        for old in objects_dir.glob('*.o'):
            old.unlink()
        source = ROOT / ('tests/corpus/hello/hello.lu' if case == 'hello' else 'src/ligature.lu')
        call([WOLF, 'build', '--no-cache', '--emit=obj', source, '-o', objects_dir / 'main.o'])
        objects = sorted(objects_dir.glob('*.o'))
        assert objects and (case != 'self-link' or len(objects) > 1)
        link_args = ['-static', '-nostdlib', '--gc-sections', '--undefined=__wolf_rt_trap_at', '--defsym=wolf_trap=__wolf_rt_trap_at', LIB / 'crt1.o', LIB / 'crti.o', '--start-group', *objects, BUNDLE / 'libwolf_rt.a', LIB / 'libc.a', LIB / 'libunwind.a', '--end-group', LIB / 'crtn.o']
        times = {}
        hashes = {}
        for name, linker in [('baseline', baseline), ('candidate', ROOT / 'target/ligature')]:
            target = OUT / (case + '-' + name)
            times[name], _ = call([linker, *link_args, '-o', target])
            hashes[name] = [digest(target), digest(target)]
            print(row, name, f'{times[name]:.6f}s', hashes[name][0], flush=True)
        assert len(set(hashes['baseline'] + hashes['candidate'])) == 1, 'FAIL ' + row + '-identity'
        target = OUT / (case + '-candidate')
        _, result = call([target] + (['--version'] if case == 'self-link' else []))
        assert result.stderr == b''
        assert result.stdout.startswith(b'ligature ') if case == 'self-link' else result.stdout == b'hello, wolf\n'
        ratio = times['candidate'] / times['baseline']
        record = {'row': row, 'seconds': times, 'ratio': ratio, 'bound': 0.50, 'sha256_read_twice': hashes}
        rows.append(record)
        (OUT / 'results.json').write_text(json.dumps(rows, indent=2) + '\n')
        if ratio > 0.50:
            raise AssertionError(f'FAIL {row}: ratio={ratio:.6f} bound=0.50')
        print(f'PASS {row}: ratio={ratio:.6f} bound=0.50 byte-identical; 0 SKIP', flush=True)


if __name__ == '__main__':
    main()
