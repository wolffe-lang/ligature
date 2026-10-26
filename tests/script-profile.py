#!/usr/bin/env python3
"""Closed script boundary: no acceptance is a kernel-link capability claim."""
import json, pathlib, re, subprocess
ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / 'target/evidence/script-profile'
OUT.mkdir(parents=True, exist_ok=True)
BIN = ROOT / 'target/ligature'
source = (ROOT / 'tests/fixtures/pax-kernel.ld').read_text()
plain = re.sub(r'/\*.*?\*/', ' ', source, flags=re.S)
rows = []
def check(name, text, accepted=False, reason='script:'):
    path = OUT / (name + '.ld')
    path.write_text(text)
    run = subprocess.run([BIN, 'script-plan', path], capture_output=True, timeout=30)
    assert run.returncode == (0 if accepted else 1), (name, run.returncode, run.stderr)
    if accepted:
        value = json.loads(run.stdout)
        assert value == {'format':'ligature.script-profile.v1','profile':'pax-kernel','linking':False,'base':0xffffffff80000000,'entry':'_start','load_flags':[5,4,6],'alignment':4096}, value
    else:
        assert reason.encode() in run.stderr, (name, run.stderr)
        assert not run.stdout, (name, run.stdout)
    rows.append({'name':name,'status':run.returncode,'stderr':run.stderr.decode()})
check('original', source, True)
check('no-comments', plain, True)
check('whitespace', re.sub(r'\s+', '\r\n\t', plain), True)
check('comment-boundary', plain.replace('ENTRY(', 'ENTRY/* boundary */('), True)
for name, old, new in [
    ('format','elf64-x86-64','elf64-littleaarch64'),('entry','ENTRY(_start)','ENTRY(other)'),
    ('missing-entry','ENTRY(_start)',''),('duplicate-entry','ENTRY(_start)','ENTRY(_start) ENTRY(_start)'),
    ('phdr-type','PT_LOAD','PT_TLS'),('phdr-flags','FLAGS(5)','FLAGS(7)'),
    ('phdr-reference',':rodata',':text'),('base','0xffffffff80000000','0x10000000000000000'),
    ('arithmetic','0xffffffff80000000','0xffffffff80000000 + 4096'),
    ('alignment','ALIGN(0x1000)','ALIGN(3)'),('symbol','__pax_text_end','__other'),
    ('wildcard','.text.*','.text?'),('common','*(COMMON)',''),('order','*(.data.limine)',''),
    ('discard','*(.eh_frame)','*(.debug_info)'),('memory','PHDRS','MEMORY'),
    ('overlay','SECTIONS','OVERLAY'),('include','OUTPUT_FORMAT','INCLUDE'),
    ('literal-split','ENTRY','ENT/* split */RY'),('unicode','_start','_stárt'),
]:
    check(name, plain.replace(old,new,1))
check('trailing', plain + ' ENTRY(_start)')
check('unclosed-comment', plain + ' /*', reason='unterminated comment')
check('nul', plain + '\0', reason='control byte')
check('too-large', ' ' * 65537, reason='65536-byte')
for operands in ([], ['one', 'two']):
    run = subprocess.run([BIN, 'script-plan', *operands], capture_output=True, timeout=30)
    assert run.returncode == 1 and b'script-plan: usage:' in run.stderr, (operands, run.stderr)
    rows.append({'name':'arity-' + str(len(operands)), 'status':run.returncode, 'stderr':run.stderr.decode()})
plan = subprocess.run([BIN, '--print-plan', '-nostdlib', '-T', '/missing-profile.ld', '/missing-object.o'], capture_output=True, timeout=30)
assert plan.returncode == 0 and json.loads(plan.stdout)['script'] == '/missing-profile.ld', plan.stderr
rows.append({'name':'declarative-plan-opens-no-input', 'status':plan.returncode, 'stderr':plan.stderr.decode()})
(OUT / 'results.json').write_text(json.dumps(rows,indent=2)+'\n')
print(f'script-profile: {len(rows)} rows, 0 SKIP; preflight only; executable kernel links require explicit -T')
