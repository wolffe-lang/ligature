#!/usr/bin/env python3
"""Black-box runtime argv preflight. Exit 2 is BLOCKED on wolf-lang#962, not PASS."""
import hashlib,json,os,pathlib,subprocess,sys
ROOT=pathlib.Path(__file__).resolve().parent.parent
OUT=ROOT/'target/evidence/musl-argv';OUT.mkdir(parents=True,exist_ok=True)
BASE=pathlib.Path(os.environ.get('LIGATURE_LINK_INPUTS',str(ROOT/'.link-inputs'))).resolve();LIB=BASE/'sysroot'
WOLF=pathlib.Path(os.environ.get('WOLF',str(ROOT/'.wolf-bin/wolf'))).resolve()
SOURCE=ROOT/'tests/fixtures/musl-argv'
def call(args,env=None):
    p=subprocess.run(list(map(str,args)),capture_output=True,timeout=120,env=env)
    assert p.returncode==0,(args,p.returncode,p.stderr)
    return p
call([WOLF,'build','--no-cache','--emit=obj',SOURCE/'main.lu','-o',OUT/'main.o'])
env={**os.environ,'CC':'cc','WOLF_RT_LIB':str(WOLF.parent/'libwolf_rt.a')}
call([WOLF,'build','--no-cache',SOURCE/'main.lu','-o',OUT/'glibc'],env)
objects=[LIB/'crt1.o',LIB/'crti.o','--start-group',OUT/'main.o',BASE/'libwolf_rt.a',LIB/'libc.a',LIB/'libunwind.a','--end-group',LIB/'crtn.o']
for label,ld in [('lld',BASE/'ld.lld'),('gnu','ld.bfd')]:
    call([ld,'-static','--gc-sections','--undefined=__wolf_rt_trap_at','--defsym=wolf_trap=__wolf_rt_trap_at','-o',OUT/label,*objects])
call(['musl-gcc','-c',SOURCE/'control.c','-o',OUT/'control.o'])
call([BASE/'ld.lld','-static','-o',OUT/'c-musl',LIB/'crt1.o',LIB/'crti.o',OUT/'control.o',LIB/'libc.a',LIB/'crtn.o'])
expected=b'argc=3\n[--version]\n[space word]\n[]\n';rows=[]
for label in ('glibc','lld','gnu','c-musl'):
    path=OUT/label;args=[str(path),'--version','space word','']
    p=subprocess.run(args,capture_output=True,timeout=30)
    with path.open('rb') as stream:sha=hashlib.file_digest(stream,'sha256').hexdigest()
    rows.append({'case':label,'argv':args,'status':p.returncode,'stdout':p.stdout.decode(),'stderr':p.stderr.decode(),'sha256':sha})
    print('musl-argv',label,p.returncode,repr(p.stdout),repr(p.stderr),flush=True)
assert all(r['status']==0 and r['stderr']=='' for r in rows),rows
assert rows[0]['stdout']==rows[3]['stdout']==expected.decode(),rows
blocked=rows[1]['stdout']==rows[2]['stdout']=='argc=0\n'
result={'row':'self-link runtime argv','status':'BLOCKED' if blocked else 'PASS','issue':'wolf-lang#962' if blocked else None,'rows':rows}
(OUT/'results.json').write_text(json.dumps(result,indent=2)+'\n')
if blocked:
    print('BLOCKED self-link: wolf-lang#962; both pinned musl links lose argv while cc/glibc and the pinned C/musl control preserve it',flush=True)
    sys.exit(2)
assert rows[1]['stdout']==rows[2]['stdout']==expected.decode(),rows
print('musl-argv: all three Wolf links and pinned C/musl control preserve argv; 0 SKIP',flush=True)
