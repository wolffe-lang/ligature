#!/usr/bin/env python3
"""Unpack the staged archive, hash every file twice, link and execute hello."""
import argparse
import hashlib
import json
import os
import pathlib
import subprocess
import tarfile
import tomllib

ROOT = pathlib.Path(__file__).resolve().parent.parent


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def call(argv, **kwargs):
    result = subprocess.run(list(map(str, argv)), capture_output=True, timeout=900, **kwargs)
    assert result.returncode == 0, (list(map(str, argv)), result.returncode, result.stderr[-4000:])
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('stage', type=pathlib.Path)
    args = parser.parse_args()
    receipt = json.loads((args.stage / 'receipt.json').read_text())
    archive = args.stage / receipt['archive']
    expected = {}
    for row in (ROOT / 'tests/pax-link.sums').read_text().splitlines():
        name, sha, _ = row.split()
        expected[name] = sha
    expected['libwolf_rt.a'] = tomllib.loads((ROOT / 'wolf-toolchain.toml').read_text())['wolf-rt']['libwolf_rt']
    for name, sha in expected.items():
        assert receipt['members'][name]['sha256'] == sha, ('binary pin', name)
    for _ in range(2):
        assert digest(archive) == receipt['sha256_read_twice'][0] == receipt['sha256_read_twice'][1]
    out = ROOT / 'target/evidence/bundle-smoke'
    out.mkdir(parents=True, exist_ok=True)
    extracted = out / 'unpacked'
    extracted.mkdir(exist_ok=False)
    with tarfile.open(archive) as tf:
        members = tf.getmembers()
        assert [m.name for m in members] == sorted(receipt['members']), 'exact unpack roster'
        for member in members:
            path = pathlib.PurePosixPath(member.name)
            assert member.isfile() and not path.is_absolute() and '..' not in path.parts
            assert member.mode == (0o755 if member.name in {'cc', 'ld.lld'} else 0o644)
        tf.extractall(extracted, filter='data')
    manifest = dict(line.split('  ', 1)[::-1] for line in (extracted / 'MANIFEST').read_text().splitlines())
    assert set(manifest) == set(receipt['members']) - {'MANIFEST'}
    assert (extracted / 'MANIFEST').read_bytes() == (args.stage / 'MANIFEST').read_bytes()
    hashes = {}
    for name, record in receipt['members'].items():
        reads = [digest(extracted / name) for _ in range(2)]
        assert reads == record['sha256_read_twice'] == [record['sha256']] * 2
        assert (extracted / name).stat().st_size == record['size']
        if name != 'MANIFEST':
            assert manifest[name] == reads[0]
        hashes[name] = reads
    version = call([extracted / 'ld.lld', '--version']).stdout.decode().strip()
    assert version == 'LLD 17.0.6 (compatible with GNU linkers)', version
    env = dict(os.environ, WOLF_STD=str(ROOT / '.wolf-bin/std'),
               WOLF_RT_LIB=str(extracted / 'libwolf_rt.a'),
               PAX_LLD=str(extracted / 'ld.lld'), PAX_CC_SYSROOT=str(extracted / 'sysroot'),
               LIGATURE_SYSROOT=str(extracted / 'sysroot'))
    obj = out / 'hello.o'
    call([ROOT / '.wolf-bin/wolf', 'build', '--emit=obj', ROOT / 'tests/corpus/hello/hello.lu', '-o', obj], env=env)
    rows = []
    for name, linker in [('bundle-cc-lld', extracted / 'cc'), ('ligature', ROOT / 'target/ligature')]:
        exe = out / name
        call([linker, '-static', '-o', exe, obj, extracted / 'libwolf_rt.a', '-lpthread', '-ldl', '-lm',
              '-Wl,--gc-sections', '-Wl,--undefined=__wolf_rt_trap_at', '-Wl,--defsym=wolf_trap=__wolf_rt_trap_at'], env=env)
        result = call([exe])
        assert (result.stdout, result.stderr) == (b'hello, wolf\n', b''), (name, result)
        if name == 'ligature':
            call([linker, 'verify', exe])
        rows.append({'linker': name, 'stdout': result.stdout.decode(), 'exit': result.returncode,
                     'sha256_read_twice': [digest(exe), digest(exe)]})
    (out / 'results.json').write_text(json.dumps({'archive': receipt['archive'], 'version': version,
                                                 'unpacked_hashes_read_twice': hashes, 'runs': rows}, indent=2) + '\n')
    print('bundle-smoke: every unpacked file hashed twice; LLD version; cc/LLD and ligature hello executed; 0 SKIP')


if __name__ == '__main__':
    main()
