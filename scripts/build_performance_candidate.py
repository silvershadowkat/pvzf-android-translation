#!/usr/bin/env python3
"""Build local performance candidates over the published pre3 APKs.

Without a payload report, only the bridge DEX, two bridge libraries and version
attributes may change. An audited payload report additionally allows the seven
explicit translation entries. AI builds require their own audited Unity identity.
Original game native libraries, package IDs and all other entries are retained.
No publishing, installation or device access is performed.
"""
import argparse
import copy
import hashlib
import json
import os
import shutil
from pathlib import Path
import struct
import subprocess
import zipfile
from runtime_apk import Pool, chunks, U32
from package_apk_payload import copy_entry, is_old_signature

BASES = {
    'regular': ('9200f8dca136ebc754a422b8ff8f843cc1c19b1ad10a60bd12bdda150dc8b97d', 'com.LanPiaoPiao.PlantsVsZombiesEN'),
    'ai': ('be3b8c64f2852d85b10c8cc2b4c391b274bf6c7733f81b92f4f409fad4798e42', 'com.LanPiaoPiao.PlantsVsZombiesENAI'),
}
CERT = '1f2552cc7dbfbbbee21d2ea7e77edf371a377902cdcb78ba4f3104e387cd7bc6'

def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def loaded_sections(path):
    """Keep every allocated ELF section byte-identical when stripping symbols."""
    b=Path(path).read_bytes()
    assert b[:4]==b'\x7fELF' and b[5]==1
    wide=b[4]==2
    off=struct.unpack_from('<Q' if wide else '<I',b,40 if wide else 32)[0]
    size,count,names=struct.unpack_from('<HHH',b,58 if wide else 46)
    fmt='<IIQQQQIIQQ' if wide else '<IIIIIIIIII'
    sections=[struct.unpack_from(fmt,b,off+i*size) for i in range(count)]
    table=sections[names];strings=b[table[4]:table[4]+table[5]]
    result={}
    for s in sections:
        if not s[2]&2:continue
        name=strings[s[0]:].split(b'\0',1)[0].decode('ascii')
        payload=b'' if s[1]==8 else b[s[4]:s[4]+s[5]]
        result[name]=(s[1],s[2],s[3],s[5],hashlib.sha256(payload).hexdigest())
    return result

