#!/usr/bin/env python3
"""PC32 is S+A-P, not S+A-P+4; independently decode the data-site equation."""
import pathlib
import struct
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / 'target/evidence/pc32'
OUT.mkdir(parents=True, exist_ok=True)
source = OUT / 'site.s'
source.write_text('''.text
.global _start
_start: mov $60,%eax
 xor %edi,%edi
 syscall
.data
.global target
site: .long target - .
.space 12
.section .note.GNU-stack,"",@progbits
''')
target_source = OUT / 'target.s'
target_source.write_text('.data\n.global target\ntarget: .quad 41\n.section .note.GNU-stack,"",@progbits\n')
obj = OUT / 'site.o'
target_obj = OUT / 'target.o'
subprocess.run(['as', '--64', str(source), '-o', str(obj)], check=True)
subprocess.run(['as', '--64', str(target_source), '-o', str(target_obj)], check=True)
assert b'R_X86_64_PC32' in subprocess.check_output(['readelf', '-rW', str(obj)]), 'missing PC32 input'
for name, linker, extra in [('candidate', str(ROOT / 'target/ligature'), ['-nostdlib']),
                            ('lld', 'ld.lld-17', []), ('gnu', 'ld.bfd', [])]:
    exe = OUT / name
    subprocess.run([linker, *extra, '-static', '-o', str(exe), str(obj), str(target_obj)], check=True)
    data = exe.read_bytes()
    shoff = struct.unpack_from('<Q', data, 40)[0]
    count, names_index = struct.unpack_from('<HH', data, 60)
    sections = [struct.unpack_from('<IIQQQQIIQQ', data, shoff + 64 * i) for i in range(count)]
    strings = sections[names_index]
    names = data[strings[4]:strings[4] + strings[5]]
    by_name = {names[s[0]:].split(b'\0', 1)[0]: s for s in sections}
    section = by_name[b'.data']
    # The assembler emits one 4-byte PC-relative field followed by 12 padding bytes.
    # Both target and place are in this section; no candidate symbol/map is trusted.
    actual = struct.unpack_from('<i', data, section[4])[0]
    expected = (section[3] + 16) - section[3]
    assert actual == expected, ('pc32-equation', name, actual, expected)
    result = subprocess.run([str(exe)], capture_output=True, timeout=10)
    assert (result.returncode, result.stdout, result.stderr) == (0, b'', b'')
print('pc32-equation: three linker equations and executed outputs; 0 SKIP')
