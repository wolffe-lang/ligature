#!/usr/bin/env python3
"""Independent per-site decoding: corrupt unused data, not executable behavior."""
import hashlib,json,pathlib,runpy,struct,subprocess
ROOT=pathlib.Path(__file__).resolve().parent.parent
BIN=ROOT/'target/ligature';OUT=ROOT/'target/evidence/relocation-witness';OUT.mkdir(parents=True,exist_ok=True)
differ=runpy.run_path(str(ROOT/'tools/differ'));snapshot=differ['snapshot']
def call(args):
    p=subprocess.run(list(map(str,args)),capture_output=True,timeout=120)
    assert p.returncode==0,(args,p.returncode,p.stderr)
    return p
source=OUT/'site.s';obj=OUT/'site.o'
source.write_text('''.text
.global _start
_start: mov $60,%eax
 xor %edi,%edi
 syscall
.local entry_label
.set entry_label,_start
.data
.global pointer,target
pointer: .quad target
.long target-.
target: .quad 41
.section .debug_probe,"",@progbits
.quad target
.section .note.GNU-stack,"",@progbits
''')
call(['as','--64','-g',source,'-o',obj])
rows=[]
for label,linker in [('ligature',BIN),('lld','ld.lld-17'),('gnu','ld.bfd')]:
    path=OUT/label
    call([linker,*(['-nostdlib'] if label=='ligature' else ['--emit-relocs']),'-static','-o',path,obj])
    view=snapshot(path)
    assert not view['refused'],(label,view['refused'])
    assert len(view['relocations'])>=3,(label,'missing retained sites')
    data=bytearray(path.read_bytes());shoff=struct.unpack_from('<Q',data,40)[0]
    n,ns=struct.unpack_from('<HH',data,60)
    heads=[struct.unpack_from('<IIQQQQIIQQ',data,shoff+64*i) for i in range(n)]
    names=data[heads[ns][4]:heads[ns][4]+heads[ns][5]]
    sections={bytes(names[h[0]:]).split(b'\0',1)[0].decode():h for h in heads}
    for section in ('.data','.debug_probe'):
        mutated=bytearray(data);mutated[sections[section][4]]^=1
        # Re-seal so the relocation gate, rather than the digest gate, must fail.
        if '.note.wolf.link' in sections:
            no=sections['.note.wolf.link'][4];mo=sections['.wolf.link.manifest']
            mutated[no+44:no+108]=bytes(64)
            whole=hashlib.sha256(mutated).digest()
            mutated[no+44:no+76]=hashlib.sha256(mutated[mo[4]:mo[4]+mo[5]]).digest()
            mutated[no+76:no+108]=whole
        bad=OUT/(label+'-'+section[1:]+'-bad');bad.write_bytes(mutated);bad.chmod(0o755)
        assert call([bad]).stdout==b'' # no behavioral witness can catch this byte
        broken=snapshot(bad)
        assert any(r['reason']=='resolved relocation bytes differ' for r in broken['refused']),(label,section,broken['refused'])
    rows.append({'linker':label,'sites':len(view['relocations']),'entry':view['entry']})
assert rows[0]['entry']==rows[1]['entry']==rows[2]['entry']=={'symbols':['_start'],'offset':0},rows
identity=differ['address_identity']
base={'name':'entry','section':1,'type':2,'binding':1,'value':100,'size':4}
local={**base,'name':'.Ldebug','binding':0}
assert identity(100,[base],[])==identity(100,[base,local],[])
assert identity(100,[base],[])!=identity(100,[{**base,'name':'other'}],[])
assert identity(100,[base],[])!=identity(101,[base],[])
# An arbitrary zero in live debug data must not be accepted as a tombstone.
(OUT/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
print('relocation-witness: three linkers, retained sites, unused data/debug corruption red, local/entry normalization; 0 SKIP')
# The writer's four TLS models and strong/weak/COMMON cases retain independently
# decodable output sites, including relaxed instructions and consumed call pairs.
for case in json.loads((ROOT/'target/evidence/writer/results.json').read_text()):
    path=ROOT/'target/evidence/writer'/(case['case']+'-ligature')
    view=snapshot(path,execute=False)
    assert not view['refused'],(case['case'],view['refused'][:4])
    assert view['relocations'],(case['case'],'no retained relocation sites')
print('relocation-witness: all writer cases independently decoded, including four TLS models; 0 SKIP')
