#!/usr/bin/env python3
"""Rerun the linking tests with trunk's linker; every ELF executable they write must be identical.

The tests run once with the candidate (target/ligature) and once with trunk's binary in its place,
from the same tree, so every object and path is the same. Each run's target/evidence is kept aside;
every ET_EXEC file in the two is hashed and compared, and the two file sets must be equal.
usage: identity-suite.py TRUNK_BINARY   (cwd: the tree, after the core step built target/ligature)
"""
import hashlib, json, os, pathlib, shutil, subprocess, sys

ROOT = pathlib.Path.cwd()
TESTS = ['integration', 'oracle', 'resolution', 'resolve', 'lazy-order', 'writer', 'relocation-witness',
         'cc', 'provenance', 'attribution', 'compact', 'classify-static', 'findings', 'layout-controls',
         'kernel-script', 'kernel-edge', 'pc32', 'addrsig', 'aarch64', 'archive-write', 'real-ligature',
         'self-link']
EVIDENCE = ROOT / 'target/evidence'
LINKER = ROOT / 'target/ligature'


def executables(base):
    found = {}
    for p in sorted(base.rglob('*')):
        if not p.is_file() or p.is_symlink():
            continue
        with p.open('rb') as f:
            head = f.read(18)
        if len(head) == 18 and head[:4] == b'\x7fELF' and head[16] == 2 and head[17] == 0:
            with p.open('rb') as f:
                found[str(p.relative_to(base))] = hashlib.file_digest(f, 'sha256').hexdigest()
    return found


def run(label):
    if EVIDENCE.exists():
        shutil.rmtree(EVIDENCE)
    for t in TESTS:
        p = subprocess.run([sys.executable, '-I', f'tests/{t}.py'], capture_output=True, text=True, timeout=3600)
        tail = (p.stdout.strip().splitlines() or [''])[-1][:160]
        print(f'identity {label} {t} exit={p.returncode} {tail}', flush=True)
        if p.returncode != 0:
            print(p.stdout[-1500:], p.stderr[-1500:], flush=True)
            raise SystemExit(f'FAIL identity-suite: {t} failed under the {label} linker')
    kept = ROOT / f'target/identity-{label}'
    if kept.exists():
        shutil.rmtree(kept)
    EVIDENCE.rename(kept)
    return executables(kept)


trunk = pathlib.Path(sys.argv[1]).resolve()
aside = ROOT / 'target/evidence-before-identity'
if aside.exists():
    shutil.rmtree(aside)
if EVIDENCE.exists():
    EVIDENCE.rename(aside)
candidate_copy = ROOT / 'target/ligature.candidate'
shutil.copy2(LINKER, candidate_copy)
try:
    candidate = run('candidate')
    shutil.copy2(trunk, LINKER)
    baseline = run('trunk')
finally:
    shutil.copy2(candidate_copy, LINKER)
    if aside.exists():
        if EVIDENCE.exists():
            shutil.rmtree(EVIDENCE)
        aside.rename(EVIDENCE)
(ROOT / 'target/identity-suite.json').write_text(json.dumps({'candidate': candidate, 'trunk': baseline}, indent=2) + '\n')
differ = sorted(k for k in candidate.keys() & baseline.keys() if candidate[k] != baseline[k])
only = sorted(candidate.keys() ^ baseline.keys())
for k in differ:
    print(f'FAIL identity-suite: {k} candidate {candidate[k]} trunk {baseline[k]}', flush=True)
for k in only:
    print(f'FAIL identity-suite: {k} written by one run only', flush=True)
if differ or only or not candidate:
    sys.exit(1)
print(f'PASS identity-suite: {len(candidate)} ELF executables from {len(TESTS)} linking tests byte-identical '
      f'under trunk and the candidate; 0 SKIP', flush=True)
