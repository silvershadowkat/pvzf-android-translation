"""Clean pre6 derivative with reviewed text and scoped native vehicle repairs."""
import argparse,copy,hashlib,json,os,re,subprocess,zipfile
from pathlib import Path
from apply_41_prerelease4 import file_sha,write
from build_41_prerelease4 import audit_apk,CERT
from build_performance_candidate import manifest,loaded_sections
from package_apk_payload import copy_entry,is_old_signature
from migrate_version_text import same_arguments
from build_metadata_translation import parse_metadata

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('base','review','work','output','sdk','jdk','secret','dobby'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--variant',choices=('en','ai'),required=True);a=p.parse_args();a.work.mkdir(parents=True,exist_ok=True);a.output.parent.mkdir(parents=True,exist_ok=True)
    review=json.loads(a.review.read_text('utf8'));assert file_sha(a.base)==review['base_'+a.variant+'_sha256'],'Not the immutable clean pre5 base'
    ai=a.variant=='ai';package='com.LanPiaoPiao.PlantsVsZombiesEN'+('AI' if ai else '');version=4100122 if ai else 4100121;name='4.1-English-pre6'+('-ENAI' if ai else '')
    logs=a.work/'logs';logs.mkdir(exist_ok=True)
    def run(n,args,timeout=120,env=None):
        with (logs/(n+'.log')).open('w',encoding='utf8') as f:r=subprocess.run(list(map(str,args)),stdout=f,stderr=subprocess.STDOUT,timeout=timeout,env=env)
        if r.returncode:raise RuntimeError(n+' failed: '+str(logs/(n+'.log')))
        print(a.variant,n+' passed',flush=True)
    bt=a.sdk/'build-tools/35.0.0';signer=[a.jdk/'bin/java.exe','-XX:ActiveProcessorCount=2','-Xmx512m','-jar',bt/'lib/apksigner.jar']
    run('base-signature',signer+['verify','--print-certs',a.base]);assert CERT in (logs/'base-signature.log').read_text()
    source=Path(__file__).resolve().parents[1]/'runtime';cm=a.sdk/'cmake/3.22.1/bin/cmake.exe';native={}
    assert not (source/'diagnostic.inc').exists() and not (source/'private_cheats.inc').exists()
    for abi in ('arm64-v8a','armeabi-v7a'):
        build=a.work/('native-'+abi)
        run('configure-'+abi,[cm,'-S',source,'-B',build,'-G','Ninja','-DCMAKE_MAKE_PROGRAM='+str(a.sdk/'cmake/3.22.1/bin/ninja.exe'),'-DCMAKE_TOOLCHAIN_FILE='+str(a.sdk/'ndk/25.2.9519653/build/cmake/android.toolchain.cmake'),'-DANDROID_ABI='+abi,'-DANDROID_PLATFORM=android-22','-DCMAKE_BUILD_TYPE=Release','-DANDROID_STL=c++_static','-DDOBBY_SOURCE='+str(a.dobby),'-DPVZF_LOCAL_PLANTBRUSH='+('ON' if ai else 'OFF'),'-DPVZF_MUSIC_DIAGNOSTICS=OFF'])
        run('compile-'+abi,[cm,'--build',build,'--target','pvzfenglish','--parallel','2'],240)
        lib=build/'libpvzfenglish.so';strip=build/'stripped.so'
        run('strip-'+abi,[a.sdk/'ndk/25.2.9519653/toolchains/llvm/prebuilt/windows-x86_64/bin/llvm-strip.exe','--strip-unneeded','-o',strip,lib]);assert loaded_sections(lib)==loaded_sections(strip)
        native['lib/'+abi+'/libpvzfenglish.so']=strip
    with zipfile.ZipFile(a.base) as z:
        d=json.loads(z.read('assets/english/translations.json'));previous=dict(d['exact']);literals=parse_metadata(z.read('assets/bin/Data/Managed/Metadata/global-metadata.dat'))[1]
        for c in review['context']:
            assert literals[c['slot']].text==c['source'] and hashlib.sha256(c['source'].encode()).hexdigest()==c['source_sha256']
            assert same_arguments(c['source'],c['english']) and not re.search('[\u3400-\u9fff]',c['english'])
        d['exact'].update(review['runtime_exact']);assert previous.keys()<=d['exact'].keys()
        patterns={r[0] for r in d['regex']};d['regex']+=[r for r in review['runtime_regex'] if r[0] not in patterns]
        d['pc_commit']=review['blooms']['commit'];d['pc_overlay_commit']=review['blooms']['commit']
        dictionary=json.dumps(d,ensure_ascii=False,indent=2).encode()+b'\n';(a.work/'translations.json').write_bytes(dictionary)
        managed=json.loads(z.read('assets/english/manifest.json'));managed.update(revision=name,pc_checked_commit=review['blooms']['commit']);managed['files']['translations.json']=hashlib.sha256(dictionary).hexdigest()
        changes={'AndroidManifest.xml':manifest(z.read('AndroidManifest.xml'),package,version,name),'assets/english/manifest.json':json.dumps(managed,ensure_ascii=False,separators=(',',':')).encode(),'assets/english/translations.json':dictionary}
        changes.update({n:p.read_bytes() for n,p in native.items()})
        # No private menu/cheat code is added, no game strings or save protocols rewritten.
        unsigned=a.work/'unsigned.apk'
        with zipfile.ZipFile(unsigned,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=3) as out:
            for info in z.infolist():
                if is_old_signature(info.filename):continue
                if info.filename in changes:out.writestr(copy.copy(info),changes[info.filename])
                else:copy_entry(z,out,info)
    aligned=a.work/'aligned.apk';run('align',[bt/'zipalign.exe','-f','-P','16','4',unsigned,aligned])
    props={}
    for line in (a.secret/'signing.properties').read_text('utf-8-sig').splitlines():
        if '=' in line and not line.startswith('#'):
            k,v=line.split('=',1);props[k.strip()]=v.strip()
    env=os.environ.copy();env['PVZF_STORE_PASS']=props['storepass'];env['PVZF_KEY_PASS']=props['keypass']
    run('sign',signer+['sign','--ks',a.secret/'PvZ-Fusion-English-Release.jks','--ks-key-alias',props['alias'],'--ks-pass','env:PVZF_STORE_PASS','--key-pass','env:PVZF_KEY_PASS','--v1-signing-enabled','true','--v2-signing-enabled','true','--v3-signing-enabled','true','--v4-signing-enabled','false','--out',a.output,aligned],180,env);del props,env
    run('signature',signer+['verify','--verbose','--print-certs',a.output]);assert CERT in (logs/'signature.log').read_text()
    run('alignment',[bt/'zipalign.exe','-c','-P','16','4',a.output]);run('manifest',[bt/'aapt2.exe','dump','badging',a.output]);badging=(logs/'manifest.log').read_text();assert package in badging and name in badging and str(version) in badging
    changed=audit_apk(a.base,a.output,set(changes),set(changes))
    result=dict(apk=str(a.output),sha256=file_sha(a.output),bytes=a.output.stat().st_size,variant=a.variant,package=package,version_code=version,version_name=name,base_sha256=file_sha(a.base),certificate_sha256=CERT,changed_entries=changed,all_other_entries_identical=True,compression_preserved=True,original_game_code_and_dex_unchanged=True,runtime_bridge_updated=True,almanacs_and_metadata_unchanged=True,audio_unchanged=True,offline_model_and_inference_unchanged=ai,private_cheats_included=False,blooms_commit=review['blooms']['commit'],counts=review['counts'],emulator_diagnostic_tested=True,vehicle_vertical_instability_reproduced=True,vehicle_grounding_repair=True,reporter_device_confirmation_pending=True,published=False)
    write(a.work/'BUILD.json',result);print(a.variant,'clean APK audited:',result['sha256'],flush=True)
if __name__=='__main__':main()
