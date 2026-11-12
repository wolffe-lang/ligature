#!/usr/bin/env python3
"""Time rows: each captured link by trunk's linker and the candidate, interleaved, on one CPU.

Each link is the captured cc-shaped command, run as a direct child; its CPU time (user + sys) and
its own ru_maxrss come from wait4. Trunk runs under a 4 GiB address-space cap, the candidate under
the memory rows' 512 MiB, in its default form (the provenance in a sidecar). Rows, each PASS or
FAIL <row>:
  time-NAME         the candidate's fastest CPU time of the rounds is under 2 s
  time-determinism  every candidate output of one program, and its sidecar, is one file
  time-identity     the candidate's embedded form (--provenance=embed) of each program is the
                    file trunk's linker writes, in every round
Hello's 1 s is reported against its number, not held as a row (the time it cannot go under is
the manifest's hashing; see the lane's note). With --lld-cc and --lld, each program is also linked
once by the compiler's cc and ld.lld, and every form's size is reported beside lld's.
usage: time-rows.py --capture DIR --sysroot DIR [--rounds N] [--lld-cc CC --lld LLD] TRUNK CANDIDATE
       (cwd: the checkout; run it pinned to one CPU)
"""
import argparse
import hashlib
import json
import os
import pathlib
import resource
import sys
import time

BOUND = 2.0
PROGRAMS = ['hello', 'netproc', 'pelt', 'ligself']
p = argparse.ArgumentParser()
p.add_argument('--capture', required=True)
p.add_argument('--sysroot', required=True)
p.add_argument('--rounds', type=int, default=3)
p.add_argument('--lld-cc')
p.add_argument('--lld')
p.add_argument('trunk')
p.add_argument('candidate')
a = p.parse_args()
capture = pathlib.Path(a.capture)
out = pathlib.Path.cwd() / 'target/evidence/time-rows'
out.mkdir(parents=True, exist_ok=True)


def argv_for(linker, prog, output):
    stashed = json.loads((capture / prog / 'link.json').read_text())['stashed']
    argv, i = [linker], 0
    while i < len(stashed):
        if stashed[i] == '-o':
            argv += ['-o', str(output)]
            i += 2
            continue
        argv.append(str(capture / prog / stashed[i][1:]) if stashed[i].startswith('@') else stashed[i])
        i += 1
    return argv


def child(argv, cap, env=None):
    started = time.monotonic()
    pid = os.fork()
    if pid == 0:
        try:
            resource.setrlimit(resource.RLIMIT_AS, (cap, cap))
            fd = os.open(str(out / 'child.stderr'), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)
            os.dup2(fd, 2)
            os.execve(argv[0], argv, env or dict(os.environ, LIGATURE_SYSROOT=a.sysroot))
        finally:
            os._exit(127)
    _, status, usage = os.wait4(pid, 0)
    return {'status': os.waitstatus_to_exitcode(status), 'wall': round(time.monotonic() - started, 3),
            'cpu': round(usage.ru_utime + usage.ru_stime, 3), 'resident_peak': usage.ru_maxrss * 1024,
            'stderr_tail': (out / 'child.stderr').read_bytes()[-300:].decode(errors='replace')}


