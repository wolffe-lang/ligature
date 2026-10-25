#!/usr/bin/env python3
"""Exercise the Wolf resolver on independent ELF/archive fixtures."""
import json, pathlib, subprocess
ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT/'target/evidence/resolve'
OUT.mkdir(parents=True, exist_ok=True)
BIN = ROOT/'target/ligature'

def command(argv):
    return subprocess.run(list(map(str,argv)), capture_output=True, timeout=60)
def obj(name, text):
    src=OUT/(name+'.s'); dst=OUT/(name+'.o')
    src.write_text(text+'\n.section .note.GNU-stack,"",@progbits\n')
    p=command(['as','--64',src,'-o',dst]); assert p.returncode == 0,p.stderr
    return dst
def archive(name, *members):
    dst=OUT/(name+'.a')
    dst.unlink(missing_ok=True)
    p=command(['ar','rcs',dst,*members]); assert p.returncode == 0,p.stderr
    return dst
def resolve(*args, error=None):
    p=command([BIN,'--resolve','-nostdlib',*args])
    if error:
        assert p.returncode == 1 and error.encode() in p.stderr,(args,p.returncode,p.stderr)
        return []
    assert p.returncode == 0,p.stderr
    return [json.loads(x) for x in p.stdout.splitlines()]
def defs(rows):return {r['name']:r for r in rows if r['row']=='definition'}
def pulls(rows):return [r['edge'] for r in rows if r['row']=='pull']
start=obj('start','.text\n.global _start\n_start: .quad choice')
strong=obj('strong','.data\n.global choice\nchoice: .quad 11')
weak=obj('weak','.data\n.weak choice\nchoice: .quad 22')
weak2=obj('weak2','.data\n.weak choice\nchoice: .quad 33')
common=obj('common','.comm choice,16,64')
common2=obj('common2','.comm choice,32,32')
for files,winner in [([strong,weak],0),([weak,strong],1),([weak,weak2],0),([strong,common],0),([common,strong],1),([weak,common],1),([common,weak],0)]:
    row=defs(resolve(*files))['choice']; assert row['object']==winner,row
row=defs(resolve(common,common2))['choice']; assert row['size']==32 and row['value']==64,row
resolve(strong,strong,error='duplicate strong symbol choice')
a=archive('choices',weak,strong)
assert pulls(resolve(start,a))[0]['member']=='weak.o'
weakref=obj('weakref','.text\n.global _start\n.weak choice\n_start: .quad choice')
assert not pulls(resolve(weakref,a))
assert pulls(resolve(weakref,a,'-u','choice'))[0]['member']=='weak.o'
assert pulls(resolve(a,start))[0]['member']=='weak.o' # LLD-compatible lazy backward reference
# Group rescan revisits earlier archives, without adding unrelated members.
aobj=obj('a','.text\n.global a\na: .quad b')
bobj=obj('b','.text\n.global b\nb: .quad a')
ref=obj('ref','.text\n.global _start\n_start: .quad a')
a1=archive('a',aobj);a2=archive('b',bobj)
rows=resolve(ref,'--start-group',a2,a1,'--end-group')
assert [x['member'] for x in pulls(rows)]==['a.o','b.o']
assert 'b' in defs(resolve(ref,a2,a1)) # earlier archives remain lazy
resolve(ref,'--end-group',error='unmatched --end-group')
resolve(ref,'--start-group',error='unmatched --start-group')
# Duplicate member names remain distinct via header identity.
left=OUT/'left';right=OUT/'right';left.mkdir(exist_ok=True);right.mkdir(exist_ok=True)
(left/'same.o').write_bytes(aobj.read_bytes());(right/'same.o').write_bytes(bobj.read_bytes())
adup=archive('duplicate',left/'same.o',right/'same.o')
rows=resolve(ref,adup)
assert len(pulls(rows))==2 and len({x['header'] for x in pulls(rows)})==2
# COMDAT drops only the later group, not an ordinary duplicate definition.
c1=obj('comdat1','.section .text.pick,"axG",@progbits,pick,comdat\n.global pick\npick: ret')
c2=obj('comdat2','.section .text.pick,"axG",@progbits,pick,comdat\n.global pick\npick: nop\nret')
assert defs(resolve(c1,c2))['pick']['object']==0
resolve(strong,'--defsym=choice=choice',error='self-referential')
print('resolve: strong/weak/common, indexed archives, groups, duplicate names, COMDAT; 0 SKIP')
