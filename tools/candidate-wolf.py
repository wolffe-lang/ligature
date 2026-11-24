#!/usr/bin/env python3
"""Digest-stage a compiler candidate and build all shipped/tested Wolf programs.

The source inventory is discovered for each invocation, not copied from a gate's
current list. --source-root diagnoses historical committed sources with this
runner unchanged. It never changes the production toolchain or executes tests.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import tomllib

ROOT = Path(__file__).resolve().parents[1]


class Failure(Exception):
    def __init__(self, row, detail):
        self.row, self.detail = row, detail


def fail(row, detail):
    raise Failure(row, detail)


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def target():
    pair = (platform.system(), platform.machine())
    choices = {('Darwin', 'arm64'): 'aarch64-apple-darwin',
               ('Linux', 'x86_64'): 'x86_64-unknown-linux-gnu',
               ('Linux', 'aarch64'): 'aarch64-unknown-linux-gnu'}
    if pair not in choices:
        fail('inputs', f'unsupported host {pair}')
    return choices[pair]


def stage_path():
    return Path(os.environ.get('LIGATURE_CANDIDATE_STAGE', ROOT / 'target/candidate-wolf')).resolve()


def files_at(stage):
    out = {}
    for path in sorted(stage.rglob('*')):
        if path.is_symlink():
            fail('inputs', f'stage contains symlink {path}')
        if path.is_file() and path.name != 'STAGE.json':
            out[path.relative_to(stage).as_posix()] = sha(path)
    return out


def verify(stage, pin):
    wolf = Path(os.environ.get('LIGATURE_CANDIDATE_WOLF', stage / 'wolf')).resolve()
    std = Path(os.environ.get('LIGATURE_CANDIDATE_STD', stage / 'std')).resolve()
    if wolf != stage / 'wolf' or std != stage / 'std':
        fail('inputs', 'compiler and std must belong to the digest-verified stage')
    if not wolf.is_file() or not os.access(wolf, os.X_OK) or not (std / 'STD-REV').is_file():
        fail('inputs', 'executable compiler and bundled std required')
    receipt_path = stage / 'STAGE.json'
    if not receipt_path.is_file():
        fail('inputs', 'digest-staging receipt required')
    receipt = json.loads(receipt_path.read_text())
    if any(str(receipt.get(k)) != str(pin[k]) for k in ('run', 'rev')) or receipt.get('archive_sha256') != pin[target()]:
        fail('inputs', 'candidate staging identity differs from pin')
    if receipt.get('files') != files_at(stage):
        fail('inputs', 'candidate staged files differ from receipt')
    if (std / 'STD-REV').read_text().strip() != pin['std_rev']:
        fail('std', 'bundled std differs from pin')
    q = subprocess.run([str(wolf), '--version'], capture_output=True, text=True, timeout=30)
    version = q.stdout.splitlines()[0] if q.stdout else ''
    if q.returncode or version != pin['version_line']:
        fail('version', f'got {version!r}, expected {pin["version_line"]!r}')
    print(f'PASS candidate-wolf-version {version}', flush=True)
    print(f'PASS candidate-wolf-std {pin["std_rev"]}', flush=True)
    return wolf, std


def fetch(pin):
    stage = stage_path()
    if stage.exists():
        verify(stage, pin)
        print(f'PASS candidate-wolf-archive staged {pin[target()]}', flush=True)
        return
    parent = ROOT / 'target'
    parent.mkdir(exist_ok=True)
    if platform.system() == 'Darwin' and shutil.disk_usage(parent).free < 15 * (1 << 30):
        fail('archive', 'less than 15 GiB free before candidate transfer/extraction')
    with tempfile.TemporaryDirectory(prefix='candidate-fetch-', dir=parent) as tmp:
        work = Path(tmp)
        archive_env = os.environ.get('LIGATURE_CANDIDATE_ARCHIVE')
        if archive_env:
            archive = Path(archive_env).resolve()
        else:
            artifact = {'aarch64-apple-darwin': 'archive-macos-latest',
                        'x86_64-unknown-linux-gnu': 'archive-ubuntu-22.04',
                        'aarch64-unknown-linux-gnu': 'archive-ubuntu-22.04-arm'}[target()]
            download = work / 'download'
            download.mkdir()
            q = subprocess.run(['gh', 'run', 'download', pin['run'], '-R', pin['repo'], '-n', artifact, '-D', str(download)], capture_output=True, text=True)
            if q.returncode:
                fail('archive', 'artifact download failed or expired: ' + q.stderr.strip())
            archive = download / f'wolf-{pin["archive_version"]}-{target()}.tar.gz'
        if not archive.is_file():
            fail('archive', 'supplied archive is missing')
        if sha(archive) != pin[target()] or sha(archive) != pin[target()]:
            fail('archive', 'SHA-256 differs from candidate pin')
        prefix = f'wolf-{pin["archive_version"]}-{target()}'
        unpack = work / 'unpack'
        unpack.mkdir()
        with tarfile.open(archive, 'r:gz') as tar:
            seen = set()
            members = tar.getmembers()
            total = 0
            for member in members:
                path = PurePosixPath(member.name)
                if path.is_absolute() or '..' in path.parts or not path.parts or path.parts[0] != prefix or member.name in seen or not (member.isdir() or member.isfile()):
                    fail('archive', f'unsafe or duplicate archive member {member.name!r}')
                seen.add(member.name)
                total += member.size
            if total > 2 * (1 << 30):
                fail('archive', 'candidate extraction exceeds 2 GiB')
            if platform.system() == 'Darwin' and shutil.disk_usage(parent).free - total < 15 * (1 << 30):
                fail('archive', 'extraction would cross 15 GiB disk floor')
            for member in members:
                dest = unpack / member.name
                if member.isdir():
                    dest.mkdir(parents=True, exist_ok=True)
                else:
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    stream = tar.extractfile(member)
                    if stream is None:
                        fail('archive', 'missing regular member data')
                    with stream, dest.open('wb') as output:
                        shutil.copyfileobj(stream, output)
                    dest.chmod(member.mode & 0o777)
        base = unpack / prefix
        receipt = dict(archive_sha256=pin[target()], run=pin['run'], rev=pin['rev'], files=files_at(base))
        (base / 'STAGE.json').write_text(json.dumps(receipt, sort_keys=True, indent=2) + '\n')
        # Validate before publishing the new stage. The executable has a verified digest.
        old_wolf = os.environ.pop('LIGATURE_CANDIDATE_WOLF', None)
        old_std = os.environ.pop('LIGATURE_CANDIDATE_STD', None)
        try:
            verify(base, pin)
        finally:
            if old_wolf is not None:
                os.environ['LIGATURE_CANDIDATE_WOLF'] = old_wolf
            if old_std is not None:
                os.environ['LIGATURE_CANDIDATE_STD'] = old_std
        stage.parent.mkdir(parents=True, exist_ok=True)
        base.rename(stage)
    print(f'PASS candidate-wolf-archive {pin[target()]}', flush=True)


def tokens(text):
    """Lex enough to identify a top-level main, ignoring comments/string bodies."""
    at, n = 0, len(text)
    while at < n:
        if text.startswith('//', at):
            end = text.find('\n', at)
            at = n if end < 0 else end + 1
        elif text.startswith('/*', at):
            at += 2
            depth = 1
            while at < n and depth:
                if text.startswith('/*', at):
                    depth += 1
                    at += 2
                elif text.startswith('*/', at):
                    depth -= 1
                    at += 2
                else:
                    at += 1
            if depth:
                fail('discovery', 'unterminated block comment')
        elif text[at] in ('"', "'"):
            quote = text[at]
            at += 1
            while at < n and text[at] != quote:
                at += 2 if text[at] == '\\' else 1
            if at >= n:
                fail('discovery', 'unterminated string/character')
            at += 1
        elif text[at].isalpha() or text[at] == '_':
            start = at
            at += 1
            while at < n and (text[at].isalnum() or text[at] == '_'):
                at += 1
            yield text[start:at]
        else:
            if text[at] in '{}(':
                yield text[at]
            at += 1


def programs(root):
    out = {}
    for folder in ('src', 'tests'):
        for path in sorted((root / folder).rglob('*.lu')):
            relative = path.relative_to(root)
            if any(part.startswith('.') for part in relative.parts):
                continue
            words = list(tokens(path.read_text()))
            depth, mains = 0, 0
            for i, word in enumerate(words):
                if depth == 0 and words[i:i + 3] == ['fn', 'main', '(']:
                    mains += 1
                if word == '{':
                    depth += 1
                elif word == '}':
                    depth -= 1
            is_test = folder == 'tests' or path.name.endswith('_test.lu')
            if path.name.endswith('_test.lu') and not mains:
                fail('discovery', f'{relative}: test program has no main')
            if not mains:
                continue
            if mains != 1 or depth != 0:
                fail('discovery', f'{relative}: ambiguous or unbalanced program')
            name = (relative.relative_to('src') if folder == 'src' else relative).with_suffix('').as_posix()
            if name in out:
                fail('discovery', f'duplicate program identity {name}')
            out[name] = (relative.as_posix(), is_test)
    if not out or not any(not test for _, test in out.values()):
        fail('discovery', 'at least one shipped main required')
    return dict(sorted(out.items()))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--fetch', action='store_true')
    parser.add_argument('--source-root', type=Path, default=ROOT)
    parser.add_argument('--program')
    parser.add_argument('--tier', choices=('native', 'release'))
    parser.add_argument('--list', action='store_true')
    args = parser.parse_args()
    pin = tomllib.loads((ROOT / 'candidate-wolf.toml').read_text())['wolf-candidate']
    if args.fetch:
        fetch(pin)
        return 0
    source = args.source_root.resolve()
    inventory = programs(source)
    if args.program is not None and args.program not in inventory:
        fail('arguments', 'unknown/empty program selection')
    selected = {args.program: inventory[args.program]} if args.program is not None else inventory
    tiers = (args.tier,) if args.tier else ('native', 'release')
    cells = [(name, path, tier) for tier in tiers for name, (path, test) in selected.items()
             if tier == 'native' or not test or (args.program is not None and args.tier == 'release')]
    if args.list:
        print(json.dumps([dict(program=name, source=path, tier=tier) for name, path, tier in cells], indent=2))
        return 0
    stage = stage_path()
    # Explicitly provided stages never trigger an unrequested network fallback.
    if not stage.exists() and 'LIGATURE_CANDIDATE_STAGE' not in os.environ:
        fetch(pin)
    wolf, std = verify(stage, pin)
    output = Path(os.environ.get('LIGATURE_CANDIDATE_OUTPUT', ROOT / 'target/candidate-build')).resolve()
    output.mkdir(parents=True, exist_ok=True)
    failed, counts = False, {}
    print(f'candidate-wolf: programs={len(selected)} cells={len(cells)} source={source}', flush=True)
    home = output / 'home'
    home.mkdir(exist_ok=True)
    env = dict(os.environ, WOLF_STD=str(std), HOME=str(home), SHELL='/bin/sh', LC_ALL='C')
    for name, path, tier in cells:
        binary = output / f'{name}-{tier}'
        log = output / f'{name}-{tier}.log'
        log.parent.mkdir(parents=True, exist_ok=True)
        binary.unlink(missing_ok=True)
        command = [str(wolf), 'build', '--no-cache', '--error-limit=0', '--deny-warnings']
        if tier == 'release':
            command.append('--release')
        command += [path, '-o', str(binary)]
        try:
            with log.open('wb') as stream:
                q = subprocess.run(command, cwd=source, env=env, stdout=stream, stderr=subprocess.STDOUT, timeout=600)
            rc = q.returncode
        except subprocess.TimeoutExpired:
            rc = 124
        text = log.read_text(errors='replace')
        counts[name, tier] = len(re.findall(r'^error\[E1010\]', text, re.M))
        if rc == 0 and binary.is_file() and os.access(binary, os.X_OK) and not re.search(r'^(?:error|warning)\[', text, re.M):
            print(f'PASS candidate-wolf-build-{name}-{tier}', flush=True)
        else:
            failed = True
            print(f'FAIL candidate-wolf-build-{name}-{tier}: exit {rc}' + (' (missing executable or diagnostic)' if rc == 0 else ''), flush=True)
            for line in text.splitlines():
                print('  ' + line, flush=True)
    compared, split = 0, False
    for name, (_, test) in selected.items():
        if test or (name, 'native') not in counts or (name, 'release') not in counts:
            continue
        compared += 1
        native, release = counts[name, 'native'], counts[name, 'release']
        if native != release:
            split = failed = True
            print(f'FAIL candidate-wolf-tier-independent: {name} E1010 native {native}, release {release}', flush=True)
    if compared and not split:
        print(f'PASS candidate-wolf-tier-independent: E1010 counts agree for {compared} programs', flush=True)
    (output / 'inventory.json').write_text(json.dumps([dict(program=n, source=p, tier=t, E1010=counts[n, t]) for n, p, t in cells], indent=2) + '\n')
    return int(failed)


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Failure as error:
        print(f'FAIL candidate-wolf-{error.row}: {error.detail}', flush=True)
        sys.exit(1)
    except (OSError, ValueError, KeyError, tarfile.TarError, subprocess.SubprocessError) as error:
        print(f'FAIL candidate-wolf-inputs: {error}', flush=True)
        sys.exit(1)
