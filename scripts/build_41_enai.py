"""Build a local ENAI update from the exact verified 4.1 feedback APK.

Keeps the current translation, stat fixes and native music. Adds only the
optional loopback recognizer and guards its identity against published ENAI.
"""
import argparse,copy,gc,hashlib,json,os,re,shutil,subprocess,zipfile
from pathlib import Path
import UnityPy
import runtime_apk
from build_plantbrush_prototype import ai_manifest
from build_performance_candidate import manifest,loaded_sections
from package_apk_payload import copy_entry,is_old_signature
from protected_metadata import verify_metadata

BASE='fb219ee164ac1fe9a39c44900ed3b29814e4ec36b39c80b01788f4ce4af31ddc'
PREVIOUS='e4f33f9f5a25bca8014cb5d56e1ab60fca0fb441c0b2bca6012d0f7b73adc8b1'
ORT='67397e4a970e75617f765d2015ceaf911917e1d822276cfb5792744e8085cbce'
CERT='1f2552cc7dbfbbbee21d2ea7e77edf371a377902cdcb78ba4f3104e387cd7bc6'
PACKAGE='com.LanPiaoPiao.PlantsVsZombiesENAI'
VERSION=4100108;NAME='4.1-English-pre1-ENAI-local3'
BUNDLE='assets/bin/Data/data.unity3d';META='assets/bin/Data/Managed/Metadata/global-metadata.dat'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def digest(b):return hashlib.sha256(b).hexdigest()
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('base','previous-ai','official','prototype-work','work','output','sdk','jdk','dobby','secret','types'):
        p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();r=Path(__file__).resolve().parents[1];w=a.work.resolve();w.mkdir(parents=True,exist_ok=True);a.output.parent.mkdir(parents=True,exist_ok=True)
    assert sha(a.base)==BASE and sha(a.previous_ai)==PREVIOUS
    prototype=a.prototype_work;assert sha(prototype/'onnxruntime-android-1.24.3.aar')==ORT
    ort=prototype/'ort-1.24.3';logs=w/'logs';logs.mkdir(exist_ok=True)
    with zipfile.ZipFile(prototype/'onnxruntime-android-1.24.3.aar') as archive:
        for name in archive.namelist():
            if name=='classes.jar' or name.startswith(('jni/arm64-v8a/','jni/armeabi-v7a/')) and name.endswith('.so'):
                assert digest(archive.read(name))==sha(ort/name),'Extracted inference runtime differs from the pinned AAR'
    def run(name,args,timeout=120,env=None):
        with (logs/(name+'.log')).open('w',encoding='utf-8') as f:process=subprocess.run(list(map(str,args)),stdout=f,stderr=subprocess.STDOUT,timeout=timeout,env=env)
        if process.returncode:raise RuntimeError(name+' failed: '+str(logs/(name+'.log')))
        print(name+' passed',flush=True)
    bt=a.sdk/'build-tools/35.0.0';android=a.sdk/'platforms/android-35/android.jar'
    signer=[a.jdk/'bin/java.exe','-XX:ActiveProcessorCount=2','-Xmx512m','-jar',bt/'lib/apksigner.jar']
    run('previous-signature',signer+['verify','--verbose','--print-certs',a.previous_ai])
    assert CERT in (logs/'previous-signature.log').read_text()
    run('previous-package',[bt/'aapt2.exe','dump','badging',a.previous_ai]);assert PACKAGE in (logs/'previous-package.log').read_text()
    identity_path=w/'identity-unity-audit.json';bundle=w/'identity-ai.unity3d'
    identity=json.loads(identity_path.read_text(encoding='utf-8')) if identity_path.exists() else {}
    cached_identity=identity.get('base_apk_sha256')==BASE and bundle.exists() and identity.get('sha256')==sha(bundle) and identity.get('only_enai_identity_and_loopback_config_changed')
    with zipfile.ZipFile(a.base) as z:
        source=None if cached_identity else z.read(BUNDLE);game_manifest=json.loads(z.read('assets/english/manifest.json'))
        names={row['seedType']:row['name'] for row in json.loads(z.read('assets/english-almanac/LawnStrings.json'))['plants']}
        (w/'base-classes.dex').write_bytes(z.read('classes.dex'))
    # Exact Unity object audit: ENAI identity plus a loopback-only service asset.
    # The asset also fails closed if an optional native hook cannot install.
    if not cached_identity:
        e=UnityPy.load(source);del source
        before={(o.assets_file.name,o.path_id):digest(o.get_raw_data()) for o in e.objects};settings=[]
        for o in e.objects:
            if o.type.name=='TextAsset':
                data=o.read()
                if data.m_Name=='MaLiangService':
                    config=json.loads(data.m_Script)
                    assert set(config)=={'endpoint','apiToken'},'Review changed service configuration schema'
                    config.update(endpoint='http://127.0.0.1:17861',apiToken='offline-local')
                    data.m_Script=json.dumps(config,separators=(',',':'));data.save();settings.append((o.assets_file.name,o.path_id))
            if o.type.name!='PlayerSettings':continue
            tree=o.read_typetree();assert tree['productName']=='PlantsVsZombiesEN';tree['productName']='PlantsVsZombiesENAI'
            def rename(value):
                if isinstance(value,dict):return {k:rename(v) for k,v in value.items()}
                if isinstance(value,list):return [rename(v) for v in value]
                return PACKAGE if value=='com.LanPiaoPiao.PlantsVsZombiesEN' else value
            o.save_typetree(rename(tree));settings.append((o.assets_file.name,o.path_id))
        assert len(settings)==2 and ('globalgamemanagers',1) in settings
        bundle.write_bytes(e.file.save(packer='lz4'));del e;gc.collect()
        e=UnityPy.load(str(bundle));after={(o.assets_file.name,o.path_id):digest(o.get_raw_data()) for o in e.objects};del e;gc.collect()
        assert set(before)==set(after) and {k for k in before if before[k]!=after[k]}==set(settings)
        identity=dict(objects_compared=len(before),changed=settings,only_enai_identity_and_loopback_config_changed=True,sha256=sha(bundle),base_apk_sha256=BASE,recognition_endpoint='http://127.0.0.1:17861',original_service_credentials_removed=True);write(identity_path,identity)
    print('Unity identity and loopback-only configuration audit passed',flush=True)
    # Rewrite one encoded BuildConfig value using the established DEX library.
    jars=[prototype/n for n in ('smali-dexlib2-3.0.9.jar','smali-util-3.0.9.jar','smali-baksmali-3.0.9.jar','guava-33.5.0-jre.jar')]
    identity_classes=w/'identity-classes';identity_classes.mkdir(exist_ok=True);cp=os.pathsep.join(map(str,[identity_classes,*jars]))
    run('identity-javac',[a.jdk/'bin/javac.exe','-encoding','UTF-8','-cp',cp,'-d',identity_classes,r/'runtime/plantbrush/tests/PlantbrushIdentity.java',r/'runtime/plantbrush/tests/PlantbrushDexAudit.java'])
    run('identity-dex',[a.jdk/'bin/java.exe','-Xmx256m','-cp',cp,'PlantbrushIdentity',w/'base-classes.dex',w/'ai-classes.dex'])
    for name,path in [('before',w/'base-classes.dex'),('after',w/'ai-classes.dex')]:
        run('smali-'+name,[a.jdk/'bin/java.exe','-Xmx256m','-cp',cp,'PlantbrushDexAudit',path,w/('dex-'+name)])
    old_files={p.relative_to(w/'dex-before'):p for p in (w/'dex-before').rglob('*.smali')};new_files={p.relative_to(w/'dex-after'):p for p in (w/'dex-after').rglob('*.smali')};assert old_files.keys()==new_files.keys()
    dex_changes=[]
    def normalize(s):return re.sub(r'(?m)^(\.field[^\n]*?) = (?:0x0L?|false|null)$',r'\1',s)
    for path in old_files:
        old=normalize(old_files[path].read_text(encoding='utf-8'));new=normalize(new_files[path].read_text(encoding='utf-8'))
        if old!=new:
            assert str(path).replace('\\','/').endswith('/BuildConfig.smali')
            assert old.replace('"com.LanPiaoPiao.PlantsVsZombiesEN"','"'+PACKAGE+'"')==new
            dex_changes.append(str(path))
    assert len(dex_changes)==1
    write(w/'identity-dex-audit.json',dict(classes_compared=len(old_files),only_application_id_semantic_change=True,changed=dex_changes))
    assets=w/'assets';assets.mkdir(exist_ok=True)
    model_manifest=json.loads((prototype/'assets/manifest.json').read_text(encoding='utf-8'))
    for name,expected in model_manifest['files'].items():assert sha(prototype/'assets'/name)==expected
    catalog=json.loads((prototype/'assets/catalog.json').read_text(encoding='utf-8'));dump=a.types.read_text(encoding='utf-8');enum=dump[dump.index('public enum PlantType'):];enum=enum[:enum.index('\n}')]
    types={int(value):name for name,value in re.findall(r'\n\s+public const PlantType (\w+) = (-?\d+);',enum)}
    for row in catalog:
        assert types.get(row['plantType'])==row['enumName'],'Catalog/game identity mismatch'
        name=names.get(row['plantType'])
        if name and not re.search('[\u3400-\u9fff]',name):row['displayName']=name
    write(assets/'catalog.json',catalog);model_manifest['files']['catalog.json']=sha(assets/'catalog.json')
    model_manifest.update(android_variant=NAME,plant_only=True,retain_until_game_exit=True,release_on_critical_memory_pressure=True)
    write(assets/'manifest.json',model_manifest)
    for name in ('vision.onnx','index.bin','NOTICE.txt','CLIP-LICENSE.txt','ONNXRUNTIME-LICENSE.txt'):
        # Reuse immutable large inputs by path during packaging, not by copying.
        assert (prototype/'assets'/name).is_file()
    # Stage the optional wrapper without introducing an AI dependency into EN.
    source=(r/'runtime/java/com/silvershadow/pvzf/EnglishActivity.java').read_text(encoding='utf-8')
    needle='            loadTranslations();';assert source.count(needle)==1
    source=source.replace(needle,needle+'\n            PlantbrushBridge.init(getApplicationContext());')
    needle='    private static native void startRuntime(boolean blooms);';assert source.count(needle)==1
    source=source.replace(needle,needle+'\n    public static int requestPlantbrush(){return PlantbrushBridge.request();}\n    public static int plantbrushStatus(){return PlantbrushBridge.status();}\n    public static void leavePlantbrush(){PlantbrushBridge.leave();}')
    wrapper=w/'EnglishActivity.java';wrapper.write_text(source,encoding='utf-8')
    classes=w/'classes';dex=w/'dex'
    for path in (classes,dex):
        assert path.resolve().parent==w
        if path.exists():shutil.rmtree(path)
        path.mkdir()
    java=[wrapper]+[r/'runtime/java/com/silvershadow/pvzf'/(n+'.java') for n in ('ManagedFiles','BoundedTextCache','RegexPrefix','PlantbrushTranslations','PlantbrushBridge')]+sorted((r/'runtime/plantbrush/java').rglob('*.java'))
    run('javac',[a.jdk/'bin/javac.exe','-encoding','UTF-8','-source','8','-target','8','-cp',os.pathsep.join(map(str,[android,ort/'classes.jar'])),'-d',classes,*java])
    run('d8',[a.jdk/'bin/java.exe','-XX:ActiveProcessorCount=2','-Xmx512m','-cp',bt/'lib/d8.jar','com.android.tools.r8.D8','--release','--min-api','26','--lib',android,'--output',dex,*sorted(classes.rglob('*.class')),ort/'classes.jar'])
    assert not (dex/'classes2.dex').exists()
    cm=a.sdk/'cmake/3.22.1/bin/cmake.exe';native={}
    for abi in ('arm64-v8a','armeabi-v7a'):
        build=w/('native-'+abi)
        run('configure-'+abi,[cm,'-S',r/'runtime','-B',build,'-G','Ninja','-DCMAKE_MAKE_PROGRAM='+str(a.sdk/'cmake/3.22.1/bin/ninja.exe'),'-DCMAKE_TOOLCHAIN_FILE='+str(a.sdk/'ndk/25.2.9519653/build/cmake/android.toolchain.cmake'),'-DANDROID_ABI='+abi,'-DANDROID_PLATFORM=android-22','-DCMAKE_BUILD_TYPE=Release','-DANDROID_STL=c++_static','-DDOBBY_SOURCE='+str(a.dobby),'-DPVZF_LOCAL_PLANTBRUSH=ON','-DPVZF_MUSIC_DIAGNOSTICS=OFF'])
        run('compile-'+abi,[cm,'--build',build,'--target','pvzfenglish','--parallel','2'],240)
        lib=build/'libpvzfenglish.so';stripped=build/'stripped.so';run('strip-'+abi,[a.sdk/'ndk/25.2.9519653/toolchains/llvm/prebuilt/windows-x86_64/bin/llvm-strip.exe','--strip-unneeded','-o',stripped,lib])
        assert loaded_sections(lib)==loaded_sections(stripped)
        native['lib/'+abi+'/libpvzfenglish.so']=stripped
        for file in (ort/'jni'/abi).glob('*.so'):native['lib/'+abi+'/'+file.name]=file
    runtime_apk.OLD='com.LanPiaoPiao.PlantsVsZombiesEN';runtime_apk.NEW=PACKAGE
    with zipfile.ZipFile(a.base) as z:resource=runtime_apk.resources(z.read('resources.arsc'))
    game_manifest['revision']=NAME
    replacements={BUNDLE:bundle,'classes.dex':w/'ai-classes.dex','classes2.dex':dex/'classes.dex',**native}
    replacements.update({'assets/plantbrush/'+p.name:p for p in assets.iterdir()})
    replacements.update({'assets/plantbrush/'+n:prototype/'assets'/n for n in ('vision.onnx','index.bin','NOTICE.txt','CLIP-LICENSE.txt','ONNXRUNTIME-LICENSE.txt')})
    memory={'resources.arsc':resource,'assets/english/manifest.json':json.dumps(game_manifest,separators=(',',':')).encode()}
    unsigned=w/'unsigned.apk'
    with zipfile.ZipFile(a.base) as base,zipfile.ZipFile(unsigned,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=3) as out:
        memory['AndroidManifest.xml']=manifest(ai_manifest(base.read('AndroidManifest.xml')),PACKAGE,VERSION,NAME)
        for info in base.infolist():
            if is_old_signature(info.filename):continue
            if info.filename in memory:out.writestr(copy.copy(info),memory[info.filename])
            elif info.filename in replacements:out.write(replacements[info.filename],info.filename,compress_type=info.compress_type)
            else:copy_entry(base,out,info)
        for name,path in replacements.items():
            if name not in base.namelist():out.write(path,name,compress_type=zipfile.ZIP_STORED if name.startswith('lib/') else zipfile.ZIP_DEFLATED)
    aligned=w/'aligned.apk';run('align',[bt/'zipalign.exe','-f','-P','16','4',unsigned,aligned])
    props={}
    for line in (a.secret/'signing.properties').read_text(encoding='utf-8-sig').splitlines():
        if '=' in line and not line.startswith('#'):key,value=line.split('=',1);props[key.strip()]=value.strip()
    env=os.environ.copy();env['PVZF_AI_STORE_PASS']=props['storepass'];env['PVZF_AI_KEY_PASS']=props['keypass']
    run('sign',signer+['sign','--ks',a.secret/'PvZ-Fusion-English-Release.jks','--ks-key-alias',props['alias'],'--ks-pass','env:PVZF_AI_STORE_PASS','--key-pass','env:PVZF_AI_KEY_PASS','--v1-signing-enabled','true','--v2-signing-enabled','true','--v3-signing-enabled','true','--v4-signing-enabled','false','--out',a.output,aligned],180,env)
    del env
    run('signature',signer+['verify','--verbose','--print-certs',a.output]);assert CERT in (logs/'signature.log').read_text()
    run('alignment',[bt/'zipalign.exe','-c','-P','16','4',a.output])
    run('manifest',[bt/'aapt2.exe','dump','badging',a.output]);badging=(logs/'manifest.log').read_text();assert PACKAGE in badging and str(VERSION) in badging and re.search(r"(?:minSdkVersion|sdkVersion):'26'",badging)
    run('manifest-tree',[bt/'aapt2.exe','dump','xmltree',a.output,'--file','AndroidManifest.xml'])
    tree=(logs/'manifest-tree.log').read_text();assert ':plantbrush' in tree and 'com.silvershadow.pvzf.PlantbrushService' in tree
    changed=[]
    with zipfile.ZipFile(a.base) as base,zipfile.ZipFile(a.output) as final,zipfile.ZipFile(a.official) as official:
        assert final.testzip() is None
        allowed=set(replacements)|set(memory)
        for name in base.namelist():
            if is_old_signature(name):continue
            with base.open(name) as f:x=hashlib.file_digest(f,'sha256').digest()
            with final.open(name) as f:y=hashlib.file_digest(f,'sha256').digest()
            if x!=y:assert name in allowed;changed.append(name)
        added=set(final.namelist())-set(base.namelist());assert all(is_old_signature(n) or n in replacements for n in added)
        for name in official.namelist():
            if name.startswith('lib/'):
                with final.open(name) as f:x=hashlib.file_digest(f,'sha256').digest()
                with official.open(name) as f:y=hashlib.file_digest(f,'sha256').digest()
                assert x==y
        protection=verify_metadata(official.read(META),final.read(META))
        assert final.read(META)==base.read(META)
    record=dict(status='Local ENAI candidate; not installed or published; device testing pending',apk=str(a.output),sha256=sha(a.output),bytes=a.output.stat().st_size,package=PACKAGE,version_code=VERSION,version_name=NAME,certificate_sha256=CERT,previous_enai_sha256=PREVIOUS,base_en_sha256=BASE,upgrade_identity_matches_previous=True,unity_identity=identity,dex_identity=dict(classes_compared=len(old_files),only_application_id_semantic_change=True),changed_entries=changed,added_entries=sorted(added),original_game_native_libraries_unchanged=True,metadata_and_music_unchanged_from_base_en=True,protected_metadata=protection,ort_version='1.24.3',ort_aar_sha256=ORT,generated_wrapper_sha256=sha(wrapper),model_manifest=model_manifest,offline_plant_count=len(set(x['plantType'] for x in catalog)),zombie_catalog=False,all_catalog_enum_identities_match_41=True,device_tested=False,runtime_source_sha256={str(p.relative_to(r)):sha(p) for p in sorted((r/'runtime').rglob('*')) if p.is_file() and p.suffix in ('.cpp','.h','.inc','.java')})
    write(w/'build.json',record);print('Verified local ENAI APK: '+str(a.output),flush=True)

if __name__=='__main__':main()
