"""Package verified shared text payloads over the matching public pre8 edition."""
import argparse, copy, hashlib, json, os, subprocess, zipfile
from pathlib import Path
from apply_41_prerelease4 import BUNDLE, META, file_sha, write
from build_41_prerelease4 import audit_apk, CERT
from build_performance_candidate import manifest
from package_apk_payload import copy_entry, is_old_signature


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for n in ('base', 'review', 'payload', 'work', 'output', 'sdk', 'jdk', 'secret'):
        p.add_argument('--' + n, type=Path, required=True)
    p.add_argument('--variant', choices=('en', 'ai'), required=True)
    a = p.parse_args(); a.work.mkdir(parents=True, exist_ok=True); a.output.parent.mkdir(parents=True, exist_ok=True)
    review = json.loads(a.review.read_text('utf8')); report = json.loads((a.payload / 'translation-report.json').read_text('utf8'))
    assert file_sha(a.base) == review['base_' + a.variant + '_sha256']
    assert report['base_sha256'] == review['base_' + a.variant + '_sha256'] and report['variant'] == a.variant
    assert report['counts'] == review['counts'] and report['blooms_commit'] == review['blooms']['commit']
    assert file_sha(a.payload / 'data.unity3d') == report['bundle_sha256']
    assert file_sha(a.payload / 'metadata.dat') == report['metadata_sha256']
    ai = a.variant == 'ai'; package = 'com.LanPiaoPiao.PlantsVsZombiesEN' + ('AI' if ai else '')
    version = 4100128 if ai else 4100127; name = '4.1-English-pre9' + ('-ENAI' if ai else '')
    logs = a.work / 'logs'; logs.mkdir(exist_ok=True)
    def run(n, args, timeout=180, env=None):
        with (logs / (n + '.log')).open('w', encoding='utf8') as f:
            r = subprocess.run(list(map(str, args)), stdout=f, stderr=subprocess.STDOUT, timeout=timeout, env=env)
        if r.returncode: raise RuntimeError(n + ' failed: ' + str(logs / (n + '.log')))
        print(a.variant, n + ' passed', flush=True)
    bt = a.sdk / 'build-tools/35.0.0'
    signer = [a.jdk / 'bin/java.exe', '-XX:ActiveProcessorCount=2', '-Xmx512m', '-jar', bt / 'lib/apksigner.jar']
    run('base-signature', signer + ['verify', '--print-certs', a.base]); assert CERT in (logs / 'base-signature.log').read_text()
    replacements = {BUNDLE: a.payload / 'data.unity3d', META: a.payload / 'metadata.dat',
                    'assets/english/translations.json': a.payload / 'translations.json'}
    for n in ('LawnStrings', 'ZombieStrings', 'DetailStrings'): replacements['assets/english-almanac/' + n + '.json'] = a.payload / (n + '.json')
    with zipfile.ZipFile(a.base) as z:
        # Each edition retains its own bundle differences outside approved text.
        managed = json.loads(z.read('assets/english/manifest.json'))
        managed.update(revision=name, pc_checked_commit=review['blooms']['commit'], metadata_sha256=file_sha(replacements[META]))
        managed['files']['translations.json'] = file_sha(replacements['assets/english/translations.json'])
        for n in ('LawnStrings', 'ZombieStrings', 'DetailStrings'): managed['almanac_files'][n + '.json'] = file_sha(a.payload / (n + '.json'))
        memory = {'AndroidManifest.xml': manifest(z.read('AndroidManifest.xml'), package, version, name),
                  'assets/english/manifest.json': json.dumps(managed, ensure_ascii=False, separators=(',', ':')).encode()}
        unsigned = a.work / 'unsigned.apk'
        with zipfile.ZipFile(unsigned, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=3) as out:
            for info in z.infolist():
                n = info.filename
                if is_old_signature(n): continue
                if n in memory: out.writestr(copy.copy(info), memory[n])
                elif n in replacements: out.write(replacements[n], n, compress_type=info.compress_type)
                else: copy_entry(z, out, info)
    aligned = a.work / 'aligned.apk'; run('align', [bt / 'zipalign.exe', '-f', '-P', '16', '4', unsigned, aligned])
    props = {}
    for line in (a.secret / 'signing.properties').read_text('utf-8-sig').splitlines():
        if '=' in line and not line.startswith('#'):
            k, v = line.split('=', 1); props[k.strip()] = v.strip()
    env = os.environ.copy(); env['PVZF_STORE_PASS'] = props['storepass']; env['PVZF_KEY_PASS'] = props['keypass']
    run('sign', signer + ['sign', '--ks', a.secret / 'PvZ-Fusion-English-Release.jks', '--ks-key-alias', props['alias'], '--ks-pass', 'env:PVZF_STORE_PASS', '--key-pass', 'env:PVZF_KEY_PASS', '--v1-signing-enabled', 'true', '--v2-signing-enabled', 'true', '--v3-signing-enabled', 'true', '--v4-signing-enabled', 'false', '--out', a.output, aligned], env=env)
    del props, env
    run('signature', signer + ['verify', '--verbose', '--print-certs', a.output]); assert CERT in (logs / 'signature.log').read_text()
    run('alignment', [bt / 'zipalign.exe', '-c', '-P', '16', '4', a.output])
    run('manifest', [bt / 'aapt2.exe', 'dump', 'badging', a.output]); badging = (logs / 'manifest.log').read_text()
    assert "name='" + package + "'" in badging and "versionCode='" + str(version) + "'" in badging and name in badging
    allowed = set(replacements) | set(memory)
    required = set(memory) | {BUNDLE, 'assets/english/translations.json', 'assets/english-almanac/DetailStrings.json'}
    changed = audit_apk(a.base, a.output, allowed, required)
    assert set(changed) == required, 'Unexpected payload edit'
    write(a.work / 'BUILD.json', dict(apk=str(a.output), sha256=file_sha(a.output), bytes=a.output.stat().st_size,
          package=package, version_code=version, version_name=name, variant=a.variant, certificate_sha256=CERT,
          base_sha256=file_sha(a.base), changed_entries=changed, all_other_entries_identical=True, compression_preserved=True,
          game_native_libraries_and_dex_unchanged=True, runtime_bridge_unchanged=True, audio_unchanged=True,
          offline_model_and_inference_unchanged=ai, protected_metadata=report['protected_metadata'],
          counts=review['counts'], blooms_commit=review['blooms']['commit'], published=False))
    print(a.variant, 'signed APK audited:', file_sha(a.output), flush=True)


if __name__ == '__main__': main()
