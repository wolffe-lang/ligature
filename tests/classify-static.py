#!/usr/bin/env python3
"""Keep TLS contents, layout and binding differences as separate recorded facts."""
import json,pathlib,subprocess,tempfile
ROOT=pathlib.Path(__file__).resolve().parent.parent
OUT=ROOT/'target/evidence/classify-static';OUT.mkdir(parents=True,exist_ok=True)
with tempfile.TemporaryDirectory(dir=OUT) as tmp:
    base=pathlib.Path(tmp)
    symbol={'name':'tls','type':6,'section':'.tdata','value':0,'size':1,'binding':1}
    different={**symbol,'value':1,'binding':0}
    report={'differences':[{'kind':'symbols','reference':[symbol],'candidate':[different]},{'kind':'tls','reference':{'bytes':'0a0b','memsz':2},'candidate':{'bytes':'0b0a','memsz':2}}]}
    (base/'results.json').write_text(json.dumps({'rows':[{'case':'fixture','structural':[{'oracle':'gnu','record':'comparison.json'}]}]}))
    for payload,equal in [('0b0a',True),('0b0c',False)]:
        report['differences'][1]['candidate']['bytes']=payload
        (base/'comparison.json').write_text(json.dumps(report))
        subprocess.run([ROOT/'tools/classify-static',base,base/'classified.json'],check=True,capture_output=True)
        result=json.loads((base/'classified.json').read_text())
        assert result['total']==2 and result['waivers']==[]
        tls=next(c for c in result['rows'][0]['classes'] if c['kind']=='tls')
        assert tls['symbol_normalized_initializers_equal']==equal
        assert tls['symbol_bindings_equal'] is False
print('TLS classification: same named payload despite ordering/binding changes; changed payload remains unequal; no findings waived; 0 SKIP')
