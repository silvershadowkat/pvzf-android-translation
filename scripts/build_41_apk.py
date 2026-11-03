"""Build one local 4.1 EN prerelease from the pinned official Android APK.

No recognizer service/model, Android music player or publishing steps. Original
native libraries are retained byte-for-byte; the allowed shell/payload changes
are verified after signing. Signing credentials stay in environment variables.
"""
import argparse, copy, hashlib, json, os, shutil, subprocess, zipfile
from pathlib import Path
from runtime_apk import manifest, resources, dex_application_id
from package_apk_payload import copy_entry, is_old_signature
from protected_metadata import verify_metadata
from build_performance_candidate import loaded_sections

OFFICIAL = '6272551fd2573bd3e342acf1a214aa0ee6d44833260babe600e27301ef9a6390'
CERT = '1f2552cc7dbfbbbee21d2ea7e77edf371a377902cdcb78ba4f3104e387cd7bc6'
META = 'assets/bin/Data/Managed/Metadata/global-metadata.dat'
BUNDLE = 'assets/bin/Data/data.unity3d'
RESOURCE = 'assets/bin/Data/resources.resource'
VERSION_CODE = 4100103
VERSION_NAME = '4.1-English-pre1-r4'
PACKAGE = 'com.LanPiaoPiao.PlantsVsZombiesEN'


