#!/usr/bin/env python3
"""The local record enumerates every gate command, plus the real candidate leaf."""
import json
from pathlib import Path
import shlex
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
planner = ROOT / 'tools/record-steps'
if not planner.is_file():
    print('FAIL record-steps-present')
    sys.exit(1)
q = subprocess.run([str(planner)], cwd=ROOT, capture_output=True, text=True)
assert q.returncode == 0, (q.stdout, q.stderr)
steps = json.loads(q.stdout)
assert len({s['name'] for s in steps}) == len(steps), steps
assert ['tools/check-candidate-wolf'] in [s['argv'] for s in steps]
assert ['python3', '-I', 'tests/candidate-wolf.py'] in [s['argv'] for s in steps]
for filename in ('tools/check', 'tools/check-core'):
    for line in (ROOT / filename).read_text().splitlines():
        if line.startswith('python3 -I ') or line.startswith('tools/') and line != 'tools/check-core':
            words = shlex.split(line)
            assert words in [s['argv'] for s in steps], (filename, line)
assert ['.wolf-bin/wolf', 'fmt', '--check', 'src'] in [s['argv'] for s in steps]
assert ['.wolf-bin/wolf', 'test', '--deny-warnings', '--json', 'src'] in [s['argv'] for s in steps]
for required in ('real-ligature', 'self-link', 'link-cost', 'link-memory', 'runtime', 'candidate-wolf'):
    assert any(s['name'] == required for s in steps), required
print(f'PASS record-steps-complete: {len(steps)} commands, no duplicate names')