def manifest(data, package, version_code=4050341, version_name='4.0.5-English-pre3-performance1'):
    parts = list(chunks(data))
    pool = Pool(next(b for _, kind, _, b in parts if kind == 1))
    edits = set()
    for _, kind, _, b in parts:
        if kind != 0x102 or pool.strings[U32(b,20)] != 'manifest':
            continue
        start, size, n = struct.unpack_from('<HHH', b, 24)
        for i in range(n):
            p = 16 + start + i * size
            name = pool.strings[U32(b,p+4)]
            if name == 'package':
                assert pool.strings[U32(b,p+16)] == package
                edits.add(name)
            elif name == 'versionCode':
                struct.pack_into('<I', b, p+8, 0xffffffff)
                b[p+15] = 0x10
                struct.pack_into('<I', b, p+16, version_code)
                edits.add(name)
            elif name == 'versionName':
                ix = pool.add(version_name)
                struct.pack_into('<I', b, p+8, ix)
                b[p+15] = 3
                struct.pack_into('<I', b, p+16, ix)
                edits.add(name)
    assert edits == {'package','versionCode','versionName'}
    body = b''.join(pool.encode() if k == 1 else bytes(b) for _,k,_,b in parts)
    header = bytearray(data[:8]); struct.pack_into('<I', header,4,len(body)+8)
    return bytes(header)+body

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ('regular','ai','work','output','sdk','jdk','dobby','ort','secret'):
        ap.add_argument('--'+name,type=Path,required=True)
    ap.add_argument('--version-code',type=int,default=4050341)
    ap.add_argument('--version-name',default='4.0.5-English-pre3-performance1')
    ap.add_argument('--payload-report',type=Path)
    ap.add_argument('--release-names',action='store_true')
    ap.add_argument('--variant',choices=('regular','ai','all'),default='all')
    a=ap.parse_args();r=Path(__file__).resolve().parents[1]
    a.work.mkdir(parents=True,exist_ok=True);a.output.mkdir(parents=True,exist_ok=True)
    logs=a.work/'logs';logs.mkdir(exist_ok=True)
    def run(name,args,timeout=120,env=None):
        with (logs/(name+'.log')).open('w',encoding='utf8') as log:
            p=subprocess.run(list(map(str,args)),stdout=log,stderr=subprocess.STDOUT,timeout=timeout,env=env)
        if p.returncode:raise RuntimeError(name+' failed; inspect '+str(logs/(name+'.log')))
        print(name+' passed',flush=True)
    for variant in BASES:
        assert sha(getattr(a,variant)) == BASES[variant][0], 'Unreviewed base APK'
    payload={}
    if a.payload_report:
        report=json.loads(a.payload_report.read_text('utf8'))
        allowed={'assets/bin/Data/data.unity3d','assets/bin/Data/Managed/Metadata/global-metadata.dat','assets/english/translations.json','assets/english/manifest.json'}|{'assets/english-almanac/'+n+'.json' for n in ('LawnStrings','ZombieStrings','DetailStrings')}
        assert set(report['files'])==allowed
        for name,row in report['files'].items():
            assert sha(row['path'])==row['sha256'],'Payload differs from audit: '+name
            payload[name]=Path(row['path'])
        # The AI variant's PlayerSettings identity must survive shared text
        # updates. Never replace its bundle with the regular EN bundle.
        identity=report.get('ai_identity_bundle')
        if a.variant in ('ai','all'):
            assert identity and sha(identity['path'])==identity['sha256'],'Missing audited ENAI identity bundle'
            assert identity['only_player_settings_changed'] is True
    cm=a.sdk/'cmake/3.22.1/bin/cmake.exe';bt=a.sdk/'build-tools/35.0.0';android=a.sdk/'platforms/android-35/android.jar'
    for abi in ('arm64-v8a','armeabi-v7a'):
        build=a.work/('native-'+abi)
        run('configure-'+abi,[cm,'-S',r/'runtime','-B',build,'-G','Ninja',
            '-DCMAKE_MAKE_PROGRAM='+str(a.sdk/'cmake/3.22.1/bin/ninja.exe'),
            '-DCMAKE_TOOLCHAIN_FILE='+str(a.sdk/'ndk/25.2.9519653/build/cmake/android.toolchain.cmake'),
            '-DANDROID_ABI='+abi,'-DANDROID_PLATFORM=android-22','-DCMAKE_BUILD_TYPE=Release',
            '-DANDROID_STL=c++_static','-DPVZF_MUSIC_DIAGNOSTICS=OFF','-DDOBBY_SOURCE='+str(a.dobby)])
        run('native-'+abi,[cm,'--build',build,'--target','pvzfenglish','--parallel','2'],240)
        original=build/'libpvzfenglish.so';stripped=build/'libpvzfenglish-stripped.so'
        run('strip-'+abi,[a.sdk/'ndk/25.2.9519653/toolchains/llvm/prebuilt/windows-x86_64/bin/llvm-strip.exe','--strip-unneeded','-o',stripped,original])
        assert loaded_sections(original)==loaded_sections(stripped), 'Strip changed loaded ELF sections'
    props=dict(line.split('=',1) for line in (a.secret/'signing.properties').read_text('utf-8-sig').splitlines() if '=' in line and not line.startswith('#'))
    for variant, (digest,package) in BASES.items():
        if a.variant!='all' and variant!=a.variant:continue
        w=a.work/variant;w.mkdir(exist_ok=True)
        classes=w/'classes';dex=w/'dex'
        # Remove only this builder's disposable Java outputs. Otherwise removed
        # anonymous classes can leak into the next APK from a cached build.
        for folder in (classes,dex):
            assert folder.resolve().parent==w.resolve() and w.resolve().parent==a.work.resolve()
            if folder.exists():shutil.rmtree(folder)
            folder.mkdir()
        sources=sorted((r/'runtime/java').rglob('*.java'))
        deps=[android]
        if variant=='ai':
            sources+=sorted((r/'runtime/plantbrush/java').rglob('*.java'));deps.append(a.ort/'classes.jar')
        run(variant+'-javac',[a.jdk/'bin/javac.exe','-encoding','UTF-8','-source','8','-target','8','-classpath',os.pathsep.join(map(str,deps)),'-d',classes,*sources],60)
        run(variant+'-d8',[a.jdk/'bin/java.exe','-XX:ActiveProcessorCount=2','-Xmx768m','-cp',bt/'lib/d8.jar','com.android.tools.r8.D8','--release','--min-api','26' if variant=='ai' else '22','--lib',android,'--output',dex,*sorted(classes.rglob('*.class')),*([a.ort/'classes.jar'] if variant=='ai' else [])],120)
        assert not (dex/'classes2.dex').exists(), 'Unexpected multidex'
        replacements={'classes2.dex':dex/'classes.dex',**payload}
        if variant=='ai' and a.payload_report:replacements['assets/bin/Data/data.unity3d']=Path(identity['path'])
        for abi in ('arm64-v8a','armeabi-v7a'):
            replacements['lib/'+abi+'/libpvzfenglish.so']=a.work/('native-'+abi)/'libpvzfenglish-stripped.so'
        unsigned=w/'unsigned.apk'
        with zipfile.ZipFile(getattr(a,variant)) as base,zipfile.ZipFile(unsigned,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=3) as out:
            for info in base.infolist():
                if is_old_signature(info.filename):continue
                if info.filename=='AndroidManifest.xml':out.writestr(copy.copy(info),manifest(base.read(info),package,a.version_code,a.version_name))
                elif info.filename in replacements:out.write(replacements[info.filename],info.filename,compress_type=info.compress_type)
                else:copy_entry(base,out,info)
        aligned=w/'aligned.apk';run(variant+'-align',[bt/'zipalign.exe','-f','-P','16','4',unsigned,aligned])
        env=os.environ.copy();env['PVZF_LOCAL_STORE_PASS']=props['storepass'];env['PVZF_LOCAL_KEY_PASS']=props['keypass']
        filename='PvZ-Fusion-4.0.5-English'+('-AI' if variant=='ai' else '')+'-Android-prerelease3-performance1.apk'
        if a.release_names:filename='PvZ-Fusion-4.0.5-English-prerelease3'+('-Experimental-AI' if variant=='ai' else '')+'.apk'
        output=a.output/filename
        if output.exists():raise FileExistsError('Keep existing candidate: '+str(output))
        signer=[a.jdk/'bin/java.exe','-XX:ActiveProcessorCount=2','-Xmx512m','-jar',bt/'lib/apksigner.jar']
        run(variant+'-sign',signer+['sign','--ks',a.secret/'PvZ-Fusion-English-Release.jks','--ks-key-alias',props['alias'],'--ks-pass','env:PVZF_LOCAL_STORE_PASS','--key-pass','env:PVZF_LOCAL_KEY_PASS','--v4-signing-enabled','false','--out',output,aligned],180,env)
        del env
        run(variant+'-signature',signer+['verify','--verbose','--print-certs',output],120)
        assert CERT in (logs/(variant+'-signature.log')).read_text()
        run(variant+'-alignment',[bt/'zipalign.exe','-c','-P','16','4',output])
        run(variant+'-manifest',[bt/'aapt2.exe','dump','xmltree',output,'--file','AndroidManifest.xml'])
        changed=[]
        with zipfile.ZipFile(getattr(a,variant)) as base,zipfile.ZipFile(output) as final:
            assert final.testzip() is None
            assert {n for n in base.namelist() if not is_old_signature(n)}=={n for n in final.namelist() if not is_old_signature(n)}
            for info in base.infolist():
                if not is_old_signature(info.filename) and info.CRC != final.getinfo(info.filename).CRC:changed.append(info.filename)
            assert set(changed)<=set(replacements)|{'AndroidManifest.xml'}
            assert {'AndroidManifest.xml','classes2.dex','lib/arm64-v8a/libpvzfenglish.so','lib/armeabi-v7a/libpvzfenglish.so'}<=set(changed)
        record={'apk':str(output),'sha256':sha(output),'size':output.stat().st_size,'package':package,'version_code':a.version_code,'base_sha256':digest,'changed_entries':changed,'audited_payload_report':str(a.payload_report) if a.payload_report else None,'all_other_entries_unchanged':True,'local_only':True,'certificate_sha256':CERT}
        (a.output/(variant+'-build.json')).write_text(json.dumps(record,indent=2),encoding='utf8')
        print('Verified '+filename,flush=True)

if __name__=='__main__':main()
