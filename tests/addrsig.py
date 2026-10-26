#!/usr/bin/env python3
"""Published LLVM ADDRSIG format, validated before explicit exclusion; no ICF."""
import pathlib,struct,subprocess
R=pathlib.Path(__file__).resolve().parent.parent;O=R/'target/evidence/addrsig';O.mkdir(parents=True,exist_ok=True);B=R/'target/ligature'
s=O/'index.s';s.write_text('.text\n.global _start\n_start: ret\n.section .llvm_addrsig,"e",@progbits\n.byte 1\n.section .note.GNU-stack,"",@progbits\n')
subprocess.run(['as','--64',s,'-o',O/'index.o'],check=True)
b=bytearray((O/'index.o').read_bytes());off=struct.unpack_from('<Q',b,40)[0];n,ns=struct.unpack_from('<HH',b,60);sh=[struct.unpack_from('<IIQQQQIIQQ',b,off+64*i) for i in range(n)];pool=b[sh[ns][4]:sh[ns][4]+sh[ns][5]]
i=next(i for i,x in enumerate(sh) if pool[x[0]:].split(b'\0',1)[0]==b'.llvm_addrsig');sym=next(i for i,x in enumerate(sh) if x[1]==2)
struct.pack_into('<I',b,off+i*64+4,1879002115);struct.pack_into('<I',b,off+i*64+40,sym)
def check(name,data,reason=None):
 path=O/(name+'.o');path.write_bytes(data)
 p=subprocess.run([B,'roundtrip',path],capture_output=True);assert p.returncode==(1 if reason else 0),(name,p.stderr)
 if reason:assert reason.encode() in p.stderr,(name,p.stderr)
 else:
  p=subprocess.run([B,'-nostdlib','-o',O/name,path],capture_output=True);assert p.returncode==0,p.stderr
check('valid',b)
bad=bytearray(b);bad[sh[i][4]]=128;check('unterminated',bad,'truncated LLVM_ADDRSIG')
bad=bytearray(b);bad[sh[i][4]]=127;check('out-of-table',bad,'symbol index outside')
bad=bytearray(b);struct.pack_into('<I',bad,off+i*64+40,0);check('bad-link',bad,'symbol table link')
bad=bytearray(b);struct.pack_into('<Q',bad,off+i*64+8,0);check('not-excluded',bad,'nonexcluded')
print('addrsig: valid symbol index consumed without folding; four malformed forms refused; 0 SKIP')
