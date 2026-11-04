#!/usr/bin/env python3
"""Licensed-bundle boundary, offline mutations and Linux CI wiring."""
import hashlib
import io
import pathlib
import runpy
import tarfile
import tempfile
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
ARCHIVE = '8210ac2223d969ab8f0845cc74950a1c68226b58b10dd083cd2e2113acd3e37a'
MANIFEST = '8bcea75770a47a23f619ad778d05c84a028f2e840964302d164195ea74e73886'
rows = []


def row(name, action):
    try:
        action()
    except Exception as error:
        rows.append(name)
        print(f'FAIL {name}: {error}', flush=True)
    else:
        print(f'PASS {name}', flush=True)


# Base fetch scripts run on import; prevent any network access during discovery.
original = urllib.request.urlretrieve
urllib.request.urlretrieve = lambda *_: (_ for _ in ()).throw(RuntimeError('fetch executed on import'))
try:
    try:
        module = runpy.run_path(str(ROOT / 'tools/fetch-bundle'))
    except RuntimeError:
        module = {}
finally:
    urllib.request.urlretrieve = original


def pin():
    assert module.get('SHA') == ARCHIVE, 'licensed archive digest not pinned'
    assert module.get('MANIFEST_SHA') == MANIFEST, 'licensed MANIFEST digest not pinned'
    assert module['URL'].endswith('/link-bundle-wolf-0.2.36/musl-link-bundle-sha256-' + ARCHIVE + '.tar.gz')


row('licensed-bundle-pin', pin)
(ROOT / 'target').mkdir(exist_ok=True)
with tempfile.TemporaryDirectory(dir=ROOT / 'target') as temp:
    temp = pathlib.Path(temp)
    files = {'NOTICE': b'licence notice\n', 'sysroot/crt1.o': b'object bytes'}
    manifest = ''.join(f'{hashlib.sha256(data).hexdigest()}  {name}\n' for name, data in sorted(files.items())).encode()
    manifest_sha = hashlib.sha256(manifest).hexdigest()

    def archive(name, entries):
        path = temp / name
        with tarfile.open(path, 'w:gz') as tf:
            for name, data in entries:
                member = tarfile.TarInfo(name)
                if data is None:
                    member.type = tarfile.SYMTYPE
                    member.linkname = '/outside'
                    tf.addfile(member)
                else:
                    member.size = len(data)
                    tf.addfile(member, io.BytesIO(data))
        return path, hashlib.sha256(path.read_bytes()).hexdigest()

    entries = [('MANIFEST', manifest), *files.items()]

    def check(name, entries, expected=None, archive_sha=None, manifest_pin=manifest_sha):
        def action():
            path, sha = archive(name + '.tar.gz', entries)
            verify = module.get('verify_bundle')
            assert verify is not None, 'missing archive/MANIFEST/member verifier'
            try:
                verify(path, archive_sha or sha, manifest_pin)
            except SystemExit as error:
                assert expected and expected in str(error), (expected, str(error))
            else:
                assert expected is None, f'accepted {expected}'
        row(name, action)

    check('licensed-bundle-valid', entries)
    check('licensed-bundle-archive-digest', entries, 'REFUSED link bundle digest', archive_sha='0' * 64)
    check('licensed-bundle-manifest-digest', entries, 'REFUSED link bundle MANIFEST digest', manifest_pin='0' * 64)
    check('licensed-bundle-member-digest', [('MANIFEST', manifest), ('NOTICE', b'changed'), ('sysroot/crt1.o', files['sysroot/crt1.o'])], 'REFUSED link bundle member NOTICE')
    check('licensed-bundle-missing-member', entries[:-1], 'REFUSED link bundle missing member sysroot/crt1.o')
    check('licensed-bundle-extra-member', entries + [('extra', b'unknown')], 'REFUSED link bundle unexpected member extra')
    check('licensed-bundle-duplicate-member', entries + [('NOTICE', b'duplicate')], 'REFUSED link bundle duplicate member NOTICE')
    check('licensed-bundle-symlink', [('MANIFEST', manifest), ('NOTICE', None), ('sysroot/crt1.o', files['sysroot/crt1.o'])], 'REFUSED link bundle non-file NOTICE')
    check('licensed-bundle-traversal', entries + [('../escape', b'outside')], 'REFUSED link bundle path ../escape')
    malformed = b'not a SHA256 roster\n'
    check('licensed-bundle-manifest-format', [('MANIFEST', malformed)], 'REFUSED link bundle MANIFEST format', manifest_pin=hashlib.sha256(malformed).hexdigest())


def wiring():
    ci = (ROOT / '.github/workflows/ci.yml').read_text()
    assert 'tools/check --require-licensed-bundle' in ci, 'Linux CI does not demand licensed real-link/self-link rows'
    gate = (ROOT / 'tools/check').read_text()
    assert 'tests/real-ligature.py' in gate, 'missing real-ligature hello row'
    assert 'LIGATURE_REQUIRE_SELF_LINK=1' in gate, 'CI still admits historical BLOCKED self-link'


row('licensed-bundle-ci-rows', wiring)
if rows:
    raise SystemExit(1)
print('licensed-bundle: exact pins, ten offline archive boundaries and strict CI wiring; 0 SKIP')
