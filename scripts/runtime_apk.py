"""Version-gated Android shell edits for the EN runtime build.

Preserve resource IDs and Java class namespaces. Change the application identity,
add a pre-Unity bootstrap activity, and refresh DEX checksums after the one
BuildConfig application ID replacement. No global find/replace across the APK.
"""
import hashlib
import struct
import zlib

OLD = 'com.LanPiaoPiao.PlantsVsZombiesRH'
NEW = 'com.LanPiaoPiao.PlantsVsZombiesEN'
BOOT = 'com.silvershadow.pvzf.EnglishActivity'
UNITY = 'com.unity3d.player.UnityPlayerActivity'
APPLICATION = 'com.silvershadow.pvzf.EnglishApplication'
U32 = lambda b, p: struct.unpack_from('<I', b, p)[0]


def chunks(data, start=8):
    p = start
    while p < len(data):
        kind, header, size = struct.unpack_from('<HHI', data, p)
        if size < header or p + size > len(data):
            raise ValueError('Invalid Android resource chunk')
        yield p, kind, header, bytearray(data[p:p+size])
        p += size
    assert p == len(data)


class Pool:
    def __init__(self, raw):
        self.raw = raw
        _, self.header, _ = struct.unpack_from('<HHI', raw)
        self.count, self.style_count, self.flags, start, styles = struct.unpack_from('<IIIII', raw, 8)
        self.strings = []
        self.style_offsets = raw[self.header+4*self.count:self.header+4*(self.count+self.style_count)]
        self.styles = raw[styles:] if styles else b''
        def length(p, width):
            if width == 1:
                n=raw[p];p+=1
                if n&128:n=((n&127)<<8)|raw[p];p+=1
            else:
                n=struct.unpack_from('<H',raw,p)[0];p+=2
                if n&32768:n=((n&32767)<<16)|struct.unpack_from('<H',raw,p)[0];p+=2
            return n,p
        for i in range(self.count):
            p=start+U32(raw,self.header+4*i)
            if self.flags&256:
                _,p=length(p,1);n,p=length(p,1);s=raw[p:p+n].decode('utf-8')
            else:
                n,p=length(p,2);s=raw[p:p+2*n].decode('utf-16le')
            self.strings.append(s)

    def add(self, text):
        if text not in self.strings:self.strings.append(text)
        return self.strings.index(text)

    def encode(self):
        body=bytearray();offsets=[]
        def length(n,width):
            if width==1:return bytes([n]) if n<128 else bytes([(n>>8)|128,n&255])
            return struct.pack('<H',n) if n<32768 else struct.pack('<HH',(n>>16)|32768,n&65535)
        for s in self.strings:
            offsets.append(len(body));utf16=s.encode('utf-16le')
            if self.flags&256:
                b=s.encode('utf-8');body+=length(len(utf16)//2,1)+length(len(b),1)+b+b'\0'
            else:body+=length(len(utf16)//2,2)+utf16+b'\0\0'
        body+=b'\0'*(-len(body)%4)
        header=bytearray(self.raw[:self.header]);start=self.header+len(offsets)*4+len(self.style_offsets)
        # Appending strings invalidates SORTED_FLAG, while existing indices stay stable.
        struct.pack_into('<IIIII',header,8,len(offsets),self.style_count,self.flags&~1,start,start+len(body) if self.styles else 0)
        result=header+struct.pack('<'+'I'*len(offsets),*offsets)+self.style_offsets+body+self.styles
        struct.pack_into('<I',result,4,len(result));return result


def application_bootstrap(data):
    """Register startup for restored Activities as well as launcher entry."""
    parts=list(chunks(data));pool=Pool(next(b for _,k,_,b in parts if k==1))
    def text(i):return '' if i==0xffffffff else pool.strings[i]
    app=None;template=None
    for _,kind,_,b in parts:
        if kind!=0x102:continue
        tag=text(U32(b,20));start,size,count=struct.unpack_from('<HHH',b,24)
        assert size==20
        if tag=='application':app=b
        for i in range(count):
            pos=16+start+i*size
            if text(U32(b,pos+4))=='name' and tag=='activity':template=bytearray(b[pos:pos+size])
    assert app is not None and template is not None
    start,size,count=struct.unpack_from('<HHH',app,24)
    for i in range(count):
        pos=16+start+i*size
        if text(U32(app,pos+4))=='name':
            assert text(U32(app,pos+16))==APPLICATION,'Review an existing custom Application first'
            return data
    index=pool.add(APPLICATION)
    struct.pack_into('<I',template,8,index);template[15]=3;struct.pack_into('<I',template,16,index)
    end=16+start+size*count;assert end==len(app)
    resource_map=next(b for _,k,_,b in parts if k==0x180)
    resource_ids=struct.unpack('<'+'I'*((len(resource_map)-8)//4),resource_map[8:])
    def resource_id(attribute):
        key=U32(attribute,4)
        return resource_ids[key] if key<len(resource_ids) else 0
    assert resource_id(template)==0x01010003,'Expected the existing android:name attribute ID'
    attributes=[bytearray(app[16+start+i*size:16+start+(i+1)*size]) for i in range(count)]
    assert [resource_id(a) for a in attributes]==sorted(resource_id(a) for a in attributes)
    # Android's TypedArray lookup requires resource-ID order. Merely appending
    # android:name can make PackageManager silently ignore the Application.
    position=next((i for i,a in enumerate(attributes) if resource_id(a)>resource_id(template)),count)
    attributes.insert(position,template)
    app[:]=app[:16+start]+b''.join(attributes)
    struct.pack_into('<I',app,4,len(app));struct.pack_into('<H',app,28,count+1)
    for offset in (30,32,34):
        index=struct.unpack_from('<H',app,offset)[0]
        if index>position:struct.pack_into('<H',app,offset,index+1)
    body=b''.join(pool.encode() if k==1 else bytes(b) for _,k,_,b in parts)
    header=bytearray(data[:8]);struct.pack_into('<I',header,4,len(body)+8)
    return bytes(header)+body


def manifest(data, version_code, version_name='4.0.5-English-pre3'):
    parts=list(chunks(data));pool=Pool(next(x[3] for x in parts if x[1]==1))
    def text(i):return '' if i==0xffffffff else pool.strings[i]
    def tag(b):return text(U32(b,20))
    def attrs(b):
        start,size,n=struct.unpack_from('<HHH',b,24)
        for i in range(n):
            p=16+start+i*size;yield text(U32(b,p+4)),p
    def set_attr(b,key,value,typ=3):
        for name,p in attrs(b):
            if name==key:
                n=pool.add(value) if typ==3 else value
                struct.pack_into('<I',b,p+8,n if typ==3 else 0xffffffff)
                b[p+15]=typ;struct.pack_into('<I',b,p+16,n);return
        raise ValueError('Expected manifest attribute missing: '+key)
    activity_start=activity_end=None;depth=0
    for index,(_,kind,_,b) in enumerate(parts):
        if kind==0x102:
            t=tag(b)
            if t=='manifest':
                assert any(name=='package' and text(U32(b,p+16))==OLD for name,p in attrs(b))
                set_attr(b,'package',NEW);set_attr(b,'versionCode',version_code,0x10)
                set_attr(b,'versionName',version_name)
            if t=='application':set_attr(b,'label','PvZ Fusion English')
            if t=='activity':
                assert activity_start is None, 'Review a shell with multiple activities'
                assert any(name=='name' and text(U32(b,p+16))==UNITY for name,p in attrs(b))
                activity_start=index
            if activity_start is not None and activity_end is None:depth+=1
        elif kind==0x103 and activity_start is not None and activity_end is None:
            depth-=1
            if depth==0:activity_end=index
    assert activity_start is not None and activity_end is not None
    original=[bytearray(p[3]) for p in parts[activity_start:activity_end+1]]
    bootstrap=[bytearray(b) for b in original]
    set_attr(bootstrap[0],'name',BOOT);set_attr(bootstrap[0],'launchMode',0,0x10)
    set_attr(original[0],'exported',0,0x12)
    # Keep the launcher intent only on bootstrap, so every normal launch verifies metadata first.
    filtered=[];skip=0
    for b in original:
        kind=struct.unpack_from('<H',b)[0]
        if kind==0x102 and (skip or tag(b)=='intent-filter'):skip+=1;continue
        if skip:
            if kind==0x103:skip-=1
            continue
        filtered.append(b)
    result=bytearray(data[:8])
    for i,(_,kind,_,b) in enumerate(parts):
        if i==activity_start:result+=b''.join(bootstrap+filtered)
        if activity_start<=i<=activity_end:continue
        result+=pool.encode() if kind==1 else b
    struct.pack_into('<I',result,4,len(result));return application_bootstrap(bytes(result))


def resources(data):
    output=bytearray(data);hits=0
    for pos,kind,header,chunk in chunks(data,12):
        if kind==0x200:
            package=bytes(chunk[12:268]).decode('utf-16le').split('\0')[0]
            if package==OLD:
                output[pos+12:pos+268]=NEW.encode('utf-16le').ljust(256,b'\0');hits+=1
    assert hits==1, f'Expected one resource package, got {hits}'
    return bytes(output)


def dex_application_id(data):
    assert data.startswith(b'dex\n')
    # Equal byte length: string IDs and instruction offsets remain unchanged.
    needle=b'\0'+OLD.encode()+b'\0'
    # DEX string data has a ULEB128 length immediately before the text.
    needle=bytes([len(OLD)])+OLD.encode()+b'\0'
    assert data.count(needle)==1, 'Unexpected BuildConfig application identity count'
    result=bytearray(data.replace(needle,bytes([len(NEW)])+NEW.encode()+b'\0'))
    result[12:32]=hashlib.sha1(result[32:]).digest()
    struct.pack_into('<I',result,8,zlib.adler32(result[12:])&0xffffffff)
    return bytes(result)
