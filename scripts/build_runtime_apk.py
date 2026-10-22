"""Build the local 4.0.5 EN runtime APK and lower-version refresh-test seed.

Inputs are intentionally explicit. Signing properties never enter logs or source.
The original game native libraries are retained byte-for-byte in both ABIs.
"""
import argparse, base64, copy, hashlib, json, os, re, shutil, subprocess, sys, zipfile
from pathlib import Path
from runtime_apk import manifest, resources, dex_application_id
from prepare_runtime_payload import BASE_SHA, OFFICIAL_SHA, PIN, digest, META, BUNDLE
from package_apk_payload import is_old_signature, copy_entry
from protected_metadata import verify_metadata

DOBBY='21f07a5ce184cda9346afb8009c07fe7e47390d0'
CERT='1f2552cc7dbfbbbee21d2ea7e77edf371a377902cdcb78ba4f3104e387cd7bc6'
RESOURCE='assets/bin/Data/resources.resource'
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')

def main():
    ap=argparse.ArgumentParser()
    for name in ['base','official','work','output','sdk','jdk','secret']:ap.add_argument('--'+name,type=Path,required=True)
    ap.add_argument('--variant',choices=['seed','test1'],required=True)
    ap.add_argument('--revision',type=int,default=1)
    a=ap.parse_args();r=Path(__file__).resolve().parents[1];w=a.work.resolve();a.output.mkdir(parents=True,exist_ok=True)
    assert a.revision>=1
    suffix='' if a.revision==1 else '-r'+str(a.revision)
    logs=w/('package-'+a.variant+suffix);logs.mkdir(exist_ok=True)
    def run(stage,args,timeout=120,env=None):
        with (logs/(stage+'.log')).open('w',encoding='utf-8') as out:
            p=subprocess.run(list(map(str,args)),stdout=out,stderr=subprocess.STDOUT,timeout=timeout,env=env)
        if p.returncode:raise RuntimeError(stage+' failed; inspect '+str(logs/(stage+'.log')))
        print(stage+' passed',flush=True)
    assert digest(a.base)==BASE_SHA;assert digest(a.official)==OFFICIAL_SHA
    # The final build must not inherit fixture text or change protected metadata keys.
    metadata=w/('stale-test-metadata.dat' if a.variant=='seed' else 'metadata.dat')
    with zipfile.ZipFile(a.official) as original:protection=verify_metadata(original.read(META),metadata.read_bytes())
    java_out=w/'java-classes';java_out.mkdir(exist_ok=True)
    android=a.sdk/'platforms/android-35/android.jar';bt=a.sdk/'build-tools/35.0.0'
    run('javac',[a.jdk/'bin/javac.exe','-encoding','UTF-8','-source','8','-target','8','-classpath',android,'-d',java_out,*sorted((r/'runtime/java').rglob('*.java'))],30)
    dex_out=w/'dex';dex_out.mkdir(exist_ok=True)
    # Invoke d8 through its main class, without invoking a shell/batch wrapper.
    run('d8',[a.jdk/'bin/java.exe','-cp',bt/'lib/d8.jar','com.android.tools.r8.D8','--release','--min-api','22','--lib',android,'--output',dex_out,*sorted(java_out.rglob('*.class'))],60)
    host=w/'java-tests';host.mkdir(exist_ok=True)
    run('host-javac',[a.jdk/'bin/javac.exe','-encoding','UTF-8','-d',host,r/'runtime/java/com/silvershadow/pvzf/ManagedFiles.java',*sorted((r/'runtime/tests').glob('*.java'))],30)
    translations=json.loads((w/'english/translations.json').read_text('utf-8'))
    reviewed_metadata_change=False
    if a.variant!='seed' and translations.get('pc_overlay_commit'):
        # Permit only the literal slots explicitly recorded by the reviewed PC
        # port. Keep the package-delta gate strict for all other payloads.
        from build_metadata_translation import parse_metadata
        port=json.loads((w/'coverage-r12/port-report.json').read_text('utf-8'))
        assert port['pc_overlay']==translations['pc_overlay_commit']
        default_report=w/'editor-r19/default-name-report.json'
        default_patch=None
        if default_report.exists():
            default_patch=json.loads(default_report.read_text('utf-8'))
            assert default_patch['input_sha256']==port['outputs']['metadata.dat']
            assert default_patch['output_sha256']==digest(metadata)
            assert (default_patch['index'],default_patch['source'],default_patch['english'])==(17475,'我的规则','My Rule')
        else:
            assert port['outputs']['metadata.dat']==digest(metadata)
        with zipfile.ZipFile(a.base) as z:base_metadata=z.read(META)
        assert hashlib.sha256(base_metadata).hexdigest()==port['inputs']['metadata.dat']
        _,old_entries=parse_metadata(base_metadata);_,new_entries=parse_metadata(metadata.read_bytes())
        assert len(old_entries)==len(new_entries)
        actual={i:(x.text,y.text) for i,(x,y) in enumerate(zip(old_entries,new_entries)) if x.raw!=y.raw}
        expected={row['index']:(row['before'],row['after']) for row in port['metadata']}
        if default_patch:
            assert 17475 not in expected
            expected[17475]=('我的规则','My Rule')
        assert actual==expected,'Unreviewed metadata literal change'
        reviewed_metadata_change=bool(actual)
    (w/'regex-review.tsv').write_text('\n'.join('\t'.join(base64.b64encode(x.encode()).decode() for x in row) for row in translations['regex']))
    run('refresh-tests',[a.jdk/'bin/java.exe','-cp',host,'ManagedFilesTest',w],30)
    run('regex-tests',[a.jdk/'bin/java.exe','-cp',host,'RegexReview',w/'regex-review.tsv'],30)
    run('translation-tests',[a.jdk/'bin/java.exe','-cp',os.pathsep.join(map(str,[host,java_out,android])),'TranslationTest'],30)
    # Compile the pinned Android-compatible Dobby source with two jobs, one ABI at a time.
    dobby=w/'Dobby-android'
    assert (dobby/'CMakeLists.txt').exists(), 'Extract the pinned Dobby source first'
    archive=w/'dobby-android-source.zip'
    assert digest(archive)=='d39de3241ffef216e5e07ae9587c1f2502a747577948070e6203c3390b8491c6', 'Unexpected Dobby source archive'
    with zipfile.ZipFile(archive) as source:
        for entry in source.infolist():
            if not entry.is_dir():
                assert (dobby/entry.filename).read_bytes()==source.read(entry), 'Modified Dobby source: '+entry.filename
    cm=a.sdk/'cmake/3.22.1/bin/cmake.exe'
    for abi in ('arm64-v8a','armeabi-v7a'):
        build=w/('android-'+abi)
        run('configure-'+abi,[cm,'-S',r/'runtime','-B',build,'-G','Ninja','-DCMAKE_MAKE_PROGRAM='+str(a.sdk/'cmake/3.22.1/bin/ninja.exe'),'-DCMAKE_TOOLCHAIN_FILE='+str(a.sdk/'ndk/25.2.9519653/build/cmake/android.toolchain.cmake'),'-DANDROID_ABI='+abi,'-DANDROID_PLATFORM=android-22','-DCMAKE_BUILD_TYPE=Release','-DANDROID_STL=c++_static','-DDOBBY_SOURCE='+str(dobby)],60)
        run('native-'+abi,[cm,'--build',build,'--target','pvzfenglish','--parallel','2'],180)
    license_text=(dobby/'LICENSE').read_text()
    notice='PvZ Fusion English Android runtime\nDobby '+DOBBY+'\nhttps://github.com/jmpews/Dobby\n\n'+license_text
    (w/'english/NOTICE.txt').write_text(notice,encoding='utf-8')
    revision='4.0.5-pre3-'+a.variant+suffix
    managed={p.name:digest(p) for p in sorted((w/'english').iterdir()) if p.is_file() and p.name!='manifest.json'}
    from prepare_runtime_payload import prepare_almanac_refresh
    almanac_report=prepare_almanac_refresh(w)
    almanacs={name:w/'almanac-refresh'/('seed-'+name if a.variant=='seed' and name=='LawnStrings.json' else name) for name in ('LawnStrings.json','ZombieStrings.json','DetailStrings.json')}
    build_manifest={'revision':revision,'metadata_sha256':digest(metadata),'files':managed,'almanac_files':{name:digest(path) for name,path in almanacs.items()},'refresh_test_seed':a.variant=='seed','pc_commit':PIN}
    if translations.get('pc_overlay_commit'):
        build_manifest['pc_overlay_commit']=translations['pc_overlay_commit']
    version_code=(4050300 if a.variant=='seed' else 4050301)+2*(a.revision-1)
    replacements={BUNDLE:w/('seed-candidate.unity3d' if a.variant=='seed' else 'candidate.unity3d'),META:metadata,RESOURCE:w/'resources.resource','classes2.dex':dex_out/'classes.dex'}
    replacements.update({'assets/english-almanac/'+name:path for name,path in almanacs.items()})
    for abi in ('arm64-v8a','armeabi-v7a'):replacements['lib/'+abi+'/libpvzfenglish.so']=w/('android-'+abi)/'libpvzfenglish.so'
    for filename in managed:replacements['assets/english/'+filename]=w/'english'/filename
    memory={'assets/english/manifest.json':json.dumps(build_manifest,ensure_ascii=False,indent=2).encode()}
    with zipfile.ZipFile(a.base) as base:
        assert 'classes2.dex' not in base.namelist()
        memory['AndroidManifest.xml']=manifest(base.read('AndroidManifest.xml'),version_code)
        memory['resources.arsc']=resources(base.read('resources.arsc'))
        memory['classes.dex']=dex_application_id(base.read('classes.dex'))
        unsigned=logs/'unsigned.apk'
        with zipfile.ZipFile(unsigned,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as target:
            for info in base.infolist():
                name=info.filename
                if is_old_signature(name):continue
                if name in memory:target.writestr(copy.copy(info),memory[name])
                elif name in replacements:
                    with replacements[name].open('rb') as src,target.open(copy.copy(info),'w') as dst:shutil.copyfileobj(src,dst,8*1024*1024)
                else:copy_entry(base,target,info)
            for name,path in replacements.items():
                if name not in base.namelist():target.write(path,name)
            for name,data in memory.items():
                if name not in base.namelist():target.writestr(name,data)
    print('APK payload assembled',flush=True)
    aligned=logs/'aligned.apk';run('align',[bt/'zipalign.exe','-f','-p','4',unsigned,aligned])
    properties={}
    for line in (a.secret/'signing.properties').read_text('utf-8-sig').splitlines():
        if '=' in line and not line.startswith('#'):
            k,v=line.split('=',1);properties[k.strip()]=v.strip()
    environment=os.environ.copy();environment['PVZF_LOCAL_STORE_PASS']=properties['storepass'];environment['PVZF_LOCAL_KEY_PASS']=properties['keypass']
    output=a.output/('PvZ-Fusion-4.0.5-English-Android-prerelease3-'+('refresh-seed' if a.variant=='seed' else 'test1')+suffix+'.apk')
    signer=[a.jdk/'bin/java.exe','-jar',bt/'lib/apksigner.jar']
    run('sign',signer+['sign','--ks',a.secret/'PvZ-Fusion-English-Release.jks','--ks-key-alias',properties['alias'],'--ks-pass','env:PVZF_LOCAL_STORE_PASS','--key-pass','env:PVZF_LOCAL_KEY_PASS','--v1-signing-enabled','true','--v2-signing-enabled','true','--v3-signing-enabled','true','--v4-signing-enabled','false','--out',output,aligned],120,environment)
    environment.pop('PVZF_LOCAL_STORE_PASS');environment.pop('PVZF_LOCAL_KEY_PASS')
    run('signature',signer+['verify','--verbose','--print-certs',output],60)
    assert CERT in (logs/'signature.log').read_text()
    run('alignment',[bt/'zipalign.exe','-c','-p','4',output],60)
    run('manifest',[bt/'aapt2.exe','dump','xmltree',output,'--file','AndroidManifest.xml'],30)
    changed=[];added=[]
    with zipfile.ZipFile(a.base) as base,zipfile.ZipFile(output) as final:
        assert final.testzip() is None
        for name in final.namelist():
            if is_old_signature(name):continue
            if name not in base.namelist():added.append(name)
            elif base.getinfo(name).CRC!=final.getinfo(name).CRC:changed.append(name)
        assert set(changed)=={BUNDLE,RESOURCE,'AndroidManifest.xml','resources.arsc','classes.dex'} | ({META} if a.variant=='seed' or reviewed_metadata_change else set())
        for name in base.namelist():
            if name.startswith('lib/'):
                assert base.read(name)==final.read(name),'Original native library changed: '+name
    record={'status':'Local test build, not published; runtime device validation pending','variant':a.variant,'apk':str(output),'sha256':digest(output),'size_bytes':output.stat().st_size,'package':'com.LanPiaoPiao.PlantsVsZombiesEN','version_code':version_code,'certificate_sha256':CERT,'dobby_commit':DOBBY,'pc_commit':PIN,'changed_existing_entries':changed,'added_entries':added,'managed_refresh':build_manifest,'protected_metadata':protection,'original_native_libraries_unchanged':True,'device_tested':False}
    write(logs/'build.json',record);write(a.output/('build-'+a.variant+suffix+'.json'),record)
    print('Verified '+str(output),flush=True)

if __name__=='__main__':main()