def digest(path):
    with open(path, 'rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def sidecar(path):
    return pathlib.Path(str(path) + '.provenance')


def clear(path):
    for f in (path, sidecar(path)):
        if f.exists():
            f.unlink()


linkers = [('trunk', str(pathlib.Path(a.trunk).resolve()), 4 << 30),
           ('candidate', str(pathlib.Path(a.candidate).resolve()), 512 << 20)]
rows, failures = [], []
for rnd in range(a.rounds):
    for prog in PROGRAMS:
        for label, linker, cap in linkers:
            exe = out / f'{prog}.{label}'
            clear(exe)
            r = child(argv_for(linker, prog, exe), cap)
            r.update(round=rnd, program=prog, linker=label)
            if r['status'] == 0:
                first = digest(exe)
                r['sha256'] = first if first == digest(exe) else 'unstable'
                r['bytes'] = exe.stat().st_size
                if sidecar(exe).exists():
                    r['sidecar_sha256'] = digest(sidecar(exe))
                    r['sidecar_bytes'] = sidecar(exe).stat().st_size
                clear(exe)
            rows.append(r)
            print(f"time-rows round={rnd} {prog} {label} status={r['status']} cpu={r['cpu']} wall={r['wall']} "
                  f"resident_peak={r['resident_peak']} ({r['resident_peak'] / 2**20:.1f} MiB) "
                  f"bytes={r.get('bytes', '-')} sidecar={r.get('sidecar_bytes', '-')} sha256={r.get('sha256', '-')[:16]}",
                  flush=True)
# The candidate's embedded form, once per program, for identity with trunk's output; and lld's.
for prog in PROGRAMS:
    exe = out / f'{prog}.embedded'
    clear(exe)
    r = child(argv_for(str(pathlib.Path(a.candidate).resolve()), prog, exe) + ['-Wl,--provenance=embed'], 512 << 20)
    r.update(round='embedded', program=prog, linker='candidate-embedded')
    if r['status'] == 0:
        r['sha256'], r['bytes'] = digest(exe), exe.stat().st_size
        r['stray_sidecar'] = sidecar(exe).exists()
        clear(exe)
    rows.append(r)
    if a.lld_cc and a.lld:
        exe = out / f'{prog}.lld'
        clear(exe)
        env = dict(os.environ, PAX_LLD=a.lld, PAX_CC_SYSROOT=a.sysroot)
        r = child([a.lld_cc] + argv_for(a.lld_cc, prog, exe)[1:], 4 << 30, env)
        r.update(round='lld', program=prog, linker='lld')
        if r['status'] == 0:
            r['bytes'] = exe.stat().st_size
            clear(exe)
        rows.append(r)
(out / 'results.json').write_text(json.dumps(rows, indent=2) + '\n')
for prog in PROGRAMS:
    mine = [r for r in rows if r['program'] == prog and r['linker'] == 'candidate']
    theirs = [r for r in rows if r['program'] == prog and r['linker'] == 'trunk']
    bad = [r for r in mine if r['status'] != 0]
    if bad:
        print(f"FAIL time-{prog}: the candidate's link failed: {bad[0]['stderr_tail'].strip()[-200:]}", flush=True)
        failures.append('time-' + prog)
        continue
    best = min(r['cpu'] for r in mine)
    base = min((r['cpu'] for r in theirs if r['status'] == 0), default=None)
    detail = (f"fastest cpu {best:.3f} s of {len(mine)} (wall {min(r['wall'] for r in mine):.3f} s), "
              f"peak {max(r['resident_peak'] for r in mine) / 2**20:.1f} MiB; trunk {base} s")
    if prog == 'hello':
        print(f"NOTE time-hello: 1 s {'met' if best < 1.0 else 'not met'}: {detail}", flush=True)
    if best >= BOUND:
        print(f'FAIL time-{prog}: at or over {BOUND} s: {detail}', flush=True)
        failures.append('time-' + prog)
    else:
        print(f'PASS time-{prog}: under {BOUND} s: {detail}', flush=True)
split = {}
for prog in PROGRAMS:
    forms = {(r.get('sha256'), r.get('sidecar_sha256')) for r in rows
             if r['program'] == prog and r['linker'] == 'candidate'}
    if len(forms) != 1 or None in next(iter(forms)):
        split[prog] = sorted(map(str, forms))
if split:
    print(f'FAIL time-determinism: outputs or sidecars differ: {json.dumps(split)}', flush=True)
    failures.append('time-determinism')
else:
    print('PASS time-determinism: every candidate output and sidecar of each program is one file', flush=True)
moved = {}
for prog in PROGRAMS:
    trunk = {r.get('sha256') for r in rows if r['program'] == prog and r['linker'] == 'trunk'}
    embedded = [r for r in rows if r['program'] == prog and r['linker'] == 'candidate-embedded']
    if len(trunk) != 1 or None in trunk or [r.get('sha256') for r in embedded] != list(trunk) or \
            embedded[0].get('stray_sidecar', True):
        moved[prog] = {'trunk': sorted(map(str, trunk)), 'embedded': [r.get('sha256') for r in embedded]}
if moved:
    print(f'FAIL time-identity: the embedded form differs from trunk: {json.dumps(moved)}', flush=True)
    failures.append('time-identity')
else:
    print('PASS time-identity: the embedded form of each program is trunk\'s file: ' +
          ' '.join(f"{prog}={next(r['sha256'] for r in rows if r['program'] == prog and r['linker'] == 'trunk')[:12]}"
                   for prog in PROGRAMS), flush=True)
for prog in PROGRAMS:
    mine = next((r for r in rows if r['program'] == prog and r['linker'] == 'candidate' and r['status'] == 0), {})
    embedded = next((r for r in rows if r['program'] == prog and r['linker'] == 'candidate-embedded'), {})
    lld = next((r for r in rows if r['program'] == prog and r['linker'] == 'lld' and r['status'] == 0), {})
    ratio = f" ({mine['bytes'] / lld['bytes']:.3f}x lld's)" if mine.get('bytes') and lld.get('bytes') else ''
    print(f"NOTE size-{prog}: output {mine.get('bytes', '-')} bytes{ratio}, sidecar {mine.get('sidecar_bytes', '-')} bytes; "
          f"embedded {embedded.get('bytes', '-')} bytes; ld.lld {lld.get('bytes', '-')} bytes", flush=True)
if failures:
    print(f"time-rows: {len(failures)} row(s) failed: {' '.join(failures)}", flush=True)
    sys.exit(1)
print('time-rows: every row passed', flush=True)
