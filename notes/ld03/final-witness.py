#!/usr/bin/env python3
import hashlib,json,pathlib,struct,subprocess,time
root=pathlib.Path('/lane/ligature');base=root.parent;corpus=root/'target/static-pax'
rows=json.loads((corpus/'results.json').read_text())['rows'];ascii_rows=[]
for row in rows:
 p=corpus/row['case']/'program';b=p.read_bytes();assert hashlib.sha256(b).hexdigest()==row['sha256'];sh=struct.unpack_from('<Q',b,40)[0];n,ns=struct.unpack_from('<HH',b,60);hs=[struct.unpack_from('<IIQQQQIIQQ',b,sh+64*i) for i in range(n)];h=hs[ns];names=b[h[4]:h[4]+h[5]];m=next(h for h in hs if names[h[0]:].split(b'\0',1)[0]==b'.wolf.link.manifest');raw=b[m[4]:m[4]+m[5]];assert raw[:8]==b'WLPATCH2';metadata,strings,_,_=struct.unpack_from('<QQQQ',raw,8);at=40+metadata
 for _ in range(strings):
    length=0;shift=0
    while True:
        x=raw[at];at+=1;length|=(x&127)<<shift
        if x<128:break
        shift+=7
    assert raw[at:at+length].isascii(),row['case'];at+=length
 ascii_rows.append({'case':row['case'],'sha256':row['sha256'],'all_pooled_strings_ascii':True})
expected=next(r['sha256'] for r in rows if r['case']=='hello-hello');args=json.loads((corpus/'hello-hello/link1.command.json').read_text())['argv'];out=root/'target/final-hello';args[args.index('-o')+1]=str(out);times=[]
for i in (1,2):
 print('FINAL HELLO LINK',i,flush=True);start=time.monotonic();subprocess.run(args,check=True);times.append(time.monotonic()-start);sha=hashlib.sha256(out.read_bytes()).hexdigest();assert sha==expected,(sha,expected);print('FINAL HELLO MATCH',i,sha,flush=True)
subprocess.run([root/'target/ligature','verify',out],check=True)
subprocess.run([out],check=True)
(root/'notes/ld03/evidence/final-byte-name-witness.json').write_text(json.dumps({'reason':'Only non-ASCII name conversion changed after the full corpus; all fourteen qualified pools are ASCII. Two final-source hello links reproduce the qualified binary byte-for-byte. Final core includes an arbitrary-byte-name regression.','ascii_corpus':ascii_rows,'hello_sha256':expected,'final_link_seconds':times},indent=2)+'\n')
