#!/usr/bin/env python3
"""Exercise the actual digest/status predicate without executing a long link."""
import ast,pathlib
ROOT=pathlib.Path(__file__).resolve().parent.parent
path=ROOT/'tests/self-link.py';tree=ast.parse(path.read_text())
function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='permits_blocked')
namespace={};exec(compile(ast.Module(body=[function],type_ignores=[]),str(path),'exec'),namespace)
allows=namespace['permits_blocked'];pin='9d859b9e6b5319f5a6f609e73ba0d71981d2dfa489882648ac9f454cd9db739c'
assert allows(pin,2)
assert not any(allows(digest,status) for digest,status in [(pin,0),(pin,1),(pin,3),('0'*64,2),(pin[:-1]+'d',2),('',2)])
assert any(isinstance(n,ast.If) and isinstance(n.test,ast.Call) and isinstance(n.test.func,ast.Name) and n.test.func.id=='permits_blocked' for n in tree.body)
print('self-link blocker: exact fetched runtime digest and reproduced argv status required; other digests hard-gated; 0 SKIP')
