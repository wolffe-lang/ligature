#!/usr/bin/env python3
"""Independent binary fixtures and external compiler/linker tests; no source imports."""
import json, os, pathlib, struct, subprocess, tempfile
ROOT=pathlib.Path(__file__).resolve().parent.parent
BIN=ROOT/'target/ligature'; OUT=ROOT/'target/evidence';OUT.mkdir(parents=True,exist_ok=True)
rows=[]
def run(args, status=0, contains=None):
    p=subprocess.run(list(map(str,args)),capture_output=True,timeout=30)
    assert p.returncode==status,(args,p.returncode,p.stdout,p.stderr)
    if contains is not None: assert contains.encode() in p.stderr,(args,p.stderr)
    rows.append({'argv':list(map(str,args)),'status':p.returncode,'stdout':p.stdout.decode(errors='replace'),'stderr':p.stderr.decode(errors='replace')})
    return p

def header(machine=62, kind=1):
    return bytearray(b'\x7fELF\x02\x01\x01'+bytes(9)+struct.pack('<HHIQQQIHHHHHH',kind,machine,1,0,0,0,0,64,56,0,64,0,0))

with tempfile.TemporaryDirectory(dir=OUT,prefix='fixture-') as tmp:
    d=pathlib.Path(tmp)
    def bad(name,data,reason):
        p=d/name;p.write_bytes(data);run([BIN,'inspect',p],1,reason)
    empty=d/'empty.o';empty.write_bytes(header());run([BIN,'roundtrip',empty])
    # SHT_NOBITS has a conceptual file offset, which may exceed EOF.
    raw=header();struct.pack_into('<Q',raw,40,64);struct.pack_into('<H',raw,60,2)
    raw.extend(bytes(64));raw.extend(struct.pack('<IIQQQQIIQQ',0,8,3,0,65536,16,0,0,16,0))
    nobits=d/'nobits.o';nobits.write_bytes(raw);run([BIN,'roundtrip',nobits])
    aarch=d/'aarch.o';aarch.write_bytes(header(183));run([BIN,'roundtrip',aarch]);run([BIN,'-nostdlib',aarch],1,'undefined entry _start')
    for n in (0,1,7,8,15,16,63):bad('short'+str(n),header()[:n],'truncated range')
    b=header();b[4]=1;bad('elf32',b,'ELFCLASS32')
    b=header();b[5]=2;bad('big-endian',b,'ELFDATA2MSB')
    b=header(3);bad('machine',b,'e_machine')
    b=header();struct.pack_into('<Q',b,40,2**64-1);bad('offset-overflow',b,'offset exceeds')
    b=header();struct.pack_into('<Q',b,40,64);struct.pack_into('<H',b,60,2);bad('section-truncated',b,'truncated range')
    bad('thin.a',b'!<thin>\n','thin archives')
    def ar_member(name,body):
        h=f'{name:<16}{0:<12}{0:<6}{0:<6}{0:<8}{len(body):<10}`\n'.encode()
        assert len(h)==60
        return h+body+(b'\n' if len(body)%2 else b'')
    bad('bsd.a',b'!<arch>\n'+ar_member('#1/8',b'abcdefgh'),'BSD archives')
    bad('bad-long.a',b'!<arch>\n'+ar_member('/300',header()),'long-name offset')
    bad('bad-index.a',b'!<arch>\n'+ar_member('/',struct.pack('>II',1,999)+b'x\0'),'member header')
    source=d/'fixture.c';source.write_text('static int state; __thread int tls=7; int main(void) { return state+tls-7; }\n')
    obj=d/'member-with-a-very-long-name.o'
    run(['cc','-c','-ffunction-sections','-fdata-sections',source,'-o',obj])
    run([BIN,'roundtrip',obj]);run(['ar','rcs',d/'long.a',obj]);run([BIN,'roundtrip',d/'long.a'])
    inspected=[json.loads(x) for x in run([BIN,'inspect',obj]).stdout.splitlines()]
    assert any(x.get('row')=='section' and x['flags']&1024 for x in inspected)
    for linker in ('bfd','lld'):
        exe=d/('exe-'+linker)
        run(['cc',f'-fuse-ld={linker}',source,'-o',exe])
        run([BIN,'verify',exe])
        b=bytearray(exe.read_bytes());struct.pack_into('<Q',b,24,1)
        corrupt=d/('bad-entry-'+linker);corrupt.write_bytes(b)
        run([BIN,'verify',corrupt],1,'entry outside executable')
    # Mutations of an actual object cover symbol/string/relocation/group metadata.
    original=obj.read_bytes();shoff=struct.unpack_from('<Q',original,40)[0];shnum=struct.unpack_from('<H',original,60)[0]
    types={struct.unpack_from('<I',original,shoff+i*64+4)[0]:i for i in range(shnum)}
    if 4 in types:
        b=bytearray(original);struct.pack_into('<I',b,shoff+types[4]*64+4,9);bad('rel.o',b,'SHT_REL')
        b=bytearray(original);off=struct.unpack_from('<Q',b,shoff+types[4]*64+24)[0];struct.pack_into('<Q',b,off+8,0xffffffff00000002);bad('rel-symbol.o',b,'symbol index')
    b=bytearray(original);struct.pack_into('<I',b,shoff+64+4,123456);bad('unknown-section.o',b,'unknown section type')
    sym=types[2];symoff=struct.unpack_from('<Q',original,shoff+sym*64+24)[0]
    b=bytearray(original);struct.pack_into('<H',b,symoff+24+6,40000);bad('symbol-section.o',b,'section index')
    b=bytearray(original);struct.pack_into('<I',b,symoff+24,0xffffffff);bad('symbol-name.o',b,'string index')
    b=bytearray(original);struct.pack_into('<Q',b,shoff+64+48,3);bad('align.o',b,'power of two')
    args=['--print-plan','-o','a b','x.o','rt.a','-lpthread','-ldl','-lm','-Wl,--gc-sections','-Wl,--undefined=__wolf_rt_trap_at','-Wl,--defsym=wolf_trap=__wolf_rt_trap_at','-fuse-ld=lld','-static','-nostdlib','-L','/lib','-l','c']
    p=json.loads(run([BIN,*args]).stdout);assert p['output']=='a b' and p['static'] and p['nostdlib'] and p['libraries']==['pthread','dl','m','c']
    for args,reason in [(['-o'],'missing value'),(['--unknown','x.o'],'unsupported cc'),(['-Wl,--surprise','x.o'],'unsupported linker'),(['-Wl,--defsym=a','x.o'],'NAME=SYMBOL'),(['-nostdlib','x.o'],'cannot stat x.o')]:run([BIN,*args],1,reason)
(OUT/'integration.json').write_text(json.dumps(rows,indent=2)+'\n')
print(f'integration: {len(rows)} process rows, 0 SKIP')

# New commands run in the existing native integration gate, never as optional rows.
for suite in ("script-profile.py", "archive-write.py", "kernel-script.py", "aarch64.py", "addrsig.py"):
    subprocess.run(["python3", "-I", ROOT / "tests" / suite], check=True)
