#!/usr/bin/env python3
"""Memory rows: one static link's resident peak, measured on the linker process itself.

Each row runs ligature as a direct child under its own address-space cap (RLIMIT_AS on Linux;
on macOS, where RLIMIT_AS is not enforced, a resident-set watchdog kills the child at the cap).
The resident peak is the child's own ru_maxrss from wait4, never the harness's (VmHWM on Linux).
The cap sits below the peak the unbounded linker reached (7.2-7.4 GiB of address space for hello
against the 46.7 MB musl runtime), so a linker that keeps that footprint aborts under it.

Rows, each reported as PASS or FAIL <row>:
  link-memory-hello    hello's link: exit 0 under the cap, resident peak under the bound
  link-memory-str      the str program's link, likewise
  link-memory-verify   `ligature verify` of hello's output, likewise
  link-memory-scaling  synthetic archives of N, 10N and 100N members: the peak and the time
                       above a one-member link grow at most linearly (each 10x step within 15x)
With --baseline PATH, every output is also linked by that linker under the same inputs and
compared byte for byte (link-identity-<case>). Objects come from LIGATURE_MEMORY_OBJECTS
(DIR/hello/main.o, DIR/str/main.o) or are compiled by the pinned compiler.
"""
import argparse
import hashlib
import json
import os
import pathlib
import platform
import resource
import shutil
import signal
import subprocess
import sys
import threading
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / 'target/evidence/link-memory'
BUNDLE = ROOT / '.link-inputs'
WOLF = pathlib.Path(os.environ.get('WOLF', str(ROOT / '.wolf-bin/wolf')))
GIB = 1 << 30
MIB = 1 << 20
LINUX = platform.system() == 'Linux'
# The bound each row's resident peak must stay under, and the cap the run is held to.
BOUND = {'hello': 1 * GIB, 'str': 1 * GIB, 'verify': 1 * GIB}
CAP = 2 * GIB
SOURCES = {'hello': ROOT / 'tests/corpus/hello/hello.lu', 'str': ROOT / 'tests/corpus/str/str.lu'}
EXPECTED = {'hello': b'hello, wolf\n', 'str': b'hello, wolfhello, wolf\n'}
failures = []


