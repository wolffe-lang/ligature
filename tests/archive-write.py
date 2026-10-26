#!/usr/bin/env python3
"""Independent ar index/bytes oracle and actual lazy links by three linkers."""
import hashlib, json, pathlib, struct, subprocess
ROOT=pathlib.Path(__file__).resolve().parent.parent
OUT=ROOT/'target/evidence/archive-write'; OUT.mkdir(parents=True,exist_ok=True)
BIN=ROOT/'target/ligature'; rows=[]
def run(args, status=0, reason=None):
    p=subprocess.run(list(map(str,args)),capture_output=True,timeout=60)
    assert p.returncode==status,(args,p.returncode,p.stdout,p.stderr)
    if reason: assert reason.encode() in p.stderr,(args,p.stderr)
    rows.append({'argv':list(map(str,args)),'status':p.returncode,'stdout':p.stdout.decode(errors='replace'),'stderr':p.stderr.decode(errors='replace')})
    return p.stdout

def assemble(directory, name, code):
    directory.mkdir(exist_ok=True)
    s=directory/(name+'.s'); o=directory/name
    s.write_text(code+'\n.section .note.GNU-stack,"",@progbits\n')
    run(['as','--64',s,'-o',o]);return o
first=assemble(OUT/'one','same long member name.o','.text\n.global choice\nchoice: mov $7,%eax; ret\n.weak weak_export\nweak_export: ret\n.comm common_export,16,16\n.local local_export\nlocal_export: ret')
second=assemble(OUT/'two','same long member name.o','.text\n.global unused\nunused: mov $99,%eax; ret\n.global choice\nchoice: mov $99,%eax; ret')
entry=assemble(OUT,'entry.o','.text\n.global _start\n_start: call choice; mov %eax,%edi; mov $60,%eax; syscall')
archive=OUT/'libcreated.a'; repeat=OUT/'repeat.a'
run([BIN,'archive',archive,first,second]); run([BIN,'archive',repeat,first,second])
assert archive.read_bytes()==repeat.read_bytes(),'archive nondeterminism'
# Parse the archive independently, including index target header identities.
b=archive.read_bytes(); assert b[:8]==b'!<arch>\n';members=[];at=8
while at<len(b):
    h=b[at:at+60];assert len(h)==60 and h[-2:]==b'`\n'
    assert int(h[16:28])==int(h[28:34])==int(h[34:40])==0
    assert int(h[40:48],8)==0o644
    n=int(h[48:58]);payload=b[at+60:at+60+n];assert len(payload)==n
    members.append((at,h[:16].rstrip(),payload))
    if n%2: assert b[at+60+n:at+61+n]==b'\n'
    at+=60+n+n%2
assert at==len(b) and len(members)==4
idx=members[0][2];count=struct.unpack_from('>I',idx)[0]
offsets=struct.unpack_from('>'+str(count)+'I',idx,4)
names=idx[4+4*count:].split(b'\0');assert names.pop()==b''
expected=[(b'choice',members[2][0]),(b'weak_export',members[2][0]),(b'common_export',members[2][0]),(b'unused',members[3][0]),(b'choice',members[3][0])]
assert list(zip(names,offsets))==expected,(names,offsets,expected)
assert members[2][2]==first.read_bytes() and members[3][2]==second.read_bytes()
longnames=members[1][2]
assert [longnames[int(m[1][1:]):].split(b'/\n',1)[0] for m in members[2:]]==[first.name.encode(),second.name.encode()]
assert run(['ar','t',archive]).decode().splitlines()==[first.name,second.name]
run(['nm','--print-armap',archive]);run([BIN,'roundtrip',archive])
# Link and execute: duplicate basename must not collapse to the wrong member;
# the unused duplicate definition must not be extracted by the lazy link.
for name,ld in [('ligature',BIN),('lld','ld.lld-17'),('gnu','ld.bfd')]:
    output=OUT/name;args=[ld,'-static','-o',output,entry,archive]
    if name=='ligature':args.insert(1,'-nostdlib')
    run(args);run([output],7)
    if name=='ligature':run([BIN,'verify',output])
# GNU's archive is a behavioral control, not a byte-layout requirement.
control=OUT/'gnu.a'
if control.exists(): control.unlink()
run(['ar','rcsD',control,first,second]);run([BIN,'-nostdlib','-o',OUT/'control',entry,control]);run([OUT/'control'],7)
local=assemble(OUT,'local.o','.text\nlocal: ret')
run([BIN,'archive',OUT/'no-global.a',local]);run([BIN,'roundtrip',OUT/'no-global.a']);run(['ar','t',OUT/'no-global.a'])
# Every refusal preserves an existing output, including a bad later input.
sentinel=OUT/'sentinel.a';sentinel.write_bytes(b'unchanged')
invalid=OUT/'invalid.o';invalid.write_bytes(b'not elf')
for args,reason in [([sentinel,first,invalid],'truncated'),([sentinel,archive],'not ELF'),([sentinel,OUT/'gnu'],'ET_REL'),([first,first],'output names an input')]:
    run([BIN,'archive',*args],1,reason)
    assert sentinel.read_bytes()==b'unchanged'
run([BIN,'archive'],1,'usage')
# Header-only AArch64 is enough to witness mixed-machine refusal, never linking.
foreign=OUT/'foreign.o';raw=bytearray(local.read_bytes());struct.pack_into('<H',raw,18,183);foreign.write_bytes(raw)
run([BIN,'archive',sentinel,first,foreign],1,'mixed ELF machines');assert sentinel.read_bytes()==b'unchanged'
for name,magic in [('thin.a',b'!<thin>\n'),('bsd.a',b'!<arch>\n'+b'#1/8'.ljust(16)+b'0'.ljust(12)+b'0'.ljust(6)+b'0'.ljust(6)+b'644'.ljust(8)+b'8'.ljust(10)+b'`\nabcdefgh')]:
    path=OUT/name;path.write_bytes(magic);run([BIN,'roundtrip',path],1,'thin archives' if name=='thin.a' else 'BSD archives')
(OUT/'results.json').write_text(json.dumps({'archive_sha256':hashlib.sha256(b).hexdigest(),'index':[(n.decode(),o) for n,o in expected],'rows':rows},indent=2)+'\n')
print(f'archive-write: {len(rows)} process rows, deterministic bytes and independent index; three executed links, 0 SKIP')
