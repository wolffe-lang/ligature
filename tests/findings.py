#!/usr/bin/env python3
import copy,json,pathlib,runpy
ROOT=pathlib.Path(__file__).resolve().parent.parent
check=runpy.run_path(str(ROOT/'tools/check-findings'))['validate']
report=json.loads((ROOT/'notes/ld03/findings.json').read_text());assert check(report)==87
for kind in ('drop','reclassify','change-record','duplicate','swap-oracle'):
    bad=copy.deepcopy(report)
    if kind=='drop':bad['findings'].pop()
    if kind=='reclassify':bad['findings'][0]['status']='resolved'
    if kind=='change-record':bad['findings'][0]['facts']['candidate_only']+=1
    if kind=='duplicate':bad['findings'].append(bad['findings'][0])
    if kind=='swap-oracle':bad['findings'][0]['name']=bad['findings'][0]['name'].replace('/lld/','/gnu/')
    try:check(bad)
    except AssertionError:pass
    else:raise AssertionError(('finding mutation accepted',kind))
print('named-findings: five mutation witnesses rejected; 0 SKIP')
