#!/usr/bin/env python3
"""Exact error payload bytes for region boundaries; independent ELF/ar inputs.

Unlike the existing substring rows, these hold complete stderr, status, stdout
and untouched output/sidecar bytes. --bin can replay the same fixtures with a
historical linker without turning its potentially freed message into a golden.
"""
import argparse
import json
import os
from pathlib import Path
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'target/evidence/region-payload'


def header(machine=62, kind=1):
    return bytearray(b'\x7fELF\x02\x01\x01' + bytes(9) + struct.pack('<HHIQQQIHHHHHH', kind, machine, 1, 0, 0, 0, 0, 64, 0, 0, 64, 0, 0))


def object_bytes(machine=62, relocation=None, value=0, addend=0, offset=0, kind=1):
    names = b'\0.text\0.rela.text\0.symtab\0.strtab\0.shstrtab\0'
    labels = b'\0_start\0target\0'
    code = b'\xb8\x3c\x00\x00\x00\x31\xff\x0f\x05' if relocation is None else bytes(24)
    symbols = bytes(24) + struct.pack('<IBBHQQ', 1, 0x12, 0, 1, 0, len(code)) + struct.pack('<IBBHQQ', 8, 0x11, 0, 65521, value, 0)
    rela = b'' if relocation is None else struct.pack('<QQq', offset, (2 << 32) | relocation, addend)
    bodies = [b'', code, rela, symbols, labels, names]
    data, sections = header(machine, kind), [bytes(64)]
    for i in range(1, 6):
        data.extend(bytes(-len(data) % 8))
        at = len(data)
        data.extend(bodies[i])
        label = [b'', b'.text', b'.rela.text', b'.symtab', b'.strtab', b'.shstrtab'][i]
        sections.append(struct.pack('<IIQQQQIIQQ', names.index(label), [0, 1, 4, 2, 3, 3][i], 6 if i == 1 else 0, 0,
                                    at, len(bodies[i]), 3 if i == 2 else 4 if i == 3 else 0,
                                    1 if i in (2, 3) else 0, 8 if i in (1, 2, 3) else 1, 24 if i in (2, 3) else 0))
    data.extend(bytes(-len(data) % 8))
    shoff = len(data)
    data.extend(b''.join(sections))
    struct.pack_into('<Q', data, 40, shoff)
    struct.pack_into('<HH', data, 60, 6, 5)
    return bytes(data)


def archive(body):
    name = 'member.o/'
    head = f'{name:<16}{0:<12}{0:<6}{0:<6}{0:<8}{len(body):<10}`\n'.encode()
    assert len(head) == 60
    return b'!<arch>\n' + head + body + (b'\n' if len(body) % 2 else b'')


def fixtures():
    root = OUT / 'fixtures'
    root.mkdir(parents=True, exist_ok=True)
    rows = []

    def row(name, data, command, message):
        path = root / name
        path.write_bytes(data)
        relative = path.relative_to(ROOT).as_posix()
        rows.append(dict(name=name, argv=command(relative), stderr=f'ligature: {message(relative)}\n'))

    read = lambda p: ['roundtrip', p]
    link = lambda p: ['-nostdlib', '-o', 'target/evidence/region-payload/output', p]
    row('read-x86.o', object_bytes(relocation=999999), read, lambda _: 'unknown x86-64 relocation 999999 (AMD64 psABI 1.0 section 4.4)')
    row('read-arm.o', object_bytes(machine=183, relocation=313), read, lambda _: 'unsupported AArch64 relocation 313 (AAELF64 2025Q1 section 6)')
    row('archive-reloc.a', archive(object_bytes(relocation=999999)), read, lambda _: 'unknown x86-64 relocation 999999 (AMD64 psABI 1.0 section 4.4)')
    row('archive-machine.a', archive(header(machine=3)), read, lambda _: 'unsupported e_machine 3 (gABI ch.4)')
    row('write-x86.o', object_bytes(relocation=12), link, lambda _: 'unsupported R_X86_64 relocation 12 (AMD64 psABI table 4.9)')
    row('write-arm.o', object_bytes(machine=183, relocation=541), link, lambda _: 'unsupported AArch64 relocation 541 (AAELF64 2025Q1 section 6)')
    row('resolve-exec.o', object_bytes(kind=2), link, lambda p: f'{p}: static writer requires ET_REL')
    row('no-index.a', archive(object_bytes()), link, lambda p: f'{p}: missing archive symbol index (SysV ar)')
    row('overflow.o', object_bytes(relocation=11, value=0x80000000), link, lambda p: f'relocation overflow at {p}:.text+0 type 11: 2147483648 does not fit 32 bits (AMD64 psABI table 4.9)')
    row('tls.o', object_bytes(relocation=19, offset=4), link, lambda p: f'unsupported TLS addend at {p}:.text+4 type 19 (psABI 4.5)')
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--bin', type=Path, default=ROOT / 'target/ligature')
    parser.add_argument('--label', default='pin')
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    rows = fixtures()
    if args.self_test:
        assert len(rows) == 10 and len({r['name'] for r in rows}) == 10
        assert all(r['stderr'].startswith('ligature: ') and r['stderr'].endswith('\n') for r in rows)
        assert object_bytes().startswith(b'\x7fELF') and archive(header()).startswith(b'!<arch>\n')
        print('PASS region-payload-fixtures: ten exact diagnostics, independent ELF/ar encoding')
        return 0
    binary = args.bin.resolve()
    if not binary.is_file():
        print('FAIL region-payload-inputs: real linker required')
        return 1
    home = OUT / 'home'
    home.mkdir(exist_ok=True)
    env = dict(os.environ, SHELL='/bin/sh', HOME=str(home), LC_ALL='C')
    output = OUT / 'output'
    side = OUT / 'output.provenance'
    results, failed = [], 0
    for row in rows:
        output.write_bytes(b'untouched output')
        side.write_bytes(b'untouched sidecar')
        q = subprocess.run([str(binary), *row['argv']], cwd=ROOT, env=env, capture_output=True, timeout=60)
        ok = (q.returncode, q.stdout, q.stderr, output.read_bytes(), side.read_bytes()) == (
            1, b'', row['stderr'].encode(), b'untouched output', b'untouched sidecar')
        print(('PASS ' if ok else 'FAIL ') + f'region-payload-{args.label}-{row["name"]}', flush=True)
        results.append(dict(name=row['name'], status=q.returncode, stdout_hex=q.stdout.hex(),
                            stderr_hex=q.stderr.hex(), expected_stderr_hex=row['stderr'].encode().hex(), ok=ok))
        failed += not ok
    (OUT / f'{args.label}.json').write_text(json.dumps(results, indent=2) + '\n')
    return int(bool(failed))


if __name__ == '__main__':
    sys.exit(main())
