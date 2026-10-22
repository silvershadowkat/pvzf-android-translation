"""Local-only optional AI APK, layered on the exact published prerelease 3.

All gameplay objects, translations, metadata and original game native libraries
are retained. The ENAI prototype has separate app identity and storage.
"""
import argparse, copy, hashlib, json, os, shutil, struct, subprocess, zipfile
from pathlib import Path
from runtime_apk import Pool, chunks, U32
import runtime_apk
from package_apk_payload import copy_entry, is_old_signature

BASE_SHA='9d10eb7b8082ac27b9530a526f9cffb7dcfc0a1e27011e2951054a6a70810b5c'
CERT='1f2552cc7dbfbbbee21d2ea7e77edf371a377902cdcb78ba4f3104e387cd7bc6'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def ai_manifest(data):
    parts=list(chunks(data));pool=Pool(next(b for _,k,_,b in parts if k==1))
    assert pool.strings.count('com.LanPiaoPiao.PlantsVsZombiesEN')==1
    pool.strings[pool.strings.index('com.LanPiaoPiao.PlantsVsZombiesEN')]='com.LanPiaoPiao.PlantsVsZombiesENAI'
    assert 'PvZ Fusion English' in pool.strings
    pool.strings[pool.strings.index('PvZ Fusion English')]='PvZ Fusion English AI'
    ns=pool.add('http://schemas.android.com/apk/res/android');service=pool.add('service')
    ids={'name':0x01010003,'exported':0x01010010,'process':0x01010011,'usesCleartextTraffic':0x010104ec}
    indices={key:pool.add(key) for key in ids}
    resource=next(b for _,k,_,b in parts if k==0x180)
    resources=list(struct.unpack('<'+'I'*((len(resource)-8)//4),resource[8:]))
    while len(resources)<=max(indices.values()):resources.append(0)
    for key,index in indices.items():assert resources[index] in (0,ids[key]);resources[index]=ids[key]
    resource=struct.pack('<HHI',0x180,8,8+len(resources)*4)+struct.pack('<'+'I'*len(resources),*resources)
    def attr(key,value,typ=3):
        v=pool.add(value) if typ==3 else value
        return struct.pack('<IIIHBBI',ns,indices[key],v if typ==3 else 0xffffffff,8,0,typ,v)
    attributes=b''.join([attr('name','com.silvershadow.pvzf.PlantbrushService'),attr('exported',0,0x12),attr('process',':plantbrush')])
    start=struct.pack('<HHIII',0x102,16,36+len(attributes),1,0xffffffff)+struct.pack('<IIHHHHHH',0xffffffff,service,20,20,3,0,0,0)+attributes
    end=struct.pack('<HHIIIII',0x103,16,24,1,0xffffffff,0xffffffff,service)
    inserted=False
    for i,(p,k,h,b) in enumerate(parts):
        if k==0x102 and pool.strings[U32(b,20)]=='manifest':
            offset,size,n=struct.unpack_from('<HHH',b,24)
            for j in range(n):
                at=16+offset+j*size
                if pool.strings[U32(b,at+4)]=='versionName':
                    value=pool.add('4.0.5-English-AI-prototype1');struct.pack_into('<I',b,at+8,value);struct.pack_into('<I',b,at+16,value)
        if k==0x102 and pool.strings[U32(b,20)]=='uses-sdk':
            offset,size,n=struct.unpack_from('<HHH',b,24)
            for j in range(n):
                at=16+offset+j*size
                if pool.strings[U32(b,at+4)]=='minSdkVersion':struct.pack_into('<I',b,at+16,26)
        if k==0x102 and pool.strings[U32(b,20)]=='application':
            offset,size,n=struct.unpack_from('<HHH',b,24)
            assert not any(pool.strings[U32(b,16+offset+j*size+4)]=='usesCleartextTraffic' for j in range(n))
            # Unity's existing localhost request is HTTP. No remote AI URL is added.
            b+=attr('usesCleartextTraffic',0xffffffff,0x12);struct.pack_into('<H',b,28,n+1);struct.pack_into('<I',b,4,len(b))
            parts[i]=(p,k,h,b)
    result=bytearray(data[:8])
    for _,k,_,b in parts:
        if k==0x103 and pool.strings[U32(b,20)]=='application':result+=start+end;inserted=True
        result+=pool.encode() if k==1 else resource if k==0x180 else b
    assert inserted;struct.pack_into('<I',result,4,len(result));return bytes(result)

def main():
    ap=argparse.ArgumentParser()
    for key in ('base','work','pre3-work','output','sdk','jdk','secret'):ap.add_argument('--'+key,type=Path,required=True)
    a=ap.parse_args();r=Path(__file__).resolve().parents[1];w=a.work.resolve();w.mkdir(exist_ok=True,parents=True)
    logs=w/'build';logs.mkdir(exist_ok=True);a.output.mkdir(exist_ok=True,parents=True)
    assert sha(a.base)==BASE_SHA,'Prototype requires the approved prerelease 3'
    def run(name,args,timeout=180,env=None):
        with (logs/(name+'.log')).open('w',encoding='utf-8') as log:p=subprocess.run(list(map(str,args)),stdout=log,stderr=subprocess.STDOUT,timeout=timeout,env=env)
        if p.returncode:raise RuntimeError(name+' failed; '+str(logs/(name+'.log')))
        print(name+' passed',flush=True)
    bt=a.sdk/'build-tools/35.0.0';android=a.sdk/'platforms/android-35/android.jar';ort=w/'ort'
    classes=w/'classes';classes.mkdir(exist_ok=True);dex=w/'dex';dex.mkdir(exist_ok=True)
    run('javac',[a.jdk/'bin/javac.exe','-encoding','UTF-8','-source','8','-target','8','-classpath',os.pathsep.join(map(str,[android,ort/'classes.jar'])),'-d',classes,*sorted((r/'runtime/java').rglob('*.java')),*sorted((r/'runtime/plantbrush/java').rglob('*.java'))],45)
    run('d8',[a.jdk/'bin/java.exe','-cp',bt/'lib/d8.jar','com.android.tools.r8.D8','--release','--min-api','26','--lib',android,'--output',dex,*sorted(classes.rglob('*.class')),ort/'classes.jar'],60)
    assert not (dex/'classes2.dex').exists(),'Review a multidex bridge'
    cm=a.sdk/'cmake/3.22.1/bin/cmake.exe';dobby=a.pre3_work/'Dobby-android'
    for abi in ('arm64-v8a','armeabi-v7a'):
        build=w/('native-'+abi)
        run('configure-'+abi,[cm,'-S',r/'runtime','-B',build,'-G','Ninja','-DCMAKE_MAKE_PROGRAM='+str(a.sdk/'cmake/3.22.1/bin/ninja.exe'),'-DCMAKE_TOOLCHAIN_FILE='+str(a.sdk/'ndk/25.2.9519653/build/cmake/android.toolchain.cmake'),'-DANDROID_ABI='+abi,'-DANDROID_PLATFORM=android-22','-DCMAKE_BUILD_TYPE=Release','-DANDROID_STL=c++_static','-DDOBBY_SOURCE='+str(dobby)],60)
        run('native-'+abi,[cm,'--build',build,'--target','pvzfenglish','--parallel','2'],180)
    assets=w/'assets';manifest=json.loads((assets/'manifest.json').read_text('utf-8'))
    # Use the approved game's names by numeric identity, never invent plant names.
    with zipfile.ZipFile(a.base) as base:
        names={int(x['seedType']):x['name'] for x in json.loads(base.read('assets/english-almanac/LawnStrings.json'))['plants']}
    catalog=json.loads((assets/'catalog.json').read_text('utf-8'));changed_names=0
    for record in catalog:
        name=names.get(record['plantType'])
        if name and not any('\u3400'<=c<='\u9fff' for c in name):record['displayName']=name;changed_names+=1
    (assets/'catalog.json').write_text(json.dumps(catalog,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    manifest['files']['catalog.json']=sha(assets/'catalog.json');manifest['approved_english_names']=changed_names
    (assets/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    for name,digest in manifest['files'].items():assert sha(assets/name)==digest
    runtime_apk.OLD='com.LanPiaoPiao.PlantsVsZombiesEN';runtime_apk.NEW=runtime_apk.OLD+'AI'
    with zipfile.ZipFile(a.base) as base:(w/'ai-resources.arsc').write_bytes(runtime_apk.resources(base.read('resources.arsc')))
    identity=json.loads((w/'identity-unity-audit.json').read_text());assert identity['only_player_settings_changed']
    replacements={'classes2.dex':dex/'classes.dex','classes.dex':w/'ai-classes.dex','resources.arsc':w/'ai-resources.arsc','assets/bin/Data/data.unity3d':w/'identity-ai.unity3d'}
    for abi in ('arm64-v8a','armeabi-v7a'):
        replacements['lib/'+abi+'/libpvzfenglish.so']=w/('native-'+abi)/'libpvzfenglish.so'
        for p in (ort/'jni'/abi).glob('*.so'):replacements['lib/'+abi+'/'+p.name]=p
    for p in sorted(assets.iterdir()):
        if p.is_file():replacements['assets/plantbrush/'+p.name]=p
    unsigned=logs/'unsigned.apk'
    with zipfile.ZipFile(a.base) as base,zipfile.ZipFile(unsigned,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=3) as target:
        for info in base.infolist():
            if is_old_signature(info.filename):continue
            if info.filename=='AndroidManifest.xml':target.writestr(copy.copy(info),ai_manifest(base.read(info)))
            elif info.filename in replacements:target.write(replacements[info.filename],info.filename,compress_type=info.compress_type)
            else:copy_entry(base,target,info)
        for name,p in replacements.items():
            if name not in base.namelist():target.write(p,name)
    print('Prototype assembled',flush=True)
    aligned=logs/'aligned.apk';run('align',[bt/'zipalign.exe','-f','-P','16','4',unsigned,aligned])
    props=dict(line.split('=',1) for line in (a.secret/'signing.properties').read_text('utf-8-sig').splitlines() if '=' in line and not line.startswith('#'))
    env=os.environ.copy();env['PVZF_LOCAL_STORE_PASS']=props['storepass'];env['PVZF_LOCAL_KEY_PASS']=props['keypass']
    output=a.output/'PvZ-Fusion-4.0.5-English-AI-prototype1.apk';signer=[a.jdk/'bin/java.exe','-jar',bt/'lib/apksigner.jar']
    run('sign',signer+['sign','--ks',a.secret/'PvZ-Fusion-English-Release.jks','--ks-key-alias',props['alias'],'--ks-pass','env:PVZF_LOCAL_STORE_PASS','--key-pass','env:PVZF_LOCAL_KEY_PASS','--v4-signing-enabled','false','--out',output,aligned],180,env)
    del env
    run('signature',signer+['verify','--verbose','--print-certs',output],60);assert CERT in (logs/'signature.log').read_text()
    run('alignment',[bt/'zipalign.exe','-c','-P','16','4',output],60)
    run('manifest',[bt/'aapt2.exe','dump','xmltree',output,'--file','AndroidManifest.xml'],30)
    changed=[];added=[]
    with zipfile.ZipFile(a.base) as base,zipfile.ZipFile(output) as final:
        assert final.testzip() is None
        assert final.getinfo('resources.arsc').compress_type==zipfile.ZIP_STORED
        for info in base.infolist():
            if is_old_signature(info.filename):continue
            assert info.filename in final.namelist()
            if info.CRC!=final.getinfo(info.filename).CRC:changed.append(info.filename)
        assert set(changed)=={'AndroidManifest.xml','classes2.dex','lib/arm64-v8a/libpvzfenglish.so','lib/armeabi-v7a/libpvzfenglish.so','classes.dex','resources.arsc','assets/bin/Data/data.unity3d'}
        added=[n for n in final.namelist() if n not in base.namelist() and not is_old_signature(n)]
        assert set(added)=={n for n in replacements if n not in base.namelist()}
    record={'apk':str(output),'sha256':sha(output),'size_bytes':output.stat().st_size,'base_sha256':BASE_SHA,'version_code':4050339,'local_only':True,
        'changed_entries':changed,'added_entries':added,'unchanged_gameplay_objects_and_original_native_libraries':True,'unity_identity_audit':identity,'package':'com.LanPiaoPiao.PlantsVsZombiesENAI','certificate_sha256':CERT,
        'onnxruntime_aar_sha256':sha(w/'onnxruntime-android-1.23.2.aar'),'model_manifest':manifest}
    (a.output/'AI-PROTOTYPE-BUILD.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
    print('Verified '+str(output),flush=True)

if __name__=='__main__':main()