def digest(path):
    with open(path, 'rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def status_field(pid, key):
    try:
        with open(f'/proc/{pid}/status') as stream:
            for line in stream:
                if line.startswith(key):
                    return int(line.split()[1]) * 1024
    except (OSError, ValueError, IndexError):
        pass
    return None


def darwin_rss(pid):
    p = subprocess.run(['ps', '-o', 'rss=', '-p', str(pid)], capture_output=True, text=True)
    text = p.stdout.strip()
    return int(text) * 1024 if text.isdigit() else None


def measured(argv, cap, env=None, timeout=1800):
    """Run argv as a direct child under cap; return status, seconds, peaks and output."""
    def limit():
        if LINUX:
            resource.setrlimit(resource.RLIMIT_AS, (cap, cap))
    started = time.monotonic()
    child = subprocess.Popen([str(a) for a in argv], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             preexec_fn=limit, env=env)
    samples = {'vmpeak': 0, 'rss': 0, 'killed': False}
    done = threading.Event()

    def sample():
        while not done.is_set():
            if LINUX:
                peak = status_field(child.pid, 'VmPeak:')
                if peak:
                    samples['vmpeak'] = max(samples['vmpeak'], peak)
            else:
                rss = darwin_rss(child.pid)
                if rss:
                    samples['rss'] = max(samples['rss'], rss)
                    if rss > cap and not samples['killed']:
                        samples['killed'] = True
                        os.kill(child.pid, signal.SIGKILL)
            done.wait(0.05)
    out = {}

    def drain(name, stream):
        out[name] = stream.read()
    readers = [threading.Thread(target=drain, args=(n, s)) for n, s in (('stdout', child.stdout), ('stderr', child.stderr))]
    sampler = threading.Thread(target=sample)
    for t in readers + [sampler]:
        t.start()
    timer = threading.Timer(timeout, lambda: os.kill(child.pid, signal.SIGKILL))
    timer.start()
    _, wstatus, usage = os.wait4(child.pid, 0)
    timer.cancel()
    seconds = time.monotonic() - started
    done.set()
    for t in readers + [sampler]:
        t.join()
    child.returncode = os.waitstatus_to_exitcode(wstatus)
    # ru_maxrss is KiB on Linux and bytes on macOS.
    hwm = usage.ru_maxrss * (1024 if LINUX else 1)
    return {'argv': [str(a) for a in argv], 'status': child.returncode, 'seconds': round(seconds, 3),
            'resident_peak': hwm, 'address_space_peak_sampled': samples['vmpeak'] or None,
            'cap': cap, 'watchdog_killed': samples['killed'],
            'stderr_tail': out['stderr'][-600:].decode(errors='replace'), 'stdout': out['stdout']}


def objects():
    given = os.environ.get('LIGATURE_MEMORY_OBJECTS')
    found = {}
    for case, source in SOURCES.items():
        if given:
            found[case] = pathlib.Path(given) / case / 'main.o'
        else:
            target = OUT / case / 'main.o'
            target.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run([str(WOLF), 'build', '--no-cache', '--emit=obj', str(source), '-o', str(target)], check=True, timeout=600)
            found[case] = target
        assert found[case].is_file(), f'missing object {found[case]}'
    return found


def link_argv(linker, obj, output):
    # The released compiler's cc-shaped --linker line (the line in ligature#32).
    return [linker, '-o', output, obj, BUNDLE / 'libwolf_rt.a', '-lpthread', '-ldl', '-lm', '-Wl,--gc-sections']


def record(row, result, bound=None):
    result = dict(result)
    result.pop('stdout', None)
    result['row'] = row
    result['bound'] = bound
    rows.append(result)
    (OUT / 'results.json').write_text(json.dumps(rows, indent=2) + '\n')


def fail(row, message):
    print(f'FAIL {row}: {message}', flush=True)
    failures.append(row)


def check_peak(row, result, bound):
    gib = result['resident_peak'] / GIB
    detail = (f"status={result['status']} resident_peak={result['resident_peak']} ({gib:.3f} GiB) "
              f"bound={bound} cap={result['cap']} seconds={result['seconds']}")
    if result['status'] != 0:
        fail(row, f'link did not finish under the cap: {detail}; {result["stderr_tail"].strip()[-200:]}')
        return False
    if result['resident_peak'] >= bound:
        fail(row, f'resident peak at or over the bound: {detail}')
        return False
    print(f'PASS {row}: {detail}', flush=True)
    return True


def program(case, linker, obj, env):
    exe = OUT / case / 'program'
    exe.parent.mkdir(parents=True, exist_ok=True)
    if exe.exists():
        exe.unlink()
    row = 'link-memory-' + case
    result = measured(link_argv(linker, obj, exe), CAP, env)
    record(row, result, BOUND[case])
    within = check_peak(row, result, BOUND[case])
    if result['status'] != 0:
        return None
    if LINUX:
        ran = subprocess.run([str(exe)], capture_output=True, timeout=60)
        if (ran.returncode, ran.stdout, ran.stderr) != (0, EXPECTED[case], b''):
            fail(row, f'linked program output {ran.returncode} {ran.stdout!r} {ran.stderr!r}')
            return None
        print(f'  {case}: executed, stdout {EXPECTED[case]!r}', flush=True)
    else:
        print(f'  {case}: not executed on {platform.system()} (x86-64 Linux ELF)', flush=True)
    # A linked output over the bound is still verified and compared: its row has already failed.
    return exe if within or result['status'] == 0 else None


def assemble(source, output):
    source.write_text(source.read_text() + '\n.section .note.GNU-stack,"",@progbits\n')
    if shutil.which('as') and LINUX:
        command = ['as', '--64', str(source), '-o', str(output)]
    else:
        command = ['clang', '-target', 'x86_64-unknown-linux-gnu', '-c', str(source), '-o', str(output)]
    subprocess.run(command, check=True, capture_output=True, timeout=120)


def synthetic(linker, members, root):
    """An entry object calling every member's function, and an archive of the members."""
    root.mkdir(parents=True, exist_ok=True)
    objects = []
    for i in range(members):
        s = root / f'm{i}.s'
        s.write_text(f'.section .text.f{i},"ax",@progbits\n.global f{i}\nf{i}: lea d{i}(%rip),%rax\n'
                     f' mov (%rax),%eax\n ret\n.fill 192,1,0x90\n'
                     f'.section .data.d{i},"aw",@progbits\n.global d{i}\nd{i}: .quad f{i}\n'
                     f'.section .text.dead{i},"ax",@progbits\ndead{i}: call f{i}\n ret\n.fill 64,1,0x90\n')
        o = root / f'm{i}.o'
        assemble(s, o)
        objects.append(o)
    archive = root / 'libsynthetic.a'
    subprocess.run([str(linker), 'archive', str(archive), *map(str, objects)], check=True, capture_output=True, timeout=600)
    entry = root / 'entry.s'
    calls = ''.join(f' call f{i}\n' for i in range(members))
    entry.write_text(f'.text\n.global _start\n_start:\n{calls} mov $60,%eax\n xor %edi,%edi\n syscall\n')
    entry_o = root / 'entry.o'
    assemble(entry, entry_o)
    for o in objects:
        o.unlink()
        o.with_suffix('.s').unlink()
    return entry_o, archive


def scaling(linker, base):
    row = 'link-memory-scaling'
    sizes = [1, base, base * 10, base * 100]
    points = []
    for members in sizes:
        entry, archive = synthetic(linker, members, OUT / 'scaling' / str(members))
        exe = OUT / 'scaling' / str(members) / 'program'
        best = None
        for _ in range(2):
            result = measured([linker, '-static', '-nostdlib', '--gc-sections', '-o', exe, entry, archive], CAP)
            if result['status'] != 0:
                record(row, result)
                fail(row, f'synthetic link of {members} members failed: {result["stderr_tail"].strip()[-200:]}')
                return
            best = result if best is None or result['seconds'] < best['seconds'] else best
        point = {'members': members, 'archive_bytes': archive.stat().st_size,
                 'resident_peak': best['resident_peak'], 'seconds': best['seconds']}
        points.append(point)
        print(f"  scaling members={members} archive_bytes={point['archive_bytes']} "
              f"resident_peak={point['resident_peak']} seconds={point['seconds']}", flush=True)
    rows.append({'row': row, 'points': points})
    (OUT / 'results.json').write_text(json.dumps(rows, indent=2) + '\n')
    floor = points[0]
    worst = []
    for a, b in zip(points[1:], points[2:]):
        for key in ('resident_peak', 'seconds'):
            low = max(a[key] - floor[key], 1e-3 if key == 'seconds' else MIB)
            high = b[key] - floor[key]
            worst.append((high / low, key, a['members'], b['members']))
    ratio, key, small, large = max(worst)
    detail = f'worst 10x step {small}->{large} members: {key} above one member grew {ratio:.2f}x (bound 15x)'
    if ratio > 15:
        fail(row, 'superlinear growth: ' + detail)
    else:
        print(f'PASS {row}: {detail}', flush=True)


def identity(case, candidate_exe, baseline, obj, env):
    row = 'link-identity-' + case
    exe = OUT / case / 'baseline-program'
    result = measured(link_argv(baseline, obj, exe), 12 * GIB if LINUX else CAP, env)
    record(row, result)
    if result['status'] != 0:
        fail(row, f'baseline link failed: status {result["status"]}')
        return
    a = [digest(candidate_exe), digest(candidate_exe)]
    b = [digest(exe), digest(exe)]
    if len(set(a + b)) != 1:
        fail(row, f'candidate {a[0]} differs from baseline {b[0]}')
        return
    print(f'PASS {row}: byte-identical to the baseline linker, sha256 {a[0]} (read twice each)', flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--linker', default=str(ROOT / 'target/ligature'))
    parser.add_argument('--baseline', help='a second linker whose outputs must be byte-identical')
    parser.add_argument('--scale', type=int, default=40, help='N for the N/10N/100N scaling row')
    parser.add_argument('--rows', default='hello,str,verify,scaling')
    parser.add_argument('--verify-input', help='verify this executable instead of the hello row output')
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    wanted = args.rows.split(',')
    linker = pathlib.Path(args.linker).resolve()
    env = dict(os.environ, LIGATURE_SYSROOT=str(BUNDLE / 'sysroot'))
    found = objects() if {'hello', 'str', 'verify'} & set(wanted) else {}
    outputs = {}
    for case in ('hello', 'str'):
        if case in wanted or (case == 'hello' and 'verify' in wanted):
            outputs[case] = program(case, linker, found[case], env)
    if 'verify' in wanted:
        row = 'link-memory-verify'
        target = pathlib.Path(args.verify_input) if args.verify_input else outputs.get('hello')
        if target is None:
            fail(row, 'no hello output to verify')
        else:
            result = measured([linker, 'verify', target], CAP)
            record(row, result, BOUND['verify'])
            check_peak(row, result, BOUND['verify'])
    if 'scaling' in wanted:
        scaling(linker, args.scale)
    if args.baseline:
        for case, exe in outputs.items():
            if exe is not None:
                identity(case, exe, pathlib.Path(args.baseline).resolve(), found[case], env)
    if failures:
        print(f'link-memory: {len(failures)} row(s) failed: {" ".join(failures)}', flush=True)
        sys.exit(1)
    print('link-memory: every row passed; 0 SKIP', flush=True)


rows = []
if __name__ == '__main__':
    main()
