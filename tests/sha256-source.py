#!/usr/bin/env python3
"""The SHA-256 core in src/sha256/sha256.lu is exactly what tools/gen-sha256 writes."""
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.exit(subprocess.run([sys.executable, '-I', str(ROOT / 'tools/gen-sha256'), '--check']).returncode)
