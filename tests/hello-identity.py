#!/usr/bin/env python3
"""Hello's link identity is held per runtime pin, by digest, and the runner reads it.

The 0.2.35 entry equals the M0 census; every entry has a 64-hex runtime digest, three archives,
unique sorted names; tests/static-pax.py selects the entry by the digest of the runtime it linked and
spells no pin's counts itself; an unknown runtime is a named refusal, never a pass."""
import ast,json,pathlib,re
ROOT=pathlib.Path(__file__).resolve().parent.parent
fixture=json.loads((ROOT/'tests/fixtures/hello-identity.json').read_text())
assert fixture['format']=='ligature.hello-identity.v1'
census=json.loads((ROOT/'census/pax-link-set.json').read_text())['oracle_observations']['hello-hello']
by={e['runtime_sha256']:e for e in fixture['entries']}
assert len(by)==len(fixture['entries'])>=2,'FAIL hello-identity: duplicate or missing entries'
for sha,e in by.items():
    assert re.fullmatch('[0-9a-f]{64}',sha),('FAIL hello-identity: digest',sha)
    assert set(e['members'])=={'libwolf_rt.a','libc.a','libunwind.a'} and all(isinstance(v,int) and v>0 for v in e['members'].values()),('FAIL hello-identity: members',sha)
    names=e['defined_globals'];assert names==sorted(set(names)) and len(names)>300,('FAIL hello-identity: names',sha)
    assert e['source'] and e['runtime'],('FAIL hello-identity: unsourced entry',sha)
old=by['9d859b9e6b5319f5a6f609e73ba0d71981d2dfa489882648ac9f454cd9db739c']
assert old['members']=={'libwolf_rt.a':32,'libc.a':322,'libunwind.a':5} and old['defined_globals']==sorted({s['name'] for s in census['lld_defined_symbols']}),'FAIL hello-identity: the 0.2.35 entry differs from the M0 census'
new=by['37252e1d0d97d917bc19e95f27d8304b8da3d31afd7a2120395e0c9a87bbc740']
assert new['members']=={'libwolf_rt.a':32,'libc.a':328,'libunwind.a':5} and len(new['defined_globals'])==396,'FAIL hello-identity: the 0.2.38 entry is not the measured one'
assert {'__wolf_rt_main_start'}<=set(new['defined_globals']) and '__wolf_rt_stack_start' not in new['defined_globals']
source=(ROOT/'tests/static-pax.py').read_text()
assert 'tests/fixtures/hello-identity.json' in source,'FAIL hello-identity: tests/static-pax.py does not read the fixture'
assert "'libc.a':322" not in source.replace(' ','') and 'len(names)==401' not in source.replace(' ',''),'FAIL hello-identity: tests/static-pax.py still spells the 0.2.35 constants'
tree=ast.parse(source)
assert any(isinstance(n,ast.FunctionDef) and n.name=='hello_identity' for n in tree.body),'FAIL hello-identity: no hello_identity selector in tests/static-pax.py'
ns={};exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,(ast.Import,ast.ImportFrom)) or (isinstance(n,ast.FunctionDef) and n.name=='hello_identity')],type_ignores=[]),'static-pax','exec'),ns)
try:ns['hello_identity'](ROOT,'0'*64)
except AssertionError as e:assert 'not measured' in str(e),e
else:raise AssertionError('FAIL hello-identity: an unknown runtime digest was not refused')
assert ns['hello_identity'](ROOT,'37252e1d0d97d917bc19e95f27d8304b8da3d31afd7a2120395e0c9a87bbc740')['members']['libc.a']==328
print('hello-identity: two pins by digest, the 0.2.35 entry equal to the census, the 0.2.38 entry measured, unknown runtimes refused by name; 0 SKIP')
