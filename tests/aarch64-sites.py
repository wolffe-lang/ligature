#!/usr/bin/env python3
"""Independent AAELF64 equations over actual output RELA sites, never the manifest."""
import pathlib,struct
MASK=(1<<64)-1
def signed(n,bits):return n-(1<<bits) if n&(1<<(bits-1)) else n

def decode(path):
 b=pathlib.Path(path).read_bytes();assert b[:6]==b'\x7fELF\x02\x01'
 shoff=struct.unpack_from('<Q',b,40)[0];n,ns=struct.unpack_from('<HH',b,60)
 sh=[struct.unpack_from('<IIQQQQIIQQ',b,shoff+64*i) for i in range(n)]
 strings=b[sh[ns][4]:sh[ns][4]+sh[ns][5]]
 names=[strings[s[0]:].split(b'\0',1)[0].decode() for s in sh]
 def read(address,width):
  for s in sh:
   if s[1]!=8 and s[2]&2 and s[3]<=address and address+width<=s[3]+s[5]:return int.from_bytes(b[s[4]+address-s[3]:s[4]+address-s[3]+width],'little')
  raise AssertionError(('unmapped address',hex(address),width))
 rows=[]
 for table in sh:
  if table[1]!=4:continue
  symtab=sh[table[6]];target=sh[table[7]]
  for at in range(table[4],table[4]+table[5],24):
   p,info,a=struct.unpack_from('<QQq',b,at);k=info&0xffffffff
   sym=struct.unpack_from('<IBBHQQ',b,symtab[4]+24*(info>>32));s=sym[4];width=8 if k==257 else 4
   off=target[4]+p-target[3];assert 0<=p-target[3]<=target[5]-width
   word=int.from_bytes(b[off:off+width],'little')
   rows.append({'place':p,'symbol':s,'addend':a,'type':k,'word':word,'section':names[table[7]]})
 return b,sh,names,read,rows

def validate(path,allow_veneers=False):
 b,sh,names,read,rows=decode(path);assert struct.unpack_from('<H',b,18)[0]==183
 def page(word,p):
  assert word&0x9f000000==0x90000000
  imm=((word>>29)&3)|(((word>>5)&0x7ffff)<<2)
  return (p&~4095)+(signed(imm,21)<<12)
 for r in rows:
  p,s,a,k,w=[r[x] for x in ('place','symbol','addend','type','word')];sa=s+a
  if k==257:assert w==(sa&MASK),r
  elif k==261:assert -2**31<=sa-p<2**32 and w==(sa-p)&0xffffffff,r
  elif k in (282,283):
   assert w&0xfc000000==(0x94000000 if k==283 else 0x14000000),r
   destination=p+signed(w&0x3ffffff,26)*4
   if destination!=sa and allow_veneers:
    assert read(destination,4)==0x58000050 and read(destination+4,4)==0xd61f0200,r
    assert read(destination+8,8)==sa&MASK,r
    r['oracle_veneer']='LDR x16 literal; BR x16; exact target literal'
   else:assert destination==sa,r
  elif k==275:assert page(w,p)==sa&~4095,r
  elif k==277:assert w&0x7fc00000==0x11000000 and (w>>10)&4095==sa&4095,r
  elif k==286:assert w&0xffc00000 in (0xf9000000,0xf9400000) and ((w>>10)&4095)*8==sa&4095,r
  elif k==311:
   low=read(p+4,4);assert low&0xffc00000==0xf9400000
   got=page(w,p)+((low>>10)&4095)*8;assert read(got,8)==s and a==0,r
  elif k==312:
   got=page(read(p-4,4),p-4)+((w>>10)&4095)*8
   assert w&0xffc00000==0xf9400000 and read(got,8)==s and a==0,r
  else:raise AssertionError(('unknown relocation',r))
 return rows
