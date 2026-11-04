#!/usr/bin/env python3
"""Exercise the released compiler's real --linker route with licensed inputs."""
import json
import os
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / 'target/evidence/real-ligature'
OUT.mkdir(parents=True, exist_ok=True)
BUNDLE = ROOT / '.link-inputs'
WOLF = pathlib.Path(os.environ.get('WOLF', str(ROOT / '.wolf-bin/wolf'))).resolve()
LINKER = ROOT / 'target/ligature'
TARGET = OUT / 'hello'
env = dict(os.environ, CC='/missing/cc', LIGATURE_SYSROOT=str(BUNDLE / 'sysroot'), WOLF_RT_LIB=str(BUNDLE / 'libwolf_rt.a'))
command = [str(WOLF), 'build', '--no-cache', '--linker', str(LINKER), str(ROOT / 'tests/corpus/hello/hello.lu'), '-o', str(TARGET)]
result = subprocess.run(command, env=env, capture_output=True, timeout=1200)
assert result.returncode == 0, ('FAIL real-ligature-link', result.returncode, result.stderr[-2000:])
result = subprocess.run([str(TARGET)], capture_output=True, timeout=30)
assert (result.returncode, result.stdout, result.stderr) == (0, b'hello, wolf\n', b''), 'FAIL real-ligature-execute'
subprocess.run([str(LINKER), 'verify', str(TARGET)], check=True, timeout=120)
(OUT / 'command.json').write_text(json.dumps(command, indent=2) + '\n')
print('real-ligature: released compiler --linker route, licensed musl runtime, verified executed hello; 0 SKIP', flush=True)
