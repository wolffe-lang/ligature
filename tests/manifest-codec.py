"""Independent v2 binary-table reader/writer used only by test witnesses."""
import json, struct
MAGIC=b'WLPATCH2'
KEYS=('addend','after','before','consumed_by','end','index','member','offset','rule','section_index','start','symbol','target_member','target_symbol','type')
STRINGS={1,2,8,11}
def uint(n):
    assert 0 <= n < 1<<64
    out=bytearray()
    while n>=128: out.append((n&127)|128); n>>=7
    out.append(n);return out

def encode(doc, size=None):
    meta=dict(doc); rows=meta.pop('patches');meta.pop('zz_padding',None)
    meta['patches']=[]
    metadata=json.dumps(meta,sort_keys=True,separators=(',',':')).encode()
    pool=[];ids={};table=bytearray();previous=[0]*15
    for row in rows:
        vals=[]
        for i,k in enumerate(KEYS):
            v=row[k]
            if i in STRINGS:
                if v not in ids: ids[v]=len(pool);pool.append(v)
                v=ids[v]
            if k=='end':v-=row['start']
            vals.append(v)
        diffs=[v if i==0 else v-previous[i] for i,v in enumerate(vals)]
        mask=sum(1<<i for i,v in enumerate(diffs) if v)
        table+=struct.pack('<H',mask)
        for d in diffs:
            if d:table+=uint(2*d if d>=0 else -2*d-1)
        previous=vals
    strings=bytearray()
    for s in pool:
        b=s.encode();strings+=uint(len(b));strings+=b
    raw=MAGIC+struct.pack('<QQQQ',len(metadata),len(pool),len(rows),len(table))+metadata+strings+table
    if size is None:size=(len(raw)+4095)//4096*4096
    assert len(raw)<=size,(len(raw),size)
    return raw+bytes(size-len(raw))

def decode(raw):
    if not raw.startswith(MAGIC):return json.loads(raw)
    m,p,n,t=struct.unpack_from('<QQQQ',raw,8);at=40+m
    doc=json.loads(raw[40:at]);pool=[]
    def read():
        nonlocal at
        v=0
        for shift in range(0,70,7):
            b=raw[at];at+=1
            assert shift!=63 or b<=1
            v|=(b&127)<<shift
            if b<128:
                assert shift==0 or b!=0
                return v
        raise AssertionError('overlong varint')
    for _ in range(p):
        length=read();pool.append(raw[at:at+length].decode());at+=length
    end=at+t;rows=[];previous=[0]*15
    for _ in range(n):
        mask=struct.unpack_from('<H',raw,at)[0];at+=2;assert mask<32768
        vals=[]
        for i in range(15):
            z=read() if mask&(1<<i) else 0;d=(z>>1)^-(z&1)
            vals.append(d if i==0 else previous[i]+d)
        row={k:(pool[vals[i]] if i in STRINGS else vals[i]) for i,k in enumerate(KEYS)}
        row['end']+=row['start'];rows.append(row);previous=vals
    assert at==end and not any(raw[at:])
    assert doc['patches']==[];doc['patches']=rows
    return doc
