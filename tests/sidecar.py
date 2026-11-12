#!/usr/bin/env python3
"""The provenance sidecar: where a default link puts its manifest and retained relocations.

Rows, each PASS or FAIL <row>: (each fails by name when the two links every row reads fail):
  sidecar-default      a default link writes OUTPUT and OUTPUT.provenance; the output keeps the
                       116-byte note (flags 1, the sidecar's size and digest) and no manifest or
                       SHT_RELA section; every head, record and digest checks independently; the
                       program runs and `ligature verify` passes
  sidecar-embedded     `--provenance=embed` (and `-Wl,--provenance=embed`) writes the embedded form
                       and removes a stale sidecar; its retained tables and patch rows are the
                       sidecar's, byte for byte, and its metadata differs only in what describes the
                       output file itself (output, ranges, sections)
  sidecar-determinism  two links of each form are the same files
  sidecar-option       an unknown --provenance value is refused by name
  sidecar-inspect      inspect shows the sidecar's retained relocations as the embedded form's
  sidecar-explain      explain answers from the sidecar, and refuses when it is missing
  sidecar-refusals     verify refuses, by name: a missing sidecar, an altered sidecar, another
                       output's sidecar, an altered output, and (with both digests resealed) a
                       sidecar naming another output, a misplaced table, an entry's symbol outside
                       the symbol table, and a manifest one patch row short
"""
import hashlib
import json
import os
import pathlib
import runpy
import struct
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
BIN = ROOT / 'target/ligature'
OUT = ROOT / 'target/evidence/sidecar'
OUT.mkdir(parents=True, exist_ok=True)
files = runpy.run_path(str(ROOT / 'tests/provenance-files.py'))
codec = runpy.run_path(str(ROOT / 'tests/manifest-codec.py'))
ENV = dict(os.environ, LIGATURE_SYSROOT='/usr/lib/x86_64-linux-musl')
failures = []


def run(args, status=0, reason=None):
    p = subprocess.run(list(map(str, args)), capture_output=True, env=ENV, timeout=300)
    assert p.returncode == status, (args, p.returncode, p.stderr[-600:])
    if reason:
        assert reason.encode() in p.stderr, (args, reason, p.stderr[-600:])
    return p


def row(name, check):
    try:
        if setup_error is not None:
            raise AssertionError('the two links every row reads failed', setup_error)
        detail = check()
    except AssertionError as error:
        print(f'FAIL {name}: {error!r}'[:1200], flush=True)
        failures.append(name)
        return
    print(f'PASS {name}: {detail}', flush=True)


source = OUT / 'hello.c'
source.write_text('#include <stdio.h>\nstatic const char *message = "sidecar";\n'
                  'int main(void){puts(message);return 0;}\n')
obj = OUT / 'hello.o'
run(['musl-gcc', '-g', '-ffunction-sections', '-fdata-sections', '-c', source, '-o', obj])
other_source = OUT / 'other.c'
other_source.write_text('#include <stdio.h>\nint main(void){puts("another output, another sidecar");return 3;}\n')
other_obj = OUT / 'other.o'
run(['musl-gcc', '-c', other_source, '-o', other_obj])


def link(output, *extra, objects=(obj,)):
    run([BIN, '-o', output, *objects, '-lpthread', '-ldl', '-lm', '-Wl,--gc-sections', *extra])
    return output


default, embedded = OUT / 'default', OUT / 'embedded'
try:
    link(default)
    link(embedded, '-Wl,--provenance=embed')
    prov = files['load'](default)
    eprov = files['load'](embedded)
    setup_error = None
except (AssertionError, OSError, KeyError) as error:
    setup_error = error


