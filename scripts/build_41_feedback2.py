"""Build a local Standard EN follow-up from the immutable public pre-release 2.

Rebuild the two translation runtime libraries and replace only the reviewed
payload entries. Rebuild only the bootstrap DEX; reuse original game DEX,
audio, game libraries and identity. Preserve APK entry storage methods.
"""
import argparse,copy,hashlib,json,os,subprocess,zipfile
from pathlib import Path
from apply_41_feedback2 import BUNDLE,META,file_sha,write
from build_performance_candidate import manifest,loaded_sections
from package_apk_payload import copy_entry,is_old_signature
from protected_metadata import verify_metadata
from runtime_apk import application_bootstrap
BASE='7e372f8d95f8e044741cdc9ecb1c2c2231814ddb769c5770a40de6d65f6351ed'
CERT='1f2552cc7dbfbbbee21d2ea7e77edf371a377902cdcb78ba4f3104e387cd7bc6'
PACKAGE='com.LanPiaoPiao.PlantsVsZombiesEN'
VERSION=4100115
NAME='4.1-English-pre3'

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('base','official','payload','work','output','sdk','jdk','dobby','secret'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();r=Path(__file__).resolve().parents[1]
    a.work.mkdir(parents=True,exist_ok=True);a.output.parent.mkdir(parents=True,exist_ok=True)
    logs=a.work/'logs';logs.mkdir(exist_ok=True)
    assert file_sha(a.base)==BASE
    assert file_sha(a.official)=='6272551fd2573bd3e342acf1a214aa0ee6d44833260babe600e27301ef9a6390'
    review=json.loads((a.payload/'translation-report.json').read_text(encoding='utf8'))
    assert review['base_apk_sha256']==BASE and review['previous_keys_retained']
    assert file_sha(a.payload/'feedback.unity3d')==review['bundle_sha256']
    assert file_sha(a.payload/'metadata.dat')==review['metadata_sha256']
    with zipfile.ZipFile(a.official) as z:protection=verify_metadata(z.read(META),(a.payload/'metadata.dat').read_bytes())
    def run(n,args,timeout=120,env=None):
        with (logs/(n+'.log')).open('w',encoding='utf8') as f:
            result=subprocess.run(list(map(str,args)),stdout=f,stderr=subprocess.STDOUT,timeout=timeout,env=env)
        if result.returncode:raise RuntimeError(n+' failed; inspect '+str(logs/(n+'.log')))
        print(n+' passed',flush=True)
    bt=a.sdk/'build-tools/35.0.0';cm=a.sdk/'cmake/3.22.1/bin/cmake.exe'
    signer=[a.jdk/'bin/java.exe','-XX:ActiveProcessorCount=2','-Xmx512m','-jar',bt/'lib/apksigner.jar']
    run('base-signature',signer+['verify','--print-certs',a.base])
    assert CERT in (logs/'base-signature.log').read_text()
    classes=a.work/'java';dex=a.work/'dex';classes.mkdir(exist_ok=True);dex.mkdir(exist_ok=True)
    android=a.sdk/'platforms/android-35/android.jar'
    sources=[r/'runtime/java/com/silvershadow/pvzf'/(n+'.java') for n in
             ('EnglishActivity','EnglishApplication','ProcessStartGate','ManagedFiles','BoundedTextCache','RegexPrefix','PlantbrushTranslations')]
    run('javac',[a.jdk/'bin/javac.exe','-encoding','UTF-8','-source','8','-target','8','-cp',android,'-d',classes,*sources],60)
    run('d8',[a.jdk/'bin/java.exe','-XX:ActiveProcessorCount=2','-Xmx512m','-cp',bt/'lib/d8.jar','com.android.tools.r8.D8','--release','--min-api','22','--lib',android,'--output',dex,*sorted(classes.rglob('*.class'))],90)
    assert not (dex/'classes2.dex').exists()
    native={}
    for abi in ('arm64-v8a','armeabi-v7a'):
        build=a.work/('native-'+abi)
        run('configure-'+abi,[cm,'-S',r/'runtime','-B',build,'-G','Ninja','-DCMAKE_MAKE_PROGRAM='+str(a.sdk/'cmake/3.22.1/bin/ninja.exe'),'-DCMAKE_TOOLCHAIN_FILE='+str(a.sdk/'ndk/25.2.9519653/build/cmake/android.toolchain.cmake'),'-DANDROID_ABI='+abi,'-DANDROID_PLATFORM=android-22','-DCMAKE_BUILD_TYPE=Release','-DANDROID_STL=c++_static','-DDOBBY_SOURCE='+str(a.dobby),'-DPVZF_LOCAL_PLANTBRUSH=OFF','-DPVZF_MUSIC_DIAGNOSTICS=OFF'],60)
        run('compile-'+abi,[cm,'--build',build,'--target','pvzfenglish','--parallel','2'],240)
        lib=build/'libpvzfenglish.so';stripped=build/'libpvzfenglish-stripped.so'
        run('strip-'+abi,[a.sdk/'ndk/25.2.9519653/toolchains/llvm/prebuilt/windows-x86_64/bin/llvm-strip.exe','--strip-unneeded','-o',stripped,lib],30)
        assert loaded_sections(lib)==loaded_sections(stripped)
        native['lib/'+abi+'/libpvzfenglish.so']=stripped
    replacements={BUNDLE:a.payload/'feedback.unity3d',META:a.payload/'metadata.dat',
                  'assets/english/translations.json':a.payload/'english/translations.json',
                  'assets/english-almanac/LawnStrings.json':a.payload/'almanac-refresh/LawnStrings.json',
                  'assets/english-almanac/ZombieStrings.json':a.payload/'almanac-refresh/ZombieStrings.json',
                  'classes2.dex':dex/'classes.dex',**native}
    with zipfile.ZipFile(a.base) as z:
        managed=json.loads(z.read('assets/english/manifest.json'))
        managed.update(revision=NAME,metadata_sha256=file_sha(replacements[META]),pc_checked_commit=review['pc_checked_commit'])
        managed['files']['translations.json']=file_sha(replacements['assets/english/translations.json'])
        managed['almanac_files']['LawnStrings.json']=file_sha(replacements['assets/english-almanac/LawnStrings.json'])
        managed['almanac_files']['ZombieStrings.json']=file_sha(replacements['assets/english-almanac/ZombieStrings.json'])
        memory={'AndroidManifest.xml':application_bootstrap(manifest(z.read('AndroidManifest.xml'),PACKAGE,VERSION,NAME)),
                'assets/english/manifest.json':json.dumps(managed,ensure_ascii=False,separators=(',',':')).encode()}
        unsigned=a.work/'unsigned.apk'
        with zipfile.ZipFile(unsigned,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=3) as out:
            for info in z.infolist():
                n=info.filename
                if is_old_signature(n):continue
                if n in memory:out.writestr(copy.copy(info),memory[n])
                elif n in replacements:out.write(replacements[n],n,compress_type=info.compress_type)
                else:copy_entry(z,out,info)
    aligned=a.work/'aligned.apk';run('align',[bt/'zipalign.exe','-f','-P','16','4',unsigned,aligned])
    props={}
    for line in (a.secret/'signing.properties').read_text(encoding='utf-8-sig').splitlines():
        if '=' in line and not line.startswith('#'):
            k,v=line.split('=',1);props[k.strip()]=v.strip()
    env=os.environ.copy();env['PVZF_STORE_PASS']=props['storepass'];env['PVZF_KEY_PASS']=props['keypass']
    run('sign',signer+['sign','--ks',a.secret/'PvZ-Fusion-English-Release.jks','--ks-key-alias',props['alias'],'--ks-pass','env:PVZF_STORE_PASS','--key-pass','env:PVZF_KEY_PASS','--v1-signing-enabled','true','--v2-signing-enabled','true','--v3-signing-enabled','true','--v4-signing-enabled','false','--out',a.output,aligned],180,env)
    del env,props
    run('signature',signer+['verify','--verbose','--print-certs',a.output]);assert CERT in (logs/'signature.log').read_text()
    run('alignment',[bt/'zipalign.exe','-c','-P','16','4',a.output])
    run('manifest',[bt/'aapt2.exe','dump','badging',a.output]);badging=(logs/'manifest.log').read_text()
    assert "name='"+PACKAGE+"'" in badging and "versionCode='"+str(VERSION)+"'" in badging and NAME in badging
    changed=[]
    with zipfile.ZipFile(a.base) as base,zipfile.ZipFile(a.output) as final:
        assert final.testzip() is None and len(final.namelist())==len(set(final.namelist()))
        assert {n for n in final.namelist() if not is_old_signature(n)}=={n for n in base.namelist() if not is_old_signature(n)}
        for n in base.namelist():
            if is_old_signature(n):continue
            assert final.getinfo(n).compress_type==base.getinfo(n).compress_type,('APK entry storage changed',n)
            # Stream comparison so the largest unchanged audio/model entries
            # do not create two additional full-size in-memory copies.
            def digest(z,n):
                with z.open(n) as f:return hashlib.file_digest(f,'sha256').hexdigest()
            if digest(base,n)!=digest(final,n):changed.append(n)
        assert set(changed)==set(replacements)|set(memory),changed
        assert final.read('assets/english-almanac/LawnStrings.json')==(a.payload/'almanac-refresh/LawnStrings.json').read_bytes()
    write(a.work/'build.json',dict(apk=str(a.output),sha256=file_sha(a.output),bytes=a.output.stat().st_size,package=PACKAGE,version_code=VERSION,version_name=NAME,certificate_sha256=CERT,base_apk_sha256=BASE,changed_entries=sorted(changed),all_entry_compression_types_preserved=True,game_native_libraries_unchanged=True,all_audio_entries_unchanged=True,original_dex_and_online_recognizer_unchanged=True,bootstrap_dex_rebuilt=True,application_bootstrap='com.silvershadow.pvzf.EnglishApplication',protected_metadata=protection,review=review,device_tested=False,published=False,runtime_source_sha256={str(f.relative_to(r)):file_sha(f) for f in sorted((r/'runtime').rglob('*')) if f.is_file() and f.suffix in ('.cpp','.h','.inc','.java')}))
    print('Local Standard EN candidate verified: '+str(a.output),flush=True)

if __name__=='__main__':main()
