"""Build signed pre4 from an immutable pre3 variant and its audited payload.

Retains package, original game DEX/libraries, all media, ENAI model and identity.
No device or publication commands are run by this builder.
"""
import argparse,copy,hashlib,json,os,subprocess,zipfile
from pathlib import Path
from apply_41_prerelease4 import BUNDLE,META,file_sha,write
from build_performance_candidate import manifest,loaded_sections
from package_apk_payload import copy_entry,is_old_signature
CERT='1f2552cc7dbfbbbee21d2ea7e77edf371a377902cdcb78ba4f3104e387cd7bc6'
def audit_apk(base,output,allowed,required):
    changed=[]
    with zipfile.ZipFile(base) as old,zipfile.ZipFile(output) as new:
        names={n for n in old.namelist() if not is_old_signature(n)};assert names=={n for n in new.namelist() if not is_old_signature(n)}
        assert len(new.namelist())==len(set(new.namelist())) and new.testzip() is None
        for n in sorted(names):
            assert old.getinfo(n).compress_type==new.getinfo(n).compress_type,n
            def digest(z):
                with z.open(n) as f:return hashlib.file_digest(f,'sha256').hexdigest()
            if digest(old)!=digest(new):changed.append(n)
        assert required<=set(changed)<=allowed,changed
        managed=json.loads(new.read('assets/english/manifest.json'))
        for n,h in managed['files'].items():assert hashlib.sha256(new.read('assets/english/'+n)).hexdigest()==h
        for n,h in managed['almanac_files'].items():assert hashlib.sha256(new.read('assets/english-almanac/'+n)).hexdigest()==h
    return changed
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for n in ('base','payload','work','output','sdk','jdk','dobby','secret'):ap.add_argument('--'+n,type=Path,required=True)
    ap.add_argument('--variant',choices=['en','ai'],required=True)
    ap.add_argument('--ort-jar',type=Path);ap.add_argument('--ort-aar',type=Path)
    a=ap.parse_args();r=Path(__file__).resolve().parents[1];a.work.mkdir(parents=True,exist_ok=True);a.output.parent.mkdir(parents=True,exist_ok=True)
    report=json.loads((a.payload/'translation-report.json').read_text('utf8'));assert file_sha(a.base)==report['base_sha256'] and report['variant']==a.variant
    assert file_sha(a.payload/'data.unity3d')==report['bundle_sha256'] and file_sha(a.payload/'metadata.dat')==report['metadata_sha256']
    ai=a.variant=='ai';package='com.LanPiaoPiao.PlantsVsZombiesEN'+('AI' if ai else '');version=4100118 if ai else 4100117;name='4.1-English-pre4'+('-ENAI' if ai else '')
    logs=a.work/'logs';logs.mkdir(exist_ok=True)
    def run(n,args,timeout=120,env=None):
        with (logs/(n+'.log')).open('w',encoding='utf8') as f:p=subprocess.run(list(map(str,args)),stdout=f,stderr=subprocess.STDOUT,timeout=timeout,env=env)
        if p.returncode:raise RuntimeError(n+' failed: '+str(logs/(n+'.log')))
        print(a.variant,n+' passed',flush=True)
    bt=a.sdk/'build-tools/35.0.0';cm=a.sdk/'cmake/3.22.1/bin/cmake.exe';android=a.sdk/'platforms/android-35/android.jar'
    signer=[a.jdk/'bin/java.exe','-XX:ActiveProcessorCount=2','-Xmx512m','-jar',bt/'lib/apksigner.jar']
    run('base-signature',signer+['verify','--print-certs',a.base]);assert CERT in (logs/'base-signature.log').read_text()
    java=r/'runtime/java/com/silvershadow/pvzf';sources=[java/(n+'.java') for n in ('EnglishActivity','EnglishApplication','ProcessStartGate','ManagedFiles','BoundedTextCache','RegexPrefix','PlantbrushTranslations')]
    cp=[android]
    if ai:
        assert a.ort_jar and a.ort_aar and file_sha(a.ort_aar)=='67397e4a970e75617f765d2015ceaf911917e1d822276cfb5792744e8085cbce'
        with zipfile.ZipFile(a.ort_aar) as z:assert hashlib.sha256(z.read('classes.jar')).hexdigest()==file_sha(a.ort_jar)
        text=(java/'EnglishActivity.java').read_text('utf8');needle='            loadTranslations();';assert text.count(needle)==1
        text=text.replace(needle,needle+'\n            PlantbrushBridge.init(context);')
        needle='    private static native void startRuntime(boolean blooms);';assert text.count(needle)==1
        text=text.replace(needle,needle+'\n    public static int requestPlantbrush(){return PlantbrushBridge.request();}\n    public static int plantbrushStatus(){return PlantbrushBridge.status();}\n    public static void leavePlantbrush(){PlantbrushBridge.leave();}')
        wrapper=a.work/'EnglishActivity.java';wrapper.write_text(text,'utf8');sources[0]=wrapper
        sources += [java/'PlantbrushBridge.java',*sorted((r/'runtime/plantbrush/java').rglob('*.java'))];cp.append(a.ort_jar)
    classes=a.work/'classes';dex=a.work/'dex';classes.mkdir(exist_ok=True);dex.mkdir(exist_ok=True)
    run('javac',[a.jdk/'bin/javac.exe','-encoding','UTF-8','-source','8','-target','8','-cp',os.pathsep.join(map(str,cp)),'-d',classes,*sources],90)
    run('d8',[a.jdk/'bin/java.exe','-XX:ActiveProcessorCount=2','-Xmx512m','-cp',bt/'lib/d8.jar','com.android.tools.r8.D8','--release','--min-api','26' if ai else '22','--lib',android,'--output',dex,*sorted(classes.rglob('*.class')),*([a.ort_jar] if ai else [])],120)
    assert not (dex/'classes2.dex').exists();native={}
    for abi in ('arm64-v8a','armeabi-v7a'):
        build=a.work/('native-'+abi)
        run('configure-'+abi,[cm,'-S',r/'runtime','-B',build,'-G','Ninja','-DCMAKE_MAKE_PROGRAM='+str(a.sdk/'cmake/3.22.1/bin/ninja.exe'),'-DCMAKE_TOOLCHAIN_FILE='+str(a.sdk/'ndk/25.2.9519653/build/cmake/android.toolchain.cmake'),'-DANDROID_ABI='+abi,'-DANDROID_PLATFORM=android-22','-DCMAKE_BUILD_TYPE=Release','-DANDROID_STL=c++_static','-DDOBBY_SOURCE='+str(a.dobby),'-DPVZF_LOCAL_PLANTBRUSH='+('ON' if ai else 'OFF'),'-DPVZF_MUSIC_DIAGNOSTICS=OFF'])
        run('compile-'+abi,[cm,'--build',build,'--target','pvzfenglish','--parallel','2'],240)
        lib=build/'libpvzfenglish.so';strip=build/'stripped.so';run('strip-'+abi,[a.sdk/'ndk/25.2.9519653/toolchains/llvm/prebuilt/windows-x86_64/bin/llvm-strip.exe','--strip-unneeded','-o',strip,lib])
        assert loaded_sections(lib)==loaded_sections(strip);native['lib/'+abi+'/libpvzfenglish.so']=strip
    replacement={BUNDLE:a.payload/'data.unity3d',META:a.payload/'metadata.dat','assets/english/translations.json':a.payload/'translations.json','assets/english-almanac/LawnStrings.json':a.payload/'LawnStrings.json','assets/english-almanac/ZombieStrings.json':a.payload/'ZombieStrings.json','classes2.dex':dex/'classes.dex',**native}
    if ai:replacement.update({'assets/plantbrush/catalog.json':a.payload/'catalog.json','assets/plantbrush/manifest.json':a.payload/'plantbrush-manifest.json'})
    with zipfile.ZipFile(a.base) as z:
        managed=json.loads(z.read('assets/english/manifest.json'));managed.update(revision=name,metadata_sha256=file_sha(replacement[META]),pc_checked_commit=report['blooms_commit'])
        managed['files']['translations.json']=file_sha(replacement['assets/english/translations.json'])
        for n in ('LawnStrings.json','ZombieStrings.json'):managed['almanac_files'][n]=file_sha(replacement['assets/english-almanac/'+n])
        memory={'AndroidManifest.xml':manifest(z.read('AndroidManifest.xml'),package,version,name),'assets/english/manifest.json':json.dumps(managed,ensure_ascii=False,separators=(',',':')).encode()}
        unsigned=a.work/'unsigned.apk'
        with zipfile.ZipFile(unsigned,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=3) as out:
            for info in z.infolist():
                n=info.filename
                if is_old_signature(n):continue
                if n in memory:out.writestr(copy.copy(info),memory[n])
                elif n in replacement:out.write(replacement[n],n,compress_type=info.compress_type)
                else:copy_entry(z,out,info)
    aligned=a.work/'aligned.apk';run('align',[bt/'zipalign.exe','-f','-P','16','4',unsigned,aligned])
    props={}
    for line in (a.secret/'signing.properties').read_text('utf-8-sig').splitlines():
        if '=' in line and not line.startswith('#'):
            k,v=line.split('=',1);props[k.strip()]=v.strip()
    env=os.environ.copy();env['PVZF_STORE_PASS']=props['storepass'];env['PVZF_KEY_PASS']=props['keypass']
    run('sign',signer+['sign','--ks',a.secret/'PvZ-Fusion-English-Release.jks','--ks-key-alias',props['alias'],'--ks-pass','env:PVZF_STORE_PASS','--key-pass','env:PVZF_KEY_PASS','--v1-signing-enabled','true','--v2-signing-enabled','true','--v3-signing-enabled','true','--v4-signing-enabled','false','--out',a.output,aligned],180,env);del props,env
    run('signature',signer+['verify','--verbose','--print-certs',a.output]);assert CERT in (logs/'signature.log').read_text()
    run('alignment',[bt/'zipalign.exe','-c','-P','16','4',a.output]);run('manifest',[bt/'aapt2.exe','dump','badging',a.output])
    badging=(logs/'manifest.log').read_text();assert "name='"+package+"'" in badging and "versionCode='"+str(version)+"'" in badging and name in badging
    allowed=set(replacement)|set(memory)
    # Standard EN can reproduce its unchanged pre3 DEX. The plant-only model
    # catalog may already have these names; unchanged catalog bytes are valid.
    optional={'assets/plantbrush/catalog.json','assets/plantbrush/manifest.json'} if ai else {'classes2.dex'}
    changed=audit_apk(a.base,a.output,allowed,allowed-optional)
    write(a.work/'build.json',dict(apk=str(a.output),sha256=file_sha(a.output),bytes=a.output.stat().st_size,package=package,version_code=version,version_name=name,certificate_sha256=CERT,base_sha256=file_sha(a.base),changed_entries=changed,compression_preserved=True,other_apk_entries_identical=True,game_native_libraries_unchanged=True,all_audio_unchanged=True,offline_model_and_inference_libraries_unchanged=True if ai else None,protected_metadata=report['protected_metadata'],translation_counts=report['counts'],blooms_commit=report['blooms_commit'],device_tested=False,published=False))
    print(a.variant,'signed APK verified:',a.output,flush=True)
if __name__=='__main__':main()