def default_row():
    data, note, side = prov['data'], prov['note'], prov['side']
    assert prov['mode'] == 'sidecar' and files['sidecar'](default).exists()
    assert '.wolf.link.manifest' not in prov['sections']
    assert all(h[1] != 4 for h in prov['headers']), 'a retained table left in the output'
    assert struct.unpack_from('<III', note) == (5, 96, 1) and note[12:20] == b'WOLF' + bytes(4)
    version, flags, total, size = struct.unpack_from('<IIQQ', note, 20)
    assert (version, flags, total, size) == (1, 1, len(data), len(side))
    assert struct.unpack_from('<Q', note, 108)[0] == 0
    assert hashlib.sha256(side).digest() == note[44:76]
    zeroed = bytearray(data)
    n = prov['note_offset']
    zeroed[n + 44:n + 108] = bytes(64)
    assert hashlib.sha256(zeroed).digest() == note[76:108]
    magic, output_bytes, count, offset, msize = struct.unpack_from('<8sQQQQ', side, 0)
    assert magic == b'WLPROV01' and output_bytes == len(data) and offset + msize == len(side)
    at = 40 + 32 * count
    for t in range(count):
        info, link_index, entries_at, entries = struct.unpack_from('<QQQQ', side, 40 + 32 * t)
        assert entries_at == at and 0 < info < len(prov['headers']) and prov['headers'][link_index][1] == 2
        at += 24 * entries
    assert at == offset, (at, offset)
    doc = codec['decode'](prov['manifest'])
    assert codec['encode'](doc) == prov['manifest']
    assert doc['output']['bytes'] == len(data)
    assert len(doc['patches']) == sum(len(t['entries']) // 24 for t in prov['tables']) > 0
    cursor = 0
    for r in doc['ranges']:
        assert r['start'] == cursor and r['end'] > cursor
        cursor = r['end']
    assert cursor == len(data)
    assert run([default]).stdout == b'sidecar\n'
    run([BIN, 'verify', default])
    return (f'output {len(data)} bytes, sidecar {len(side)} bytes ({count} retained tables, '
            f'{len(doc["patches"])} patch rows, manifest {msize} bytes)')


def embedded_row():
    assert eprov['mode'] == 'embedded' and not files['sidecar'](embedded).exists()
    run([BIN, 'verify', embedded])
    top = link(OUT / 'top-level', '--provenance=embed')
    assert top.read_bytes() == embedded.read_bytes()
    stale = OUT / 'stale'
    link(stale)
    assert files['sidecar'](stale).exists()
    link(stale, '-Wl,--provenance=embed')
    assert not files['sidecar'](stale).exists(), 'an embedded link left a stale sidecar'
    assert [(t['info'], t['link'], t['entries']) for t in eprov['tables']] == \
        [(t['info'], t['link'], t['entries']) for t in prov['tables']]
    a, b = codec['decode'](eprov['manifest']), codec['decode'](prov['manifest'])
    assert a['patches'] == b['patches']
    moved = {k for k in a.keys() | b.keys() if a.get(k) != b.get(k)}
    assert moved <= {'output', 'ranges', 'sections'}, moved
    for name, h in prov['sections'].items():
        if h[1] != 8 and (h[2] & 2 or name in ('.symtab', '.strtab')):
            e = eprov['sections'][name]
            assert prov['data'][h[4]:h[4] + h[5]] == eprov['data'][e[4]:e[4] + e[5]], name
    return (f'embedded {len(eprov["data"])} bytes against {len(prov["data"])} + sidecar '
            f'{len(prov["side"])}; tables and patch rows identical, metadata moved in {sorted(moved)}')


def determinism_row():
    again = link(OUT / 'default-again')
    assert files['same_files'](again, default)
    again = link(OUT / 'embedded-again', '-Wl,--provenance=embed')
    assert files['same_files'](again, embedded)
    return 'two links of each form are the same output and the same sidecar'


def option_row():
    run([BIN, '-o', OUT / 'refused', obj, '-Wl,--provenance=elsewhere'], 1, '--provenance must be sidecar or embed')
    run([BIN, '-o', OUT / 'refused', obj, '--provenance='], 1, '--provenance must be sidecar or embed')
    plan = json.loads(run([BIN, '--print-plan', '-o', 'x', 'x.o', '-Wl,--provenance=embed']).stdout)
    assert plan['provenance'] == 'embed'
    assert json.loads(run([BIN, '--print-plan', '-o', 'x', 'x.o']).stdout)['provenance'] == 'sidecar'
    return 'unknown values refused by name; the plan names the mode'


def rela_rows(path):
    rows = [json.loads(x) for x in run([BIN, 'inspect', path]).stdout.splitlines()]
    count = sum(1 for r in rows if r['row'] == 'section')
    return count, sorted((r['target'], r['offset'], r['symbol'], r['type'], r['addend_bits'])
                         for r in rows if r['row'] == 'rela'), [r['table'] for r in rows if r['row'] == 'rela']


def inspect_row():
    count, side_rows, tables = rela_rows(default)
    _, embedded_rows, _ = rela_rows(embedded)
    assert side_rows and side_rows == embedded_rows
    assert min(tables) >= count, 'sidecar tables numbered inside the section table'
    return f'{len(side_rows)} retained relocations, the embedded form\'s, numbered from {count}'


def explain_row():
    a = json.loads(run([BIN, 'explain', default, '--symbol', 'main']).stdout)
    b = json.loads(run([BIN, 'explain', embedded, '--symbol', 'main']).stdout)
    assert a and [x['name'] for x in a] == [x['name'] for x in b] == ['main']
    lone = OUT / 'lone'
    lone.write_bytes(default.read_bytes())
    if files['sidecar'](lone).exists():
        files['sidecar'](lone).unlink()
    run([BIN, 'explain', lone, '--symbol', 'main'], 2)
    return 'explain answers main from the sidecar; without it, refused'


def refusals_row():
    names = []

    def refused(label, reason, data=None, side=None, manifest=None, reseal=False, sidecar_from=None):
        path = files['write'](prov, OUT / label, data=data, side=side, manifest=manifest, reseal=reseal)
        if sidecar_from is not None:
            files['sidecar'](path).write_bytes(files['sidecar'](sidecar_from).read_bytes())
        run([BIN, 'verify', path], 1, reason)
        names.append(label)

    path = OUT / 'missing-sidecar'
    path.write_bytes(prov['data'])
    if files['sidecar'](path).exists():
        files['sidecar'](path).unlink()
    run([BIN, 'verify', path], 1, 'missing provenance sidecar')
    names.append('missing-sidecar')
    side = bytearray(prov['side'])
    side[prov['manifest_offset'] + 50] ^= 1
    refused('altered-sidecar', 'provenance sidecar digest mismatch', side=side)
    other = link(OUT / 'other', objects=(other_obj,))
    refused('other-sidecar', 'provenance sidecar', sidecar_from=other)
    data = bytearray(prov['data'])
    data[prov['sections']['.text'][4]] ^= 1
    refused('altered-output', 'provenance output digest mismatch', data=data)
    side = bytearray(prov['side'])
    struct.pack_into('<Q', side, 8, len(prov['data']) + 1)
    refused('names-another-output', 'provenance sidecar names another output', side=side, reseal=True)
    side = bytearray(prov['side'])
    struct.pack_into('<Q', side, 40 + 16, struct.unpack_from('<Q', side, 40 + 16)[0] + 24)
    refused('misplaced-table', 'provenance sidecar layout', side=side, reseal=True)
    side = bytearray(prov['side'])
    first = struct.unpack_from('<Q', side, 40 + 16)[0]
    struct.pack_into('<Q', side, first + 8, (0xffffff << 32) | (struct.unpack_from('<Q', side, first + 8)[0] & 0xffffffff))
    refused('symbol-outside', 'RELA symbol index outside symbol table', side=side, reseal=True)
    doc = codec['decode'](prov['manifest'])
    doc['patches'].pop()
    refused('patch-row-short', 'provenance retained patch count mismatch',
            manifest=codec['encode'](doc, prov['manifest_size']), reseal=True)
    return f'{len(names)} refusals by name: {", ".join(names)}'


row('sidecar-default', default_row)
row('sidecar-embedded', embedded_row)
row('sidecar-determinism', determinism_row)
row('sidecar-option', option_row)
row('sidecar-inspect', inspect_row)
row('sidecar-explain', explain_row)
row('sidecar-refusals', refusals_row)
(OUT / 'results.json').write_text(json.dumps({
    'output_bytes': None if setup_error else len(prov['data']),
    'sidecar_bytes': None if setup_error or prov['side'] is None else len(prov['side']),
    'embedded_bytes': None if setup_error else len(eprov['data']), 'failures': failures}, indent=2) + '\n')
if failures:
    print(f'sidecar: {len(failures)} row(s) failed: {" ".join(failures)}', flush=True)
    sys.exit(1)
print('sidecar: every row passed; 0 SKIP', flush=True)
