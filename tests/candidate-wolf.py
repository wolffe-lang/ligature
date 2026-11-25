#!/usr/bin/env python3
"""Prediction: the next-wolf leaf builds every discovered main, including nested tests.

Shipped programs build on native/release, tests on native. Missing/wrong candidate
inputs and compiler exit 2 fail by name, every cell is attempted, and tier-split
E1010 counts fail. The real compiler runs in the local record only; hosted gates
run these fixtures. No compiler or network is needed by this test.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[1]
CHECK = ROOT / 'tools/check-candidate-wolf'
FETCH = ROOT / 'tools/fetch-candidate-wolf'
failed = 0


def say(ok, name, detail=''):
    global failed
    print(('PASS ' if ok else 'FAIL ') + 'candidate-wolf-' + name + (': ' + detail if detail else ''), flush=True)
    failed += not ok


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    say(CHECK.is_file() and FETCH.is_file(), 'runner-present')
    if not CHECK.is_file() or not FETCH.is_file():
        return 1
    # env_get has missing/utf8, not env_set's invalid row. An unknown bare
    # pattern binds the error and shadows the next arm (E0802 with deny-warnings).
    host = (ROOT / 'tests/corpus/pax/host.lu').read_text()
    home = re.search(r'^fn home\(\) -> str \{.*?^\}', host, re.M | re.S)
    arms = re.findall(r'(\w+)\s*=>\s*"([^"]*)"', home[0]) if home else []
    say(sorted(arms) == [('missing', 'missing'), ('utf8', 'utf8')], 'pax-host-env-row')
    image = (ROOT / 'ci/oracle.Containerfile').read_text()
    say('clang-17=1:17.0.6-9ubuntu1' in image and 'WOLF_CLANG=/usr/bin/clang-17' in image,
        'release-image-clang')
    (ROOT / 'target').mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='candidate-test-', dir=ROOT / 'target') as tmp:
        work = Path(tmp)
        tree = work / 'tree'
        (tree / 'tools').mkdir(parents=True)
        for name in ('check-candidate-wolf', 'fetch-candidate-wolf', 'candidate-wolf.py'):
            shutil.copy2(ROOT / 'tools' / name, tree / 'tools' / name)
        shutil.copy2(ROOT / 'candidate-wolf.toml', tree / 'candidate-wolf.toml')
        for name in ('src/tool.lu', 'src/unit_test.lu', 'src/deep/unit_test.lu',
                     'tests/corpus/hello.lu', 'tests/fixtures/main.lu'):
            path = tree / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('//! member: false\nfn main() -> int { 0 }\n')
        for name, text in {
            'src/.cache/stale_test.lu': 'fn main() {}',
            'src/comment.lu': '// fn main() {}\n/* fn main() {} */\nconst EXAMPLE = "fn main() {}"\n',
            'src/library.lu': 'fn sample() { let s = "fn main() {}" }',
        }.items():
            path = tree / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
        stage = work / 'stage'
        (stage / 'std').mkdir(parents=True)
        (stage / 'std/STD-REV').write_text('be1d10fa2798cc6bc2a1fd0b2e559e283469c9bf\n')
        wolf = stage / 'wolf'
        wolf.write_text('#!' + sys.executable + '\n' + '''import json, os, pathlib, sys
if '--version' in sys.argv:
    print(os.environ.get('MOCK_VERSION', 'wolf 0.2.40+dev.1add9bb (wolfgang, pin 1add9bb)'))
    raise SystemExit(0)
with open(os.environ['MOCK_CALLS'], 'a') as f: f.write(json.dumps(sys.argv[1:]) + '\\n')
tier = 'RELEASE' if '--release' in sys.argv else 'NATIVE'
for _ in range(int(os.environ.get('MOCK_E1010_' + tier, '0'))): print('error[E1010]: planted')
print('compiler diagnostic')
rc = int(os.environ.get('MOCK_EXIT', '0'))
if not rc:
    out = pathlib.Path(sys.argv[sys.argv.index('-o') + 1]); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text('mock executable'); out.chmod(0o755)
raise SystemExit(rc)
''')
        wolf.chmod(0o755)
        receipt = {
            'archive_sha256': '010f537fb65b3965fa44f0726fb2b6645065bbc566c66bff98654e22fd57a62f' if sys.platform == 'darwin' else '71e641341418022c5040f557f4101a2ed1d143e92020fadc44c4d56ae9e1bb3a',
            'rev': '1add9bb36f08d4546f7c0882decd484685728794', 'run': '45097601683',
            'files': {'wolf': sha(wolf), 'std/STD-REV': sha(stage / 'std/STD-REV')},
        }
        (stage / 'STAGE.json').write_text(json.dumps(receipt))
        home = work / 'home'
        home.mkdir()
        calls = work / 'calls'
        env = dict(os.environ, HOME=str(home), SHELL='/bin/sh', LC_ALL='C', MOCK_CALLS=str(calls),
                   LIGATURE_CANDIDATE_STAGE=str(stage), LIGATURE_CANDIDATE_OUTPUT=str(work / 'out'))
        check = tree / 'tools/check-candidate-wolf'

        def run(*args, **updates):
            calls.write_text('')
            q = subprocess.run([str(check), *args], cwd=tree, env=dict(env, **updates), capture_output=True, text=True)
            seen = [json.loads(line) for line in calls.read_text().splitlines()]
            return q, seen

        def cells(seen):
            return sorted((next(x for x in call if x.endswith('.lu')), 'release' if '--release' in call else 'native') for call in seen)

        q, seen = run()
        expected = sorted([('src/tool.lu', 'native'), ('src/tool.lu', 'release'),
                           ('src/unit_test.lu', 'native'), ('src/deep/unit_test.lu', 'native'),
                           ('tests/corpus/hello.lu', 'native'), ('tests/fixtures/main.lu', 'native')])
        say(q.returncode == 0 and cells(seen) == expected, 'discovery-all-programs', q.stdout + q.stderr if q.returncode else '')
        say(all('--error-limit=0' in c and '--deny-warnings' in c and '--no-cache' in c for c in seen) and len(seen) == 6, 'complete-diagnostics')
        say('PASS candidate-wolf-tier-independent' in q.stdout, 'tier-equal')
        q, seen = run('--program', 'deep/unit_test', '--tier', 'native')
        say(q.returncode == 0 and cells(seen) == [('src/deep/unit_test.lu', 'native')], 'nested-single-row')
        q, seen = run('--program', 'unit_test', '--tier', 'release')
        say(q.returncode == 0 and cells(seen) == [('src/unit_test.lu', 'release')], 'test-release-census')
        q, seen = run('--tier', 'release')
        say(q.returncode == 0 and cells(seen) == [('src/tool.lu', 'release')] and 'tier-independent' not in q.stdout, 'release-only-shipped')
        for choice in ('', 'absent', '../escape', '/absolute'):
            q, seen = run('--program', choice)
            say(q.returncode != 0 and not seen and 'FAIL candidate-wolf-arguments' in q.stdout, 'invalid-selection-' + (choice or 'empty'))
        q, seen = run(MOCK_EXIT='2')
        say(q.returncode != 0 and len(seen) == 6 and q.stdout.count('FAIL candidate-wolf-build-') == 6 and 'exit 2' in q.stdout and '  compiler diagnostic' in q.stdout, 'exit-two-all-cells')
        q, seen = run(MOCK_EXIT='2', MOCK_E1010_NATIVE='1', MOCK_E1010_RELEASE='0')
        say(q.returncode != 0 and 'FAIL candidate-wolf-tier-independent: tool E1010 native 1, release 0' in q.stdout, 'tier-split')
        q, seen = run(MOCK_VERSION='wrong')
        say(q.returncode != 0 and not seen and 'FAIL candidate-wolf-version' in q.stdout, 'wrong-version')
        q, seen = run(LIGATURE_CANDIDATE_STAGE=str(work / 'absent'))
        say(q.returncode != 0 and not seen and 'FAIL candidate-wolf-inputs' in q.stdout, 'missing-inputs')
        saved = (stage / 'std/STD-REV').read_text()
        (stage / 'std/STD-REV').write_text('wrong\n')
        q, seen = run()
        say(q.returncode != 0 and not seen and 'FAIL candidate-wolf-' in q.stdout, 'tampered-stage')
        (stage / 'std/STD-REV').write_text(saved)
        (tree / 'src/new_main.lu').write_text('fn main() {}\n')
        (tree / 'src/deep/new_test.lu').write_text('fn main() {}\n')
        q, seen = run()
        got = cells(seen)
        say(q.returncode == 0 and len(got) == 9 and ('src/new_main.lu', 'release') in got and ('src/deep/new_test.lu', 'native') in got, 'new-main-and-test')
        (tree / 'src/missing_test.lu').write_text('fn helper() {}\n')
        q, seen = run()
        say(q.returncode != 0 and not seen and 'FAIL candidate-wolf-discovery' in q.stdout, 'test-without-main')
        (tree / 'src/missing_test.lu').unlink()
        wrong = work / 'wrong.tar.gz'
        wrong.write_bytes(b'wrong')
        fetch = tree / 'tools/fetch-candidate-wolf'
        for name, archive in [('wrong-digest', wrong), ('missing-archive', work / 'absent.tar.gz')]:
            dest = work / ('stage-' + name)
            q = subprocess.run([str(fetch)], cwd=tree, env=dict(env, LIGATURE_CANDIDATE_ARCHIVE=str(archive), LIGATURE_CANDIDATE_STAGE=str(dest)), capture_output=True, text=True)
            say(q.returncode != 0 and 'FAIL candidate-wolf-archive' in q.stdout and not dest.exists(), name)
        # Source-root mode lets a committed runner diagnose untouched historical sources.
        source = work / 'historical'
        (source / 'src').mkdir(parents=True)
        (source / 'src/old.lu').write_text('fn main() {}\n')
        q, seen = run('--source-root', str(source))
        say(q.returncode == 0 and cells(seen) == [('src/old.lu', 'native'), ('src/old.lu', 'release')], 'historical-source-root')
        # Hosted wiring remains offline, the local record requires real candidate builds.
        gate = (ROOT / 'tools/check-core').read_text()
        record = ROOT / 'tools/record-steps'
        say('python3 -I tests/candidate-wolf.py' in gate and 'tools/check-candidate-wolf' not in gate and
            record.is_file() and 'candidate-wolf' in record.read_text(), 'wiring')
        say('candidate' not in (ROOT / '.github/workflows/ci.yml').read_text(), 'no-hosted-staging')
    return bool(failed)


if __name__ == '__main__':
    sys.exit(main())
