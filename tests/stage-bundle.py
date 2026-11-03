#!/usr/bin/env python3
"""Bundle staging is reproducible, input-pinned, and never publishes."""
import hashlib
import pathlib
import runpy
import shutil
import tarfile
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
stage = runpy.run_path(str(ROOT / 'tools/stage-bundle'))['stage']


def sha(data):
    return hashlib.sha256(data).hexdigest()


def refused(call, text):
    try:
        call()
    except ValueError as error:
        assert text in str(error), error
    else:
        raise AssertionError('missing refusal: ' + text)


(ROOT / 'target').mkdir(exist_ok=True)
with tempfile.TemporaryDirectory(prefix='stage-bundle-test-', dir=ROOT / 'target') as temp:
    root = pathlib.Path(temp)
    bundle = root / 'inputs'
    (bundle / 'sysroot').mkdir(parents=True)
    expected = {}
    names = ['cc', 'ld.lld', 'libwolf_rt.a', 'sysroot/crt1.o', 'sysroot/crti.o',
             'sysroot/crtn.o', 'sysroot/libc.a', 'sysroot/libunwind.a']
    for name in names:
        data = ('original:' + name).encode()
        (bundle / name).write_bytes(data)
        expected[name] = (sha(data), len(data))
    runtime = root / 'runtime.a'
    runtime.write_bytes(b'new musl runtime')
    runtime_sha = sha(runtime.read_bytes())
    first = stage(bundle, runtime, expected, runtime_sha, root / 'one')
    second = stage(bundle, runtime, expected, runtime_sha, root / 'two')
    assert first == second and first['published'] is False
    archive = root / 'one' / first['archive']
    assert archive.read_bytes() == (root / 'two' / second['archive']).read_bytes()
    with tarfile.open(archive) as tf:
        required = {'NOTICE', 'MANIFEST', 'SOURCES.json', 'LICENSES/musl/COPYRIGHT',
                    'LICENSES/llvm/llvm/LICENSE.TXT', 'LICENSES/llvm/lld/LICENSE.TXT',
                    'LICENSES/llvm/libunwind/LICENSE.TXT', 'LICENSES/rust/COPYRIGHT-library.html',
                    'LICENSES/wolf/LICENSE', 'LICENSES/wolf/LICENSE-EXCEPTION',
                    'LICENSES/pax/LICENSE'}
        assert required <= set(tf.getnames()), 'bundle-licence-roster: missing complete notices'
        assert tf.getnames() == sorted(first['members'])
        manifest = dict(line.split('  ', 1)[::-1] for line in tf.extractfile('MANIFEST').read().decode().splitlines())
        assert set(manifest) == set(tf.getnames()) - {'MANIFEST'}, 'manifest covers every other file'
        for name, expected_sha in manifest.items():
            assert sha(tf.extractfile(name).read()) == expected_sha, ('manifest', name)
        for name in names:
            member = tf.getmember(name)
            assert member.mode == (0o755 if name in {'cc', 'ld.lld'} else 0o644)
            expected_data = runtime.read_bytes() if name == 'libwolf_rt.a' else (bundle / name).read_bytes()
            assert tf.extractfile(name).read() == expected_data
    assert first['members']['libwolf_rt.a']['sha256'] == runtime_sha
    assert all(r['sha256_read_twice'] == [r['sha256'], r['sha256']] for r in first['members'].values())
    notices = root / 'notices'
    shutil.copytree(ROOT / 'bundle/notices', notices)
    licence = notices / 'LICENSES/musl/COPYRIGHT'
    original = licence.read_bytes()
    licence.unlink()
    refused(lambda: stage(bundle, runtime, expected, runtime_sha, root / 'missing-licence', notices), 'missing licence')
    licence.write_bytes(original + b'\naltered\n')
    refused(lambda: stage(bundle, runtime, expected, runtime_sha, root / 'altered-licence', notices), 'licence digest')
    licence.unlink()
    licence.symlink_to(ROOT / 'bundle/notices/LICENSES/musl/COPYRIGHT')
    refused(lambda: stage(bundle, runtime, expected, runtime_sha, root / 'symlink-licence', notices), 'missing licence')
    licence.unlink()
    licence.write_bytes(original)
    (notices / 'extra.txt').write_text('not admitted')
    refused(lambda: stage(bundle, runtime, expected, runtime_sha, root / 'extra-notice', notices), 'uninventoried')
    assert len((root / 'one/pax-link.sums').read_text().splitlines()) == 8
    refused(lambda: stage(bundle, runtime, {}, runtime_sha, root / 'bad-roster'), 'roster')
    refused(lambda: stage(bundle, runtime, expected, '0' * 64, root / 'bad-runtime'), 'replacement')
    (bundle / 'sysroot/crt1.o').write_bytes(b'changed')
    refused(lambda: stage(bundle, runtime, expected, runtime_sha, root / 'bad-input'), 'sysroot/crt1.o')
    assert not list((root / 'bad-input').glob('*.tar.gz'))
    assert not list((root / 'bad-runtime').glob('*.tar.gz'))
print('stage-bundle: deterministic licensed bytes, complete manifest, replacement runtime, seven refusals; 0 SKIP')
