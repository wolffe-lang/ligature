#!/usr/bin/env python3
"""Build unchanged PAX inputs, link them here, boot through PAX's own suite.
No kernel implementation is read or edited. Run inside the provisioned x86 image
with the lane root mounted; caller holds the shared CPU lock for this gauntlet.
"""
import argparse,hashlib,json,os,pathlib,runpy,shutil,subprocess,time
p=argparse.ArgumentParser();p.add_argument('--pax',type=pathlib.Path,required=True);p.add_argument('--out',type=pathlib.Path,required=True);p.add_argument('--wolf',required=True);p.add_argument('--tier',choices=('native','release','both'),default='both');a=p.parse_args()
R=pathlib.Path(__file__).resolve().parent.parent;B=R/'target/ligature';a.pax=a.pax.resolve();a.out=a.out.resolve();a.out.mkdir(parents=True,exist_ok=True);commands=[]
snapshot=runpy.run_path(str(R/'tools/differ'))['snapshot']
def call(name,args,cwd=R,env=None,permit=None):
 print(name,'START',flush=True);begin=time.monotonic();r=subprocess.run(list(map(str,args)),cwd=cwd,env=env,capture_output=True,timeout=1100)
 (a.out/(name+'.stdout')).write_bytes(r.stdout);(a.out/(name+'.stderr')).write_bytes(r.stderr)
 commands.append({'name':name,'argv':list(map(str,args)),'status':r.returncode,'seconds':time.monotonic()-begin})
 if r.returncode and permit and permit.encode() in r.stderr and b'__pax_image_start' in r.stderr:
  print(name,'NAMED ORACLE REFUSAL',r.stderr.decode(),flush=True);return None
 assert r.returncode==0,(name,r.returncode,r.stderr[-3000:]);print(name,'PASS',flush=True);return r.stdout

def sha(path):
 values=[hashlib.sha256(path.read_bytes()).hexdigest() for _ in range(2)];assert values[0]==values[1];return values
assert (a.pax/'boot/kernel.ld').read_bytes()==(R/'tests/fixtures/pax-kernel.ld').read_bytes()
source_head=call('pax-head',['git','rev-parse','HEAD'],a.pax).decode().strip()
env=dict(os.environ,PAX_WOLF=a.wolf,PAX_REQUIRE_UEFI='1')
call('limine',[a.pax/'tools/fetch-limine'],a.pax)
(a.pax/'build').mkdir(exist_ok=True)
selected=('native','release') if a.tier=='both' else (a.tier,)
previous=json.loads((a.out/'results.json').read_text()) if (a.out/'results.json').exists() else {'rows':[]}
rows=[r for r in previous['rows'] if r['tier'] not in selected]
for tier in selected:
 d=a.out/tier;d.mkdir(exist_ok=True)
 call(tier+'-inputs',[a.pax/'tools/build-kernel',*(['--release'] if tier=='release' else []),'--src','kernel/kmain_paging.lu',d],a.pax,env)
 root=d/'kmain_paging.o'
 wolfs=[root] if root.exists() else [p for p in sorted(d.glob('kmain_paging.*.o')) if '.asm-' not in p.name]
 inputs=[d/'start.o',*sorted(d.glob('*.asm-*.o')),*wolfs,d/'kmain_paging.rt-none.a']
 hashes={p.name:sha(p) for p in inputs};links={};symbols={};proofs={}
 for name,ld,options in [('candidate',B,['-nostdlib']),('lld17',R/'.link-inputs/ld.lld',['--emit-relocs']),('lld18','ld.lld-18',['--emit-relocs']),('gnu','ld.bfd',['--emit-relocs','--no-relax'])]:
  out=d/(name+'.elf')
  command=[ld,*options,'-static','-T',R/'tests/fixtures/pax-kernel.ld','-o',out,*inputs]
  if name=='lld17':
   control=call(tier+'-'+name,command,permit='R_X86_64_REX_GOTPCRELX out of range: -2147483652')
   if control is None:call(tier+'-'+name+'-no-relax',[*command,'--no-relax'])
  else:call(tier+'-'+name,command)
  links[name]=sha(out)
  symbols[name]=call(tier+'-'+name+'-symbols',['nm','-n',out]).decode()
  call(tier+'-'+name+'-headers',['readelf','-lSW',out])
  if name=='candidate':
   call(tier+'-verify',[B,'verify',out]);view=snapshot(out);assert not view['refused'],view['refused'][:10];proofs[name]=len(view['relocations'])
   repeat=d/'repeat.elf';call(tier+'-determinism',[B,'-nostdlib','-static','-T',R/'tests/fixtures/pax-kernel.ld','-o',repeat,*inputs]);assert sha(repeat)==links[name]
   repeat.unlink()
 images=a.out/'images'/tier;images.mkdir(parents=True,exist_ok=True);shutil.copyfile(d/'candidate.elf',images/'kmain_paging.elf')
 call(tier+'-image',[a.pax/'tools/mkimage',images/'kmain_paging.elf',images/'kmain_paging.iso'],a.pax,env)
 call(tier+'-boots',[a.pax/'tests/mpx2-paging','--images',a.out/'images','--tier',tier,'--firmware','both'],a.pax,env)
 # --images exercises G2-G8; explicitly assert G1's LOAD/bounds via independent ELF decoding too.
 helper=runpy.run_path(str(R/'tests/aarch64-sites.py'));data,heads,names,read,rels=helper['decode'](d/'candidate.elf')
 import struct
 ph=struct.unpack_from('<Q',data,32)[0];loads=[struct.unpack_from('<IIQQQQQQ',data,ph+56*i) for i in range(struct.unpack_from('<H',data,56)[0])];loads=[x for x in loads if x[0]==1]
 assert [x[1] for x in loads]==[5,4,6]
 bounds={}
 for name,text in symbols.items():bounds[name]={line.split()[2]:int(line.split()[0],16) for line in text.splitlines() if len(line.split())==3 and line.split()[2].startswith('__pax_')}
 for segment,start,end in zip(loads,['__pax_text_start','__pax_rodata_start','__pax_data_start'],['__pax_text_end','__pax_rodata_end','__pax_image_end']):
  assert bounds['candidate'][start]<=segment[3] and segment[3]+segment[6]<=bounds['candidate'][end]
 assert {p.name:sha(p) for p in inputs}==hashes
 bootfiles={}
 for path in (a.pax/'build').glob('mpx2-paging-'+tier+'-*'):
  if path.is_file():
   dest=a.out/path.name;shutil.copyfile(path,dest);bootfiles[path.name]=sha(dest)
 rows.append({'tier':tier,'input_hashes_read_twice':hashes,'output_hashes_read_twice':links,'independent_candidate_relocations':proofs['candidate'],'bounds':bounds,'bounds_equal_oracles':{name:bounds[name]==bounds['candidate'] for name in bounds},'boot_evidence_hashes_read_twice':bootfiles,'iso_sha256_read_twice':sha(images/'kmain_paging.iso')})
 (a.out/'results.json').write_text(json.dumps({'source_head':source_head,'rows':rows,'commands':commands},indent=2)+'\n')
print('kernel-pax: qualified tiers', [r['tier'] for r in rows], '; four binary linkers, deterministic candidates, independent sites, BIOS/UEFI and monitor-backed W^X/halt gates; 0 SKIP',flush=True)