def sha(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ('official', 'bundle', 'resource', 'payload', 'work', 'output', 'sdk', 'jdk', 'dobby', 'secret'):
        ap.add_argument('--'+name, type=Path, required=True)
    ap.add_argument('--music-diagnostics',action='store_true',help='Local seek-timing measurement only')
    a = ap.parse_args()
    r = Path(__file__).resolve().parents[1]
    a.work.mkdir(parents=True, exist_ok=True)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    logs = a.work/'logs'
    logs.mkdir(exist_ok=True)
    assert sha(a.official) == OFFICIAL, 'Unreviewed official 4.1 APK'
    report = json.loads((a.payload/'translation-report.json').read_text(encoding='utf8'))
    assert report['previous_keys_retained']
    identity = json.loads((a.bundle.parent/'identity-report.json').read_text(encoding='utf8'))
    music = json.loads((a.bundle.parent/'music-profile-build.json').read_text(encoding='utf8'))
    assert identity['only_player_settings_changed'] and identity['sha256'] == sha(a.bundle)
    assert music['all_original_audio_objects_and_payloads_unchanged'] and music['resource_sha256'] == sha(a.resource)
    assert music.get('load_type')=='DecompressOnLoad', 'Use stock-style decompressed music playback'
    with zipfile.ZipFile(a.official) as z:
        protection = verify_metadata(z.read(META), (a.payload/'metadata.dat').read_bytes())

    def run(name, args, timeout=120, env=None):
        with (logs/(name+'.log')).open('w', encoding='utf8') as log:
            p = subprocess.run(list(map(str, args)), stdout=log, stderr=subprocess.STDOUT, timeout=timeout, env=env)
        if p.returncode:
            raise RuntimeError(name+' failed; inspect '+str(logs/(name+'.log')))
        print(name+' passed', flush=True)

    android = a.sdk/'platforms/android-35/android.jar'
    bt = a.sdk/'build-tools/35.0.0'
    folders = []
    for name in ('java', 'dex'):
        path = (a.work/name).resolve()
        assert path.parent == a.work.resolve(), 'Build cleanup escaped work directory'
        if path.exists():
            shutil.rmtree(path)
        path.mkdir()
        folders.append(path)
    classes, dex = folders
    sources = [r/'runtime/java/com/silvershadow/pvzf'/(name+'.java') for name in
               ('EnglishActivity', 'ManagedFiles', 'BoundedTextCache', 'RegexPrefix', 'PlantbrushTranslations')]
    run('javac', [a.jdk/'bin/javac.exe', '-encoding', 'UTF-8', '-source', '8', '-target', '8', '-cp', android,
                  '-d', classes, *sources], 60)
    run('d8', [a.jdk/'bin/java.exe', '-XX:ActiveProcessorCount=2', '-Xmx512m', '-cp', bt/'lib/d8.jar',
               'com.android.tools.r8.D8', '--release', '--min-api', '22', '--lib', android, '--output', dex,
               *sorted(classes.rglob('*.class'))], 90)
    assert not (dex/'classes2.dex').exists()
    cm = a.sdk/'cmake/3.22.1/bin/cmake.exe'
    native = {}
    for abi in ('arm64-v8a', 'armeabi-v7a'):
        build = a.work/('native-'+abi)
        run('configure-'+abi, [cm, '-S', r/'runtime', '-B', build, '-G', 'Ninja',
                              '-DCMAKE_MAKE_PROGRAM='+str(a.sdk/'cmake/3.22.1/bin/ninja.exe'),
                              '-DCMAKE_TOOLCHAIN_FILE='+str(a.sdk/'ndk/25.2.9519653/build/cmake/android.toolchain.cmake'),
                              '-DANDROID_ABI='+abi, '-DANDROID_PLATFORM=android-22', '-DCMAKE_BUILD_TYPE=Release',
                              '-DANDROID_STL=c++_static', '-DDOBBY_SOURCE='+str(a.dobby),
                              '-DPVZF_MUSIC_DIAGNOSTICS='+('ON' if a.music_diagnostics else 'OFF')], 60)
        run('compile-'+abi, [cm, '--build', build, '--target', 'pvzfenglish', '--parallel', '2'], 240)
        lib, stripped = build/'libpvzfenglish.so', build/'libpvzfenglish-stripped.so'
        strip = a.sdk/'ndk/25.2.9519653/toolchains/llvm/prebuilt/windows-x86_64/bin/llvm-strip.exe'
        run('strip-'+abi, [strip, '--strip-unneeded', '-o', stripped, lib], 30)
        assert loaded_sections(lib) == loaded_sections(stripped)
        native['lib/'+abi+'/libpvzfenglish.so'] = stripped
    support = a.payload/'english'
    support.mkdir(exist_ok=True)
    (support/'NOTICE.txt').write_text('PvZ Fusion English Android runtime\nDobby 21f07a5ce184cda9346afb8009c07fe7e47390d0\nhttps://github.com/jmpews/Dobby\n\n'+(a.dobby/'LICENSE').read_text(encoding='utf8'), encoding='utf8')
    files = {'translations.json': sha(support/'translations.json'), 'NOTICE.txt': sha(support/'NOTICE.txt')}
    almanacs = {name: a.payload/'almanac-refresh'/name for name in ('LawnStrings.json', 'ZombieStrings.json', 'DetailStrings.json')}
    build_manifest = {'revision': VERSION_NAME, 'metadata_sha256': sha(a.payload/'metadata.dat'), 'files': files,
                      'almanac_files': {name: sha(path) for name, path in almanacs.items()},
                      'refresh_test_seed': False, 'pc_commit': report['pc_commit']}
    memory = {'assets/english/manifest.json': json.dumps(build_manifest, ensure_ascii=False, separators=(',', ':')).encode('utf8')}
    replacements = {BUNDLE: a.bundle, RESOURCE: a.resource, META: a.payload/'metadata.dat', 'classes2.dex': dex/'classes.dex',
                    **native, **{'assets/english/'+name: support/name for name in files},
                    **{'assets/english-almanac/'+name: path for name, path in almanacs.items()}}
    unsigned = a.work/'unsigned.apk'
    with zipfile.ZipFile(a.official) as base, zipfile.ZipFile(unsigned, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=3) as out:
        assert 'classes2.dex' not in base.namelist(), 'Review original multidex before adding bootstrap'
        for info in base.infolist():
            if is_old_signature(info.filename):
                continue
            if info.filename == 'AndroidManifest.xml':
                memory[info.filename] = manifest(base.read(info), VERSION_CODE, VERSION_NAME)
            elif info.filename == 'resources.arsc':
                memory[info.filename] = resources(base.read(info))
            elif info.filename == 'classes.dex':
                memory[info.filename] = dex_application_id(base.read(info))
            if info.filename in memory:
                out.writestr(copy.copy(info), memory[info.filename])
            elif info.filename in replacements:
                out.write(replacements[info.filename], info.filename, compress_type=info.compress_type)
            else:
                copy_entry(base, out, info)
        for name, path in replacements.items():
            if name not in base.namelist():
                out.write(path, name, compress_type=zipfile.ZIP_STORED if name.startswith('lib/') else zipfile.ZIP_DEFLATED)
        for name, data in memory.items():
            if name not in base.namelist():
                out.writestr(name, data)
    aligned = a.work/'aligned.apk'
    run('align', [bt/'zipalign.exe', '-f', '-P', '16', '4', unsigned, aligned], 120)
    props = {}
    for line in (a.secret/'signing.properties').read_text(encoding='utf-8-sig').splitlines():
        if '=' in line and not line.startswith('#'):
            key, value = line.split('=', 1)
            props[key.strip()] = value.strip()
    environment = os.environ.copy()
    environment['PVZF_BUILD_STORE_PASS'] = props['storepass']
    environment['PVZF_BUILD_KEY_PASS'] = props['keypass']
    signer = [a.jdk/'bin/java.exe', '-jar', bt/'lib/apksigner.jar']
    run('sign', signer+['sign', '--ks', a.secret/'PvZ-Fusion-English-Release.jks', '--ks-key-alias', props['alias'],
                       '--ks-pass', 'env:PVZF_BUILD_STORE_PASS', '--key-pass', 'env:PVZF_BUILD_KEY_PASS',
                       '--v1-signing-enabled', 'true', '--v2-signing-enabled', 'true', '--v3-signing-enabled', 'true',
                       '--v4-signing-enabled', 'false', '--out', a.output, aligned], 120, environment)
    environment.pop('PVZF_BUILD_STORE_PASS')
    environment.pop('PVZF_BUILD_KEY_PASS')
    run('signature', signer+['verify', '--verbose', '--print-certs', a.output], 60)
    assert CERT in (logs/'signature.log').read_text(encoding='utf8')
    run('alignment', [bt/'zipalign.exe', '-c', '-P', '16', '4', a.output], 60)
    run('manifest', [bt/'aapt2.exe', 'dump', 'badging', a.output], 30)
    text = (logs/'manifest.log').read_text(encoding='utf8')
    assert "name='"+PACKAGE+"'" in text and "versionCode='"+str(VERSION_CODE)+"'" in text and VERSION_NAME in text
    changed, added = [], []
    with zipfile.ZipFile(a.official) as base, zipfile.ZipFile(a.output) as final:
        assert final.testzip() is None
        assert len(final.namelist()) == len(set(final.namelist()))
        for name in base.namelist():
            if is_old_signature(name):
                continue
            data = final.read(name)
            original = base.read(name)
            if data != original:
                changed.append(name)
            if name.startswith('lib/'):
                assert data == original, 'Original native library changed: '+name
        added = sorted(set(final.namelist())-set(base.namelist()))
        added = [n for n in added if not is_old_signature(n)]
        assert set(changed) == {BUNDLE, RESOURCE, META, 'AndroidManifest.xml', 'resources.arsc', 'classes.dex'}
        assert set(added) == (set(replacements) | set(memory))-set(base.namelist())
        assert not any('onnx' in n.lower() or '/plantbrush/' in n.lower() or 'model.onnx' in n for n in final.namelist())
        assert json.loads(final.read('assets/english/manifest.json')) == build_manifest
    record = {'status': 'Local test build; not uploaded or published', 'apk': str(a.output), 'sha256': sha(a.output),
              'bytes': a.output.stat().st_size, 'package': PACKAGE, 'version_code': VERSION_CODE, 'version_name': VERSION_NAME,
              'certificate_sha256': CERT, 'official_sha256': OFFICIAL, 'pc_commit': report['pc_commit'],
              'changed_existing_entries': sorted(changed), 'added_entries': added, 'protected_metadata': protection,
              'all_original_native_libraries_unchanged': True, 'local_ai_included': False,
              'music': 'Native Unity DecompressOnLoad profiles; inactive decoded data unloaded; restart required',
              'bundle_review': identity,
              'device_tested': False, 'managed_refresh': build_manifest,
              'music_diagnostics': a.music_diagnostics,
              'runtime_source_sha256': {str(p.relative_to(r)): sha(p) for p in sorted((r/'runtime').rglob('*')) if p.is_file() and p.suffix in ('.cpp', '.h', '.inc', '.java')}}
    (a.work/'build.json').write_text(json.dumps(record, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
    print('Verified local APK: '+str(a.output), flush=True)


if __name__ == '__main__':
    main()
