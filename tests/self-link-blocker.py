#!/usr/bin/env python3
"""No runtime digest is admitted as BLOCKED: the self-link row has one outcome, PASS or a named failure."""
import ast,pathlib
ROOT=pathlib.Path(__file__).resolve().parent.parent
path=ROOT/'tests/self-link.py';source=path.read_text();tree=ast.parse(source)
assert not [n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='permits_blocked'],'FAIL self-link-admission: permits_blocked still defined'
assert 'BLOCKED' not in source,'FAIL self-link-admission: a BLOCKED outcome is still written'
assert '9d859b9e6b5319f5a6f609e73ba0d71981d2dfa489882648ac9f454cd9db739c' not in source,'FAIL self-link-admission: the 0.2.35 runtime digest is still named'
assert 'preflight.returncode==0' in source.replace(' ',''),'FAIL self-link-admission: the argv preflight is not demanded'
assert "'status':'PASS'" in source.replace(' ',''),'the PASS record is written'
print('self-link admission: no digest admitted; the argv preflight and every assertion are unconditional; 0 SKIP')
