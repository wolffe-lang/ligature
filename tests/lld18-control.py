#!/usr/bin/env python3
"""Five pinned-input lld18 controls; version differences remain explicit."""
import hashlib,json,pathlib,subprocess
ROOT=pathlib.Path(__file__).resolve().parent.parent;BASE=ROOT.parent;OUT=ROOT/'target/lld18-control';OUT.mkdir(parents=True,exist_ok=True)
ld=pathlib.Path('/usr/bin/ld.lld-18');raw=ld.read_bytes();sha=hashlib.sha256(raw).hexdigest();assert hashlib.sha256(ld.read_bytes()).hexdigest()==sha
version=subprocess.check_output([ld,'--version'],text=True).strip();assert '18.1.3' in version,version
rows=[]
for category,case in [('symbols','hello-hello'),('segments','pax-loop'),('entry','pax-hello'),('relocations','pax-std'),('tls','compiler-procs')]:
 dest=OUT/case;dest.mkdir(exist_ok=True);exe=dest/'program';objects=sorted((ROOT/'target/corpus'/case).glob('*.o'));assert objects
 lib=BASE/'link-inputs/sysroot'
 args=[ld,'-static','--emit-relocs','--gc-sections','--undefined=__wolf_rt_trap_at','--defsym=wolf_trap=__wolf_rt_trap_at','-o',exe,lib/'crt1.o',lib/'crti.o','--start-group',*objects,BASE/'link-inputs/libwolf_rt.a',lib/'libc.a',lib/'libunwind.a','--end-group',lib/'crtn.o']
 p=subprocess.run(list(map(str,args)),capture_output=True,timeout=120);assert p.returncode==0,p.stderr
 row={'chosen_class':category,'case':case,'argv':list(map(str,args)),'sha256':hashlib.sha256(exe.read_bytes()).hexdigest(),'comparisons':[]}
 for name,left,right in [('17-to-18',BASE/'pax-cases'/case/'lld',exe),('18-to-ligature',exe,BASE/'pax-cases'/case/'ligature')]:
  report=dest/(name+'.json');p=subprocess.run([ROOT/'tools/differ',left,right,'--output',report],capture_output=True,timeout=300)
  assert p.returncode in (0,1),p.stderr
  data=json.loads(report.read_text())
  row['comparisons'].append({'name':name,'status':p.returncode,'classes':[d['kind'] for d in data['differences']],'report':str(report.relative_to(OUT)),'report_sha256':hashlib.sha256(report.read_bytes()).hexdigest()})
 rows.append(row)
 (OUT/'results.json').write_text(json.dumps({'oracle_version':version,'oracle_sha256':sha,'rows':rows},indent=2)+'\n')
 print(category,case,row['comparisons'],flush=True)
