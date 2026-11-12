#!/usr/bin/env python3
"""Time rows: each captured link by trunk's linker and the candidate, interleaved, on one CPU.

Each link is the captured cc-shaped command, run as a direct child; its CPU time (user + sys) and
its own ru_maxrss come from wait4. Trunk runs under a 4 GiB address-space cap, the candidate under
the memory rows' 512 MiB. Rows, each PASS or FAIL <row>:
  time-NAME      the candidate's fastest CPU time of the rounds is under 2 s
  time-identity  every output of one program, by either linker in any round, is the same file
Hello's 1 s is reported against its number, not held as a row (the time it cannot go under is
the manifest's hashing; see the lane's note).
usage: time-rows.py --capture DIR --sysroot DIR [--rounds N] TRUNK CANDIDATE
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


def child(argv, cap):
    started = time.monotonic()
    pid = os.fork()
    if pid == 0:
        try:
            resource.setrlimit(resource.RLIMIT_AS, (cap, cap))
            fd = os.open(str(out / 'child.stderr'), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)
            os.dup2(fd, 2)
            os.execve(argv[0], argv, dict(os.environ, LIGATURE_SYSROOT=a.sysroot))
        finally:
            os._exit(127)
    _, status, usage = os.wait4(pid, 0)
    return {'status': os.waitstatus_to_exitcode(status), 'wall': round(time.monotonic() - started, 3),
            'cpu': round(usage.ru_utime + usage.ru_stime, 3), 'resident_peak': usage.ru_maxrss * 1024,
            'stderr_tail': (out / 'child.stderr').read_bytes()[-300:].decode(errors='replace')}


def digest(path):
    with open(path, 'rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


linkers = [('trunk', str(pathlib.Path(a.trunk).resolve()), 4 << 30),
           ('candidate', str(pathlib.Path(a.candidate).resolve()), 512 << 20)]
rows, digests, failures = [], {prog: set() for prog in PROGRAMS}, []
for rnd in range(a.rounds):
    for prog in PROGRAMS:
        for label, linker, cap in linkers:
            exe = out / f'{prog}.{label}'
            if exe.exists():
                exe.unlink()
            r = child(argv_for(linker, prog, exe), cap)
            r.update(round=rnd, program=prog, linker=label)
            if r['status'] == 0:
                h = [digest(exe), digest(exe)]
                r['sha256'] = h[0] if h[0] == h[1] else 'unstable'
                digests[prog].add(r['sha256'])
                exe.unlink()
            rows.append(r)
            print(f"time-rows round={rnd} {prog} {label} status={r['status']} cpu={r['cpu']} wall={r['wall']} "
                  f"resident_peak={r['resident_peak']} ({r['resident_peak'] / 2**20:.1f} MiB) "
                  f"sha256={r.get('sha256', '-')}", flush=True)
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
split = {prog: sorted(d) for prog, d in digests.items() if len(d) != 1}
if split:
    print(f'FAIL time-identity: outputs differ: {json.dumps(split)}', flush=True)
    failures.append('time-identity')
else:
    print('PASS time-identity: every output of each program is one file: ' +
          ' '.join(f'{prog}={next(iter(d))[:12]}' for prog, d in digests.items()), flush=True)
if failures:
    print(f"time-rows: {len(failures)} row(s) failed: {' '.join(failures)}", flush=True)
    sys.exit(1)
print('time-rows: every row passed', flush=True)
