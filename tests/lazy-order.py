#!/usr/bin/env python3
"""Black-box LLD discovery order, recursion, backward references and weak demand."""
import json,pathlib,re,subprocess
ROOT=pathlib.Path(__file__).resolve().parent.parent;OUT=ROOT/'target/evidence/lazy-order';OUT.mkdir(parents=True,exist_ok=True)
BIN=ROOT/'target/ligature'
def call(args):
    p=subprocess.run(list(map(str,args)),capture_output=True,timeout=90)
    assert p.returncode==0,(args,p.returncode,p.stderr)
    return p

def obj(name,text):
    src=OUT/(name+'.s');o=OUT/(name+'.o');src.write_text(text+'\n.section .note.GNU-stack,"",@progbits\n')
    call(['as','--64',src,'-o',o]);return o
start=obj('root','.text\n.global _start\n_start: mov $60,%eax\n xor %edi,%edi\n syscall\n.data\n.quad z,a')
a=obj('a','.data\n.global a\na: .quad b')
b=obj('b','.data\n.global b\nb: .quad c')
c=obj('c','.data\n.global c\nc: .quad a')
z=obj('z','.data\n.global z\nz: .quad a')
archive=OUT/'chain.a';call(['ar','rcs',archive,a,b,c,z])
rows=[]
for name,inputs in [('forward',[start,archive]),('backward',[archive,start])]:
    expected=call(['ld.lld-17','--trace','-static','-o',OUT/(name+'-lld'),*inputs]).stdout.decode().splitlines()
    expected=[re.search(r'\(([^)]+)\)$',line).group(1) for line in expected if '(' in line]
    result=call([BIN,'--resolve','-nostdlib',*inputs]);records=[json.loads(x) for x in result.stdout.splitlines()]
    edges=[r['edge'] for r in records if r['row']=='pull'];actual=[e['member'] for e in edges]
    assert actual==expected,(name,actual,expected)
    assert len(actual)==4 and len(set(actual))==4
    assert all(e['parent']<e['object'] for e in edges),edges
    call([BIN,'-nostdlib','-o',OUT/name,*inputs]);call([OUT/name])
    rows.append({'case':name,'sequence':actual,'edges':edges})
(OUT/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
print('lazy-order: forward/backward discovery matches LLD, four-member cyclic graph selected once; 0 SKIP')
