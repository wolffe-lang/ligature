#!/usr/bin/env python3
"""Read exact API payloads after scratch reuse on native, release and checked."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {'empty', 'long', 'apply-cycle', 'attribute-cycle', 'metadata-field', 'collect-read'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--wolf', type=Path, default=ROOT / '.wolf-bin/wolf')
    parser.add_argument('--std', type=Path, default=ROOT / '.wolf-bin/std')
    parser.add_argument('--label', default='pin')
    args = parser.parse_args()
    if not args.wolf.is_file() or not (args.std / 'STD-REV').is_file():
        print('FAIL region-payload-api-inputs: compiler and bundled std required')
        return 1
    out = ROOT / 'target/evidence/region-payload-api' / args.label
    out.mkdir(parents=True, exist_ok=True)
    home = out / 'home'
    home.mkdir(exist_ok=True)
    env = dict(os.environ, WOLF_STD=str(args.std.resolve()), HOME=str(home), SHELL='/bin/sh', LC_ALL='C')
    wolf = str(args.wolf.resolve())
    failed = False
    for machine in ('native', 'release', 'checked'):
        row = f'region-payload-api-{args.label}-{machine}'
        if machine == 'checked':
            q = subprocess.run([wolf, 'conform-run', 'src/region_payload_test.lu', '--checked', '--json'], cwd=ROOT, env=env, capture_output=True, text=True, timeout=600)
            records = [json.loads(line) for line in q.stdout.splitlines() if line.startswith('{')]
            good = q.returncode == 0 and len(records) == 1 and records[0].get('verdict') == 'exit(0)'
            text = records[0].get('stdout_inline', '') if good else ''
        else:
            binary = out / machine
            cmd = [wolf, 'build', '--no-cache', '--deny-warnings', 'src/region_payload_test.lu', '-o', str(binary)]
            if machine == 'release':
                cmd.append('--release')
            build = subprocess.run(cmd, cwd=ROOT, env=env, capture_output=True, text=True, timeout=600)
            (out / f'{machine}-build.log').write_text(build.stdout + build.stderr)
            if build.returncode:
                print(f'FAIL {row}-build: exit {build.returncode}', flush=True)
                for line in (build.stdout + build.stderr).splitlines():
                    print('  ' + line)
                failed = True
                continue
            q = subprocess.run([str(binary)], cwd=ROOT, env=env, capture_output=True, text=True, timeout=60)
            good, text = q.returncode == 0, q.stdout
        (out / f'{machine}.log').write_text(q.stdout + q.stderr)
        rows = [line.split()[1] for line in text.splitlines() if line.startswith('ROW ') and line.endswith(' PASS')]
        good = good and len(rows) == len(EXPECTED) and set(rows) == EXPECTED
        print(('PASS ' if good else 'FAIL ') + row + f': {len(rows)} payload rows', flush=True)
        failed |= not good
    return int(failed)


if __name__ == '__main__':
    sys.exit(main())
