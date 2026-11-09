#!/usr/bin/env python3
"""Compile the linker's own objects, self-link twice, then execute that linker.

The PAX musl runtime is not replaceable with the public glibc release. Fetch
the digest-pinned published bundle first; an absent bundle is a named failure.
The objects link against the pinned compiler's own musl runtime ([wolf-rt],
tools/fetch-musl-runtime): one release for objects and runtime (#962/#963).
The bundle supplies the sysroot, cc and lld, and its pins stay checked. The row
has one outcome: PASS, or a named failure; no runtime digest is admitted.
"""
import hashlib,json,os,pathlib,subprocess,sys,tempfile,time
ROOT=pathlib.Path(__file__).resolve().parent.parent
OUT=ROOT/'target/evidence/self-link';OUT.mkdir(parents=True,exist_ok=True)
inputs=os.environ.get('LIGATURE_LINK_INPUTS') or (str(ROOT/'.link-inputs') if (ROOT/'.link-inputs/libwolf_rt.a').exists() else None)
if not inputs:
    message='SKIP self-link: ligature#13 exact musl link bundle is not provisioned; 1 SKIP'
    print(message,flush=True)
    (OUT/'status.json').write_text(json.dumps({'status':'SKIP','row':'self-link','issue':'ligature#13','reason':message})+'\n')
    sys.exit(1)
BASE=pathlib.Path(inputs).resolve();LIB=BASE/'sysroot';BIN=ROOT/'target/ligature'
def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
for _ in range(2):
    for row in (ROOT/'tests/pax-link.sums').read_text().splitlines():
        name,sha,size=row.split();p=BASE/name
        assert p.stat().st_size==int(size) and digest(p)==sha,('self-link pin',name)
RUNTIME=pathlib.Path(os.environ.get('LIGATURE_MUSL_RUNTIME',str(ROOT/'.wolf-bin/musl/libwolf_rt.a'))).resolve()
runtime_digest=digest(RUNTIME)
def call(name,args):
    print('SELF-LINK',name,'START',flush=True);start=time.monotonic()
    p=subprocess.run(list(map(str,args)),capture_output=True,timeout=2400)
    (OUT/(name+'.stdout')).write_bytes(p.stdout);(OUT/(name+'.stderr')).write_bytes(p.stderr)
    (OUT/(name+'.command.json')).write_text(json.dumps({'argv':list(map(str,args)),'status':p.returncode,'seconds':time.monotonic()-start},indent=2)+'\n')
    assert p.returncode==0,('self-link-'+name,p.returncode,p.stderr[-2000:])
    print('SELF-LINK',name,'PASS',flush=True)
    return p
# Prove the runtime hands argv through before spending minutes linking the full tool. No runtime
# digest is admitted as a non-failing outcome (wolf-lang#962 closed at 0.2.36; the admission for the
# 0.2.35 runtime was retired with the 0.2.38 pin).
preflight=subprocess.run([sys.executable,'-I',str(ROOT/'tests/musl-argv.py')])
assert preflight.returncode==0,('FAIL self-link-argv-preflight: the pinned runtime does not hand argv through',preflight.returncode,runtime_digest)
wolf=os.environ.get('WOLF',str(ROOT/'.wolf-bin/wolf'))
object_dir=pathlib.Path(tempfile.mkdtemp(prefix='objects-',dir=OUT))
# mkdtemp makes it 0700, owned by the container's root; the evidence upload reads it from the host.
object_dir.chmod(0o755)
call('objects',[wolf,'build','--no-cache','--emit=obj',ROOT/'src/ligature.lu','-o',object_dir/'ligature.o'])
objects=sorted(object_dir.glob('*.o'))
assert len(objects)>1,'self-link compiler module object set is missing'
def link_args(inputs):
    return ['-static','-nostdlib','--gc-sections','--undefined=__wolf_rt_trap_at','--defsym=wolf_trap=__wolf_rt_trap_at',LIB/'crt1.o',LIB/'crti.o','--start-group',*inputs,RUNTIME,LIB/'libc.a',LIB/'libunwind.a','--end-group',LIB/'crtn.o']
args=link_args(objects)
first=OUT/'ligature-first';second=OUT/'ligature-second';third=OUT/'ligature-third'
call('first',[BIN,*args,'-o',first]);call('second',[BIN,*args,'-o',second])
assert first.read_bytes()==second.read_bytes(),'self-link-determinism'
call('verify',[BIN,'verify',first])
version=call('execute',[first,'--version']);assert version.stdout.startswith(b'ligature '),'self-link-execute-version'
call('third',[first,*args,'-o',third]);assert first.read_bytes()==third.read_bytes(),'self-link-bootstrap-identity'
# Run the self-linked linker on an independently compiled executed fixture.
hello=ROOT/'tests/corpus/hello/hello.lu';hello_obj=OUT/'hello.o';hello_exe=OUT/'hello'
call('hello-objects',[wolf,'build','--no-cache','--emit=obj',hello,'-o',hello_obj])
hello_args=link_args([hello_obj])
call('hello-link',[first,*hello_args,'-o',hello_exe])
hello_run=call('hello-execute',[hello_exe]);assert (hello_run.stdout,hello_run.stderr)==(b'hello, wolf\n',b''),'self-link-hello-output'
call('hello-verify',[first,'verify',hello_exe])
records=[]
for _ in range(2):records.append({p.name:digest(p) for p in (*objects,first,second,third,hello_exe)})
assert records[0]==records[1]
(OUT/'status.json').write_text(json.dumps({'status':'PASS','row':'self-link','hashes_read_twice':records,'byte_identical':True,'object_directory':str(object_dir),'objects':len(objects)},indent=2)+'\n')
print('self-link: own objects, two seed links, executable bootstrap link, byte identity, executed hello; 0 SKIP',flush=True)
