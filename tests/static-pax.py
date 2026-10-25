#!/usr/bin/env python3
"""Strict local PAX-input writer census; differences are records, never waivers.

Run only in a lane container. Binary input pins are checked twice. All commands,
raw outputs and individual structural differences stay under target/static-pax.
The exit code covers behavior, verification, determinism and hello identity;
structural equality has its own explicit unresolved counter in results.json.
"""
import argparse,collections,hashlib,json,os,pathlib,subprocess,sys,time,traceback
ROOT=pathlib.Path(__file__).resolve().parent.parent

def digest(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def checked(argv,log,timeout=1200,allowed=(0,),cwd=ROOT,env=None):
    start=time.monotonic()
    p=subprocess.run(list(map(str,argv)),cwd=cwd,env=env,capture_output=True,timeout=timeout)
    pathlib.Path(str(log)+'.stdout').write_bytes(p.stdout);pathlib.Path(str(log)+'.stderr').write_bytes(p.stderr)
    pathlib.Path(str(log)+'.command.json').write_text(json.dumps({'argv':list(map(str,argv)),'status':p.returncode,'elapsed':time.monotonic()-start},indent=2)+'\n')
    assert p.returncode in allowed,(list(map(str,argv)),p.returncode,p.stderr[-2000:])
    return p

def main():
    ap=argparse.ArgumentParser();ap.add_argument('inputs',type=pathlib.Path);a=ap.parse_args()
    BASE=a.inputs.resolve();LIB=BASE/'sysroot';BIN=ROOT/'target/ligature';OUT=ROOT/'target/static-pax';OUT.mkdir(parents=True,exist_ok=True)

    for _ in range(2):
        for row in (ROOT/'tests/pax-link.sums').read_text().splitlines():
            name,sha,size=row.split();f=BASE/name
            assert f.stat().st_size==int(size) and digest(f)==sha,('pin',name)
    print('PINS verified twice',flush=True)
    # The five remaining top-level run-phase compiler programs; hello already has its census row.
    compile_rows=[]
    for source in sorted((ROOT/'tests/corpus/compiler').glob('*.lu')):
        dest=ROOT/'target/corpus'/('compiler-'+source.stem);dest.mkdir(exist_ok=True)
        try:
            checked([os.environ['WOLF'],'build','--no-cache','--emit=obj',source,'-o',dest/'main.o'],OUT/('emit-'+source.stem))
            compile_rows.append({'case':source.stem,'status':'compiled'})
        except Exception as exc:
            compile_rows.append({'case':source.stem,'status':'failed','error':str(exc)})
    (OUT/'compile.json').write_text(json.dumps(compile_rows,indent=2)+'\n')
    rows=[];functional_failures=sum(r['status']=='failed' for r in compile_rows);structural=0
    for case in sorted((ROOT/'target/corpus').iterdir()):
        objects=sorted(case.glob('*.o'))
        if not objects:continue
        dest=OUT/case.name;dest.mkdir(exist_ok=True)
        row={'case':case.name,'objects':[{'path':p.name,'sha256':digest(p)} for p in objects]}
        print('BEGIN',case.name,flush=True)
        try:
            checked([ROOT/'tools/oracle','--link-inputs',BASE,'--out',dest/'oracle',*objects],dest/'oracles')
            exe=dest/'program'
            args=[BIN,'-static','-nostdlib','--gc-sections','--undefined=__wolf_rt_trap_at','--defsym=wolf_trap=__wolf_rt_trap_at','-o',exe,LIB/'crt1.o',LIB/'crti.o','--start-group',*objects,BASE/'libwolf_rt.a',LIB/'libc.a',LIB/'libunwind.a','--end-group',LIB/'crtn.o']
            first=checked(args,dest/'link1');sha=digest(exe)
            print('LINK1',case.name,sha,flush=True)
            checked(args,dest/'link2');assert digest(exe)==sha,'nondeterministic link'
            checked([BIN,'verify',exe],dest/'verify')
            work=dest/'run';work.mkdir(exist_ok=True)
            (work/'x.lu').write_text('//! member: false\nfn main() -> !int {\n    print("typed at PAX console, checked by wolf")\n    0\n}\n')
            p=checked([exe],dest/'run',timeout=90,allowed=tuple(range(-128,256)),cwd=work,env={'PATH':'/usr/bin:/bin','LC_ALL':'C'})
            behavior={'stdout_hex':p.stdout.hex(),'stderr_hex':p.stderr.hex(),'status':p.returncode}
            oracle=json.loads((dest/'oracle/manifest.json').read_text())
            assert behavior==oracle['lld']['run']==oracle['gnu']['run'],('behavior',behavior,oracle)
            row.update({'behavior':'equal','run':behavior,'sha256':sha,'deterministic':True,'verified':True})
            if case.name=='hello-hello':
                resolved=checked([*args,'--resolve'],dest/'resolution')
                records=[json.loads(x) for x in resolved.stdout.splitlines()]
                pulls=[r['edge'] for r in records if r['row']=='pull']
                counts=collections.Counter(pathlib.Path(r['archive']).name for r in pulls)
                assert counts=={'libwolf_rt.a':32,'libc.a':322,'libunwind.a':5},counts
                symbols=checked(['nm','-g','--defined-only',exe],dest/'globals').stdout.decode()
                names={line.split()[-1] for line in symbols.splitlines()}
                census=json.loads((ROOT/'census/pax-link-set.json').read_text())['oracle_observations']['hello-hello']
                expected={s['name'] for s in census['lld_defined_symbols']}
                assert len(names)==401 and names==expected,('symbols',sorted(names-expected),sorted(expected-names))
                row['hello_identity']={'members':dict(counts),'definitions':len(names),'equal_names':True}
            differences=[]
            for oracle_name in ('lld','gnu'):
                result=dest/(oracle_name+'-differ.json')
                diff=checked([ROOT/'tools/differ',dest/'oracle'/oracle_name/'program',exe,'--output',result],dest/(oracle_name+'-differ'),allowed=(0,1),timeout=300)
                data=json.loads(result.read_text())
                differences.append({'oracle':oracle_name,'status':diff.returncode,'record':str(result.relative_to(OUT)),'kinds':[r['kind'] for r in data['differences']],'unexplained':len(data['unexplained'])})
                structural+=len(data['unexplained'])
            row['structural']=differences
            row['status']='behavior-verified-structural-recorded'
        except Exception as exc:
            traceback.print_exc()
            row['status']='failed';row['error']=str(exc);row['error_type']=type(exc).__name__;functional_failures+=1
        rows.append(row)
        result={'format':'ligature.ld01.static-rows.v1','compile':compile_rows,'rows':rows,'functional_failures':functional_failures,'unexplained_structural_differences':structural,'structural_claim':'not equivalent while unexplained is nonzero','pax_boot':'not run by this Linux-only harness'}
        (OUT/'results.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
        print('END',case.name,row['status'],'functional_failures',functional_failures,'unexplained',structural,flush=True)
    print('COMPLETE',len(rows),'rows; functional failures',functional_failures,'unexplained structural differences',structural,flush=True)
    return bool(functional_failures)

if __name__ == "__main__":
    raise SystemExit(main())
