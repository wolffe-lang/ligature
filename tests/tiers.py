#!/usr/bin/env python3
import importlib.util, pathlib, types
root = pathlib.Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location('tiers', root/'ci/tiers.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
assert m.classify('src/elf/reader.lu')[0] == m.PR
assert m.classify('unknown')[0] == m.FULL
assert m.classify('census/pax-link-set.json')[0] == m.PR
for tier, jobs in [('pr', ['plan-test','linux']), ('full', ['plan-test','linux']), ('noop', [])]:
    import json
    needs = {'plan': {'result':'success', 'outputs':{'tier':tier,'jobs':json.dumps(jobs)}}}
    needs.update({j:{'result':'success' if j in jobs else 'skipped'} for j in ['plan-test','linux']})
    assert m.verdict(needs) == 0
    if jobs:
        needs[jobs[0]]['result']='failure'
        assert m.verdict(needs) == 1
print('tiers: selected failures rejected; 0 SKIP')
